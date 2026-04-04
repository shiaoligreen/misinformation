"""
Neural Baseline
CNN: TextCNN Opinion Classifier
=========================================
Architecture: Kim (2014) "Convolutional Neural Networks for Sentence Classification"
  Embedding = Conv1d (filter sizes 3,4,5) 

In addition to using the Kim (2014) paper, Gemini and Claude were used extensively in the implementation of the following code
While specific instances of LLM use are commented when possible, Gemini and Claude were also used for overall understanding,
architecture and planning. The comments are my own.

Embeddings are FROZEN pretrained FastText vectors. With only 600 training
examples, fine-tuning is likely to do more harm than good

FastText .vec file:
  Downloaded cc.en.300.vec from https://fasttext.cc/docs/en/crawl-vectors.html
  (Common Crawl, 300d — handles web text and tweets that are prone to typos, elongated words, emojis, etc)
  Set FASTTEXT_PATH in config.py.

Usage:
    python cnn_baseline.py

Usage (from notebook):
    import cnn_baseline as cnn
    vocab        = cnn.build_vocab(train_rows, preprocess_fn)
    embed_matrix = cnn.load_fasttext_vectors(path, vocab)
    loader       = cnn.make_loader(rows, vocab, shuffle=True)
    model        = cnn.TextCNN(len(vocab), embed_matrix).to(device)
    model        = cnn.train_model(model, train_loader, dev_loader, train_rows, device)
    preds, labels, probs = cnn.predict(model, loader, device)
"""

import csv
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Dataset

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import CONFIG, DATA_DIR, FASTTEXT_PATH, SEED  # noqa: E402
from preprocess import preprocess  # noqa: E402

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


# Data

def load_csv(path: Path):
    """
    Parameter: path of csv file
    Returns: list of dictionary

    Loads data from csv files and returns a list of dictionaries
    Each row becomes a dictionary within the list like this: {"id": "0", "text": "No Food, No FEMA...", "opinion_label": "0", ...}
    encoding is specified to be utf-8 in order to handle special characters, like emojis often used in tweets
    """
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


class Vocabulary:
    """
    Implemented as a class because lookup in two directions is needed (token2idx and idx2token)
    """

    #Two special tokens for NLP vocab: <PAD> and <OOV>

    #PAD is used to fill shorter sequences so that all sequences in a batch are the same length
    PAD = "<PAD>"

    #Handle words seen at inference time that weren't seen in training data.
    OOV = "<OOV>"

    def __init__(self):
        #Build two dictionaries to be able to lookup an index by using a token, as well as a token by using an index
        self.token2idx = {self.PAD: 0, self.OOV: 1}
        self.idx2token = [self.PAD, self.OOV]

    def build(self, tokenized_docs: list[list[str]]):
        """
            Parameter: list of documents, where each document is already a list of tokens
            Example: 
            [
                ["no", "food", "URL", "hurricane"],
                ["would-be", "looter", "MENTION", "said"]
            ]

        Builds the token2idx and the idx2token dictionaries
        """
        #Iterate through every token in every document.
        for doc in tokenized_docs:
            for tok in doc:
                #if the token has not been seen before, add it
                #Index is current length of list. Tokens numbered in order that they are seen.
                if tok not in self.token2idx:
                    self.token2idx[tok] = len(self.idx2token)
                    self.idx2token.append(tok)


    def encode(self, tokens: list[str]):
        """
        Convert a list of string tokens to a list of integers. 
        Takes a single document's token list and returns an integer list.

        """
        oov = self.token2idx[self.OOV]
        return [self.token2idx.get(t, oov) for t in tokens]

    def __len__(self):
        """
        Helper function to implement len() for the Vocabulary class
        """
        return len(self.idx2token)


def build_vocab(rows: list[dict], tokenize_fn=preprocess):
    """
    Wrapper function to build vocabulary from training rows only.
    Takes raw CSV rows and handles instantiation of Vocabulary object
    Uses the tokenize function to tokenize raw rows and then calls
    build to create vocab's dictionaries 
    
    Parameters: rows are a list of dictionaries, tokenize_fn is an optional param
    so that the tokenizer can be changed

    returns: instantiated Vocabulary object.
    """
    vocab = Vocabulary()
    #Help from Claude on list comprehension
    vocab.build([tokenize_fn(r["text"])[:CONFIG["max_len"]] for r in rows])
    return vocab


def load_fasttext_vectors(path: Path, vocab: Vocabulary, embed_dim: int = CONFIG["embed_dim"],):
    """
    Load pretrained FastText vectors for the vocabulary.
    Parameters: 
        path = path to .vec file
        vocab = Vocabulary object
        embed_dim = embed_dim that is specified in CONFIG file

    Does the following:
        Reads the .vec text format (word followed by floats, one per line).
        OOV words (in vocab but not in .vec) are initialized from
       
        PAD stays all-zeros.

    Returns a  matrix that is vocab_size x embed_dim in size and is a  float torch tensor, 
        which maps ever vocab index to an embed_dim sized vector
    """
    print(f"Loading FastText vectors from {path} …")
    ft = {}

    #Open .vec file with pretrained vectors
    with open(path, encoding="utf-8") as f:
        #get first line
        first = f.readline().split()
        # skip header line if it's "vocab_size embed_dim"
        if len(first) == 2 and first[0].isdigit():
            pass

        #it is not a header, process it
        else:
            #unpack the first element as the word and everything else as the vector values
            word, *vals = first
            ft[word] = np.array(vals, dtype=np.float32)

        #Iterate over each line in the .vec file    
        for line in f:
            #split newline from the line. Then split on spaces, too.
            parts = line.rstrip().split(" ")

            #Split the list into two, the first part is the word, second part is list of number strings
            word, vals = parts[0], parts[1:]
            
            #Make sure the line actually has embed_dim values. If it doesn't , we need to skip this vector because something is wrong with it.
            if len(vals) == embed_dim:
                #convert the list of number strings to a np array of floats and store in dictionary w/word as key
                ft[word] = np.array(vals, dtype=np.float32)

    #Computes standard deviation across all loaded vectors. This will be used to initialize OOV words (words not found in FastText)
    pretrained = np.array(list(ft.values()))
    oov_std = pretrained.std()

    #Build the final matrix row by row.
    #Initialize matrix of correct size to contain all zeros
    matrix = np.zeros((len(vocab), embed_dim), dtype=np.float32)
    
    #initialize count of number tokens found
    n_found = 0

    #Interate through token, idex in the dictionary
    for tok, idx in vocab.token2idx.items():
        
        if tok in ft:
            #token is found in FastText, copy the pretrained vector into the row
            matrix[idx] = ft[tok]
            #Increment n_found
            n_found += 1
        elif tok not in (Vocabulary.PAD, Vocabulary.OOV):
            #token is not in FastText and not in PAD or OOV. We need to add it as random noise.
            #We add it as random noise because we reserve zeros to be padding and OOV
            matrix[idx] = np.random.normal(0, oov_std, embed_dim)

    print(f"  {n_found}/{len(vocab)} vocab tokens found in FastText vectors "
          f"({100 * n_found / len(vocab):.1f}%)")
    return torch.tensor(matrix)


class OpinionDataset(Dataset):
    """
    Container class that inherits from PyTorch's Dataset class.
    
    """
    
    #Had help from Claude for  how to do this correctly.
    
    def __init__(self, rows: list[dict], vocab: Vocabulary, tokenize_fn=preprocess):
        """
        Parameters: 
            rows: list of dictionaries that are raw rows
            vocab: vocabulary object
            tokenize_fn : tokenizer function of choice, or use default

        Preprocesses everything: tokenizes, encodes to integers, converts labels to tensors and
        stores them as (ids, label) pairs in self.samples. Should be done in advance of training.
        """
        self.samples = []
        for row in rows:
            #tokenize 
            tokens = tokenize_fn(row["text"])[:CONFIG["max_len"]]
            #get integers
            ids    = torch.tensor(vocab.encode(tokens), dtype=torch.long)
            #convert to labels to tensors
            label  = torch.tensor(int(row["opinion_label"]), dtype=torch.float)
            self.samples.append((ids, label))

    #Required implementation for Dataset class
    def __len__(self):
        return len(self.samples)

    #Required implementation for Dataset class
    def __getitem__(self, idx):
        return self.samples[idx]


def _collate(batch):
    """
    DataLoader calls this function to assemble individual examples into a batch.
    Parameter: 
        batch = list of (ids, label) tuples
    
    Returns: Tuple of two sensors: token id sequences padded, labels for each example in batch     
    """
    #uppacks list of tuples into two separate tuples: all of the ids together, all of the labels together
    seqs, labels = zip(*batch)

    #takes sequences of different lengths and pads the shorter ones with zeros, so they are all the same length as the 
    #longest in the batch.
    #batch_first=True param means that output shape is (batch_size, seq_length)
    padded = pad_sequence(seqs, batch_first=True, padding_value=0)
    
    #Convert the tuple of individual label tensors into a single tensor
    #Return a tuple of two tensors: padded (token id sequences all padded to same length) and tnsor of labels for each example in batch
    return padded, torch.stack(labels)


def make_loader( rows: list[dict], vocab: Vocabulary, shuffle: bool = False, tokenize_fn=preprocess,):
    """
    Wrapper function that creates dataset 
    Parameters:
        raw rows (list of dictionaries)
        vocab: Vocabulary object
        shuffle: True for training, so that model doesn't see examples in the same order for every epoch
                False for dev/test
        tokenize_fn: tokenizer function
    Returns: DataLoader object with dataset already created
    
    """
    ds = OpinionDataset(rows, vocab, tokenize_fn)
    return DataLoader(ds, batch_size=CONFIG["batch_size"],
                      shuffle=shuffle, collate_fn=_collate)


# TextCNN Model

class TextCNN(nn.Module):
    """
    
    Class to implement the TextCNN model itself
    Inherits from nn.Module, PyTorch's base class.

    From Kim (2014) TextCNN. 
    Reads parameters from config file, but Kim's setting are the following:

    Embedding (frozen pretrained) 
    parallel Convoluted Neural Network with filter sizes [3,4,5]
    global max-pool per filter → concat → 
    Dropout(0.5) → Linear(1)
    """

    def __init__(self, vocab_size: int, embed_matrix: torch.Tensor):
        #call the nn.Module superclass init
        super().__init__()

        #get embedding dimension and number of filters from config file
        embed_dim   = CONFIG["embed_dim"]
        num_filters = CONFIG["num_filters"]

        #create embedding layer and load the FastText matrix into it
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)

        #requires_grad= False freezes embeddings. Pytorch won't compute gradients for weights, so they 
        #will not be updated during training
        self.embedding.weight = nn.Parameter(embed_matrix, requires_grad=False)

        #Three parallel convolutional filters size 3, 4, 5 (as in Kim paper). Each filter slides over
        #the token sequence looking for patterns of that number of consecutive tokens.
        #ModuleList is a a PyTorch aware python list, so registers these as params of model
        self.convs = nn.ModuleList([
            nn.Conv1d(embed_dim, num_filters, fs)
            for fs in CONFIG["filter_sizes"]
        ])

        #Dropout at 0.5 (as in Kim paper).
        #Means that there is a 50% chance of being randomly zeroed out. Roughtly half of the vector can get dropped
        #to zero at any given pass for regularlization. So model doesn't rely too heavily on any single feature.
        #applied on every single forward pass during training
        #It will be turned off during evaluation/inference time.
        self.drop       = nn.Dropout(CONFIG["dropout"])

        #Learning a weighted combination of features to produce one score.
        #Score will be passed through sigmoid later. 
        self.classifier = nn.Linear(num_filters * len(CONFIG["filter_sizes"]), 1)

    def forward(self, x: torch.Tensor):
        """
        Parameter: x is the padded batch of token IDs after _collate. Size is batch x sequence length
        Returns: Returns a 1D tensor of shape (B,) containing one raw logit per example in the batch. 
        Logits are unbounded real numbers — positive values indicate opinion, negative indicate not-opinion.
        Should pass through sigmoid to convert to probabilities.
        """
        # x: (B, T)
        #Looks up FastText vector for each token ID, giving shape (batch, sequence, embedding dimension)
        emb = self.embedding(x).permute(0, 2, 1)   # (B, E, T)

        #For each of 3 convolutions, conv(emb) slides the filter across the sequence,
        #produces (B, num_filters, T-fs+1)
        pooled = [
            #zeos out any negative activations
            torch.relu(conv(emb)).max(dim=2).values  # (B, num_filters)
            for conv in self.convs
        ]

        #concatenate the three tensors along dimension 1....go from size (B, 100) to (B, 300)
        cat = torch.cat(pooled, dim=1)               # (B, num_filters * 3)

        #Apply the dropout and squeeze results in one logit per example in the batch
        return self.classifier(self.drop(cat)).squeeze(1)


# Training & inference

def train_model( model: nn.Module, train_loader: DataLoader, dev_loader: DataLoader, train_rows: list[dict], device: torch.device,):
    """
    Parameters: 
        model: nn.Module 
        train_loader: training DataLoader
        dev_loader: development DataLoader
        train_rows: list[dict] containing raw training rows
        device: torch.device

    Train with BCEWithLogitsLoss (pos_weight for class imbalance)
    and early stopping on dev macro-F1 (patience=CONFIG['patience']).

    Returns the model loaded with the best checkpoint.
    """
    from metrics import compute_metrics
    #count how many 0s and 1s are in the training set
    label_counts = Counter(int(r["opinion_label"]) for r in train_rows)
    #pos_weight is ratio which tells loss function to penalize missing an opinion example more/less
    #than missing non-opinion. This is done to compensate for class imbalance of opinion/non-opinion
    pos_weight   = torch.tensor(
        [label_counts[0] / label_counts[1]], device=device
    )
    #Apply combined sigmoid and binary cross-entropy function, so less likely to underflow to zero
    #which would cause gradient to go to nan and break training.
    #Does math with raw logit directly
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    #Adam optimizer, only updaing parameters where requires_grad = True
    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=CONFIG["lr"],
    )

    #Three variables for stopping early. best_f1 tracks teh best dev score seen so far
    #best_state is a copy of the model weights at that point
    #no_improve counts consecutive epochs without improvement
    best_f1, best_state, no_improve = 0.0, None, 0


   
    for epoch in range(1, CONFIG["max_epochs"] + 1):
        #turns dropout on
        model.train()
        
        total_loss = 0.0

        #inner training loop
        for x, y in train_loader:
            #for each batch, move to device
            x, y = x.to(device), y.to(device)

            #zero gradients from previous step
            optimizer.zero_grad()
            
            #compute the loss
            loss = criterion(model(x), y)

            #backpropagate
            loss.backward()

            #clip graidents to prevent exploding gradients
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)

            #update weights
            optimizer.step()

            #add loss to the tally
            total_loss += loss.item()

        #after each full epoch over training data, evaluate on the dev data set
        preds, labels, probs = predict(model, dev_loader, device)

        #compute the metrics
        dev_f1 = compute_metrics(preds, labels, probs)["macro_f1"]


        print(f"Epoch {epoch:3d} | loss={total_loss/len(train_loader):.4f} "
              f"| dev_macro_f1={dev_f1:.4f}")

        #if dev F1 improved, save a copy of the weights and reset counter. If not, increment the counter
        #once no_improve = patience, it is time to stop early.
        if dev_f1 > best_f1:
            best_f1    = dev_f1
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= CONFIG["patience"]:
                print(f"  Early stopping (no improvement for "
                      f"{CONFIG['patience']} epochs). Best F1: {best_f1:.4f}")
                break
    
    #restore weights from the best epoch and return the model.
    model.load_state_dict(best_state)
    return model


def predict(model: nn.Module, loader: DataLoader, device: torch.device,):
    """
    Parameters:
        model: 
        loader
        device
    Returns:
        a tuple of three lists: (predictions, true labels, probabilities)
        tuple[list[int], list[int], list[float]]
    """

    #turn off dropout
    model.eval()

    #create 3 empty lists to start
    all_preds, all_labels, all_probs = [], [], []

    #do not need gradients at inference time
    with torch.no_grad():

        for x, y in loader:
            x = x.to(device)

            #sgimoid function to get probabilities. model(x) produces raw logits, sigmoid converts them
            #to proabilities between 0. and 1. .cpu() moves the tensor back from GPU to CUP
            #.tolist() converts to plain list of floats
            probs = torch.sigmoid(model(x)).cpu().tolist()

            #accumulates results across batches. Threshold of 0.5 converts probabilities to hard predictions
            #above 0.5 is opinion, below is not
            all_probs.extend(probs)
            all_preds.extend([int(p >= 0.5) for p in probs])

            #y.long() converts labels from float (needed for losee function) back to int
            all_labels.extend(y.long().tolist())

     #return all three lists, each of length equal to full dataset to be used for compute_metrics()       
    return all_preds, all_labels, all_probs



# Main function to be used as standalone entry point

def main():
    import nltk
    
    #if NLTK tokenizer data isn't present, download it
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)

    #use best device availabe
    device = torch.device(
        "mps"  if torch.backends.mps.is_available()  else
        "cuda" if torch.cuda.is_available()           else
        "cpu"
    )
    print(f"Device: {device}\n")

    #Load train and dev rows data only
    train_rows = load_csv(DATA_DIR / "mis_df_train.csv")
    dev_rows   = load_csv(DATA_DIR / "mis_df_dev.csv")

    #Build vocab from training data only
    #load fastText vectors for vocab
    vocab        = build_vocab(train_rows)
    embed_matrix = load_fasttext_vectors(FASTTEXT_PATH, vocab)

    #create train and dev data loaders. Shuffle for training only
    train_loader = make_loader(train_rows, vocab, shuffle=True)
    dev_loader   = make_loader(dev_rows,   vocab, shuffle=False)

    #Create the model and move it to the device.
    model = TextCNN(len(vocab), embed_matrix).to(device)
    print(f"Parameters (trainable): "
          #Trainable params will be smaller than total params because of frozen embeddings
          f"{sum(p.numel() for p in model.parameters() if p.requires_grad):,}\n")

    #train model and return best checkpoint
    model = train_model(model, train_loader, dev_loader, train_rows, device)

    #Import the metrics functions, run predictions and do evaluation
    from metrics import (compute_metrics, print_report,
                         print_confusion_matrix, error_analysis)

    preds, labels, probs = predict(model, dev_loader, device)
    metrics = compute_metrics(preds, labels, probs)

    print()
    print_report(metrics, name="TextCNN — Dev Set")
    print()
    print_confusion_matrix(preds, labels)
    print()
    error_analysis(dev_rows, preds, labels)


if __name__ == "__main__":
    main()
