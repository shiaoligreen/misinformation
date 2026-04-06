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
    metrics = cnn.evaluate_model(model, test_loader, test_rows, device, name="TextCNN — Test Set")
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
from config import CONFIG, DATA_DIR, FASTTEXT_PATH, SEED, TARGETS  # noqa: E402
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
            # store one label tensor per target — keyed by column name
            labels = {t: torch.tensor(int(row[t]), dtype=torch.float) for t in TARGETS}
            self.samples.append((ids, labels))

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
    # unpack list of (ids, labels_dict) tuples
    seqs, label_dicts = zip(*batch)

    # takes sequences of different lengths and pads the shorter ones with zeros, so they are all the same length as the
    # longest in the batch. batch_first=True means output shape is (batch_size, seq_length)
    padded = pad_sequence(seqs, batch_first=True, padding_value=0)

    # stack each target's labels into its own tensor: {target: (B,)}
    labels = {t: torch.stack([d[t] for d in label_dicts]) for t in TARGETS}

    return padded, labels


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
        self.drop = nn.Dropout(CONFIG["dropout"])

        # One linear head per target. The shared CNN backbone feeds into each head independently.
        # ModuleDict registers them as model parameters so PyTorch tracks their gradients.
        self.classifiers = nn.ModuleDict({
            t: nn.Linear(num_filters * len(CONFIG["filter_sizes"]), 1)
            for t in TARGETS
        })

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

        shared = self.drop(cat)
        # each head produces one logit per example — returns {target: (B,)}
        return {t: self.classifiers[t](shared).squeeze(1) for t in TARGETS}


# Training & inference

def train_model( model: nn.Module, train_loader: DataLoader, dev_loader: DataLoader, train_rows: list[dict], device: torch.device, train_targets: list[str] = None):
    """
    Parameters:
        model: nn.Module
        train_loader: training DataLoader
        dev_loader: development DataLoader
        train_rows: list[dict] containing raw training rows
        device: torch.device
        train_targets: which targets to train on. Defaults to all TARGETS (multi-task).
            Pass a single-element list for single-task mode, e.g. ["opinion_label"].
            All targets are treated equally — early stopping uses average F1 across
            all active targets.

    Train with BCEWithLogitsLoss (pos_weight for class imbalance)
    and early stopping on average dev macro-F1 across active targets.

    Returns the model loaded with the best checkpoint.
    """
    from metrics import compute_metrics

    # default to all targets; single-element list enables single-task mode
    active_targets = train_targets if train_targets is not None else TARGETS

    # one criterion per active target, each with its own pos_weight for class imbalance
    criteria = {}
    for t in active_targets:
        counts = Counter(int(r[t]) for r in train_rows)
        pw = torch.tensor([counts[0] / counts[1]], device=device)
        criteria[t] = nn.BCEWithLogitsLoss(pos_weight=pw)

    #Adam optimizer, only updating parameters where requires_grad = True
    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=CONFIG["lr"],
    )

    #Three variables for stopping early. best_f1 tracks the best dev score seen so far
    #best_state is a copy of the model weights at that point
    #no_improve counts consecutive epochs without improvement
    best_f1, best_state, no_improve = 0.0, None, 0

    for epoch in range(1, CONFIG["max_epochs"] + 1):
        #turns dropout on
        model.train()

        total_loss = 0.0

        #inner training loop
        for x, y in train_loader:
            # x: (B, T) — y: {target: (B,)}
            x = x.to(device)
            y = {t: y[t].to(device) for t in active_targets}

            #zero gradients from previous step
            optimizer.zero_grad()

            logits = model(x)  # {target: (B,)}

            # sum losses from active heads only
            loss = sum(criteria[t](logits[t], y[t]) for t in active_targets)

            #backpropagate
            loss.backward()

            #clip gradients to prevent exploding gradients
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)

            #update weights
            optimizer.step()

            #add loss to the tally
            total_loss += loss.item()

        # early stopping uses average macro-F1 across all active targets (all treated equally)
        f1s = [compute_metrics(*predict(model, dev_loader, device, target=t))["macro_f1"]
               for t in active_targets]
        dev_f1 = sum(f1s) / len(f1s)

        f1_str = " | ".join(f"{t}: {f:.4f}" for t, f in zip(active_targets, f1s))
        print(f"Epoch {epoch:3d} | loss={total_loss/len(train_loader):.4f} "
              f"| avg_dev_f1={dev_f1:.4f} ({f1_str})")

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


def predict(model: nn.Module, loader: DataLoader, device: torch.device,
            target: str = TARGETS[0]):
    """
    Parameters:
        model:
        loader
        device
        target: which label column to evaluate (defaults to TARGETS[0])
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

            # model now returns {target: logits}; select the requested head
            logits = model(x)[target]

            #sigmoid converts raw logits to probabilities between 0 and 1
            #.cpu() moves tensor back from GPU, .tolist() converts to plain Python list
            probs = torch.sigmoid(logits).cpu().tolist()

            #accumulates results across batches. Threshold of 0.5 converts probabilities to hard predictions
            all_probs.extend(probs)
            all_preds.extend([int(p >= 0.5) for p in probs])

            #y[target].long() selects the correct label column and converts from float back to int
            all_labels.extend(y[target].long().tolist())

    #return all three lists, each of length equal to full dataset to be used for compute_metrics()
    return all_preds, all_labels, all_probs



def evaluate_model(model: nn.Module, loader: DataLoader, rows: list[dict], device: torch.device,
                   name: str = "TextCNN", target: str = TARGETS[0]):
    """
    Run predict() and print all metrics for a given split.
    Parameters:
        model:  trained TextCNN
        loader: DataLoader for the split to evaluate
        rows:   raw CSV rows for the same split (used for error analysis)
        device: torch.device
        name:   label printed in the report header
        target: which label column to evaluate (defaults to TARGETS[0])
    Returns:
        metrics dict from compute_metrics()
    """
    from metrics import compute_metrics, print_report, print_confusion_matrix, error_analysis

    preds, labels, probs = predict(model, loader, device, target=target)
    metrics = compute_metrics(preds, labels, probs)

    print()
    print_report(metrics, name=name)
    print()
    print_confusion_matrix(preds, labels)
    print()
    error_analysis(rows, preds, labels)

    return metrics


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

    #Load train and dev rows only — test is not touched until final evaluation
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

    for target in TARGETS:
        evaluate_model(model, dev_loader, dev_rows, device,
                       name=f"TextCNN — Dev Set ({target})", target=target)


if __name__ == "__main__":
    main()
