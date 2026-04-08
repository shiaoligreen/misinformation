"""
logreg_transfer.py
──────────────────
Logistic Regression baseline with transfer learning from FastText embeddings for COLX 581 Sprint 2.

logreg_baseline.py used with FastText embeddings functions from cnn_baseline.py and TF-IDF weighting.
Gemini used to help with the two new functions: _get_tfidf_weighted_embeddings, _get_embeddings

Two tasks:
opinion_label        (0 = not-opinion, 1 = opinion)
misinformation_label (0 = factual,     1 = misinformation)

Features
TF-IDF unigrams + bigrams on raw text
Pre-computed linguistic binary features:
    all_caps_bin, exclamation_marks_bin, hedging_bin,
    adjectives_bin, unk_bin, text_length (scaled)

Usage in baseline_notebook.ipynb:
  import logreg_baseline as lr
  results["LogReg-Opinion"]  = lr.run(train_rows, dev_rows, task="opinion_label")
  results["LogReg-Misinfo"]  = lr.run(train_rows, dev_rows, task="misinformation_label")
"""

import csv
from pathlib import Path

import numpy as np
from scipy.sparse import hstack, csr_matrix

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# additional preprocess import
from preprocess import preprocess
from config import CONFIG, FASTTEXT_PATH

# Match the project seed from config.py
try:
    from config import SEED
except ImportError:
    SEED = 581

# Annotated linguistic features
LINGUISTIC_FEATURES = [
    "all_caps_bin",
    "exclamation_marks_bin",
    "hedging_bin",
    "adjectives_bin",
    "unk_bin",
    "text_length",
]

# C values to search over (log scale from lecture notes)
PARAM_GRID = {"C": [0.001, 0.01, 0.1, 1.0]}


# Data loading

def load_csv(path) -> list[dict]:
    """
    Load a CSV into a list of dicts.
    Numeric fields changed to int.
    """
    int_fields = {
        "id", "misinformation_label", "opinion_label",
        "text_length",
        "exclamation_marks_bin", "all_caps_bin",
        "hedging_bin", "adjectives_bin", "unk_bin",
        "jennifer", "nicole", "rachelle", "shiao-li",
    }

    rows = []
    # COLX 521 lecture notes were referenced when writing this
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            for field in int_fields:
                if field in row and row[field] != "":
                    try:
                        row[field] = int(row[field])
                    except ValueError:
                        pass
            rows.append(row)
    return rows


# Feature extraction 

def _extract_texts(rows: list[dict]) -> list[str]:
    """Pull the raw text field from each row."""
    return [r["text"] for r in rows]


def _extract_ling_features(rows: list[dict]) -> np.ndarray:
    """
    Returns a 2D array of the annotated linguistic features for each row.
    """
    matrix = []
    # Claude used to get features in appropriate format & information on what format is best
    for r in rows:
        matrix.append([float(r.get(f, 0) or 0) for f in LINGUISTIC_FEATURES])
    return np.array(matrix, dtype=np.float32)


def _extract_labels(rows: list[dict], task: str) -> list[int]:
    """Extract numeric labels for int values."""
    return [int(r[task]) for r in rows]


# Model building 

# vocab class, function, and fasttext function from cnn_baseline.py
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
    return np.array(matrix, dtype=np.float32)

# relied on Gemini for this helper function
def _get_embeddings(texts: list[str], vocab: Vocabulary, embed_matrix: np.ndarray, tokenize_fn=preprocess) -> np.ndarray:
    """
    Calculates document-level embeddings by tokenizing, getting FastText vectors 
    for each token, and averaging them (mean pooling).
    """
    doc_embeds = []
    embed_dim = embed_matrix.shape[1]
    
    for text in texts:
        # create the tokens and limit to 512
        tokens = tokenize_fn(text)[:CONFIG.get("max_len", 512)]
        
        # change to integer representation
        encoded = vocab.encode(tokens)

        # average the token embeddings
        token_vecs = embed_matrix[encoded]
        doc_embeds.append(np.mean(token_vecs, axis=0))
            
    return np.array(doc_embeds, dtype=np.float32)

# gemini code for this helper function too
def _get_tfidf_weighted_embeddings(
    texts: list[str], 
    vocab: Vocabulary, 
    embed_matrix: np.ndarray, 
    tfidf_vectorizer: TfidfVectorizer,
    tfidf_matrix: csr_matrix,
    tokenize_fn=preprocess
) -> np.ndarray:
    """
    Calculates document-level embeddings by taking a weighted average 
    of token FastText vectors, using their TF-IDF scores as weights.
    """
    doc_embeds = []
    embed_dim = embed_matrix.shape[1]
    
    # Extract the mapping of word -> column index in the TF-IDF matrix
    tfidf_vocab = tfidf_vectorizer.vocabulary_
    
    for i, text in enumerate(texts):
        tokens = tokenize_fn(text)[:CONFIG.get("max_len", 512)]
        encoded = vocab.encode(tokens)

        # Protect against empty documents
        if not encoded:
            doc_embeds.append(np.zeros(embed_dim))
            continue
            
        # Convert this document's row in the sparse matrix to a dense array for fast lookup
        tfidf_row = tfidf_matrix.getrow(i).toarray()[0]
        
        weighted_sum = np.zeros(embed_dim)
        weight_sum = 0.0
        
        for token, vocab_idx in zip(tokens, encoded):
            # Look up the TF-IDF weight for this specific token
            tfidf_idx = tfidf_vocab.get(token)
            
            # If the word is in the TF-IDF vocabulary, use its weight. 
            # Otherwise, give it a tiny baseline weight so it isn't entirely ignored.
            weight = tfidf_row[tfidf_idx] if tfidf_idx is not None else 0.001
                
            # Multiply the FastText vector by the TF-IDF weight
            weighted_sum += embed_matrix[vocab_idx] * weight
            weight_sum += weight
            
        # Divide by the sum of weights to get the weighted average
        if weight_sum > 0:
            doc_embeds.append(weighted_sum / weight_sum)
        else:
            # Fallback to standard mean pooling if something went wrong
            token_vecs = embed_matrix[encoded]
            doc_embeds.append(np.mean(token_vecs, axis=0))
            
    return np.array(doc_embeds, dtype=np.float32)

def _build_features(
    train_rows: list[dict],
    eval_rows: list[dict],
) -> tuple[object, object]:
    """
    Fit TF-IDF on train text, transform both splits,
    then hstack with scaled features.
    Add FastText embeddings too.
    Returns (X_train, X_eval) as sparse matrices.
    """
    # TF-IDF (unigrams + bigrams, top 10k features)
    # Used COLX 521 lecture notes for concept
    # Claude used to help with code  
    tfidf = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=10_000,
        sublinear_tf=True, # applies log(1+tf) smoothing
        strip_accents="unicode",
        analyzer="word",
        token_pattern=r"\w+",
        min_df=2, # ignores rare words
    )
    train_tfidf = tfidf.fit_transform(_extract_texts(train_rows))
    eval_tfidf  = tfidf.transform(_extract_texts(eval_rows))

    # FastText embeddings
    vocab = build_vocab(train_rows)
    embed_matrix = load_fasttext_vectors(FASTTEXT_PATH, vocab)
        
    # train_embeddings = _get_embeddings(_extract_texts(train_rows), vocab, embed_matrix)
    # eval_embeddings  = _get_embeddings(_extract_texts(eval_rows), vocab, embed_matrix)

    # adjusted to tfidf embeddings to give important words more consideration in the corpus
    train_embeddings = _get_tfidf_weighted_embeddings(
        _extract_texts(train_rows), vocab, embed_matrix, tfidf, train_tfidf
    )
    eval_embeddings = _get_tfidf_weighted_embeddings(
        _extract_texts(eval_rows), vocab, embed_matrix, tfidf, eval_tfidf
    )

    # Linguistic features
    train_ling_raw = _extract_ling_features(train_rows)
    eval_ling_raw  = _extract_ling_features(eval_rows)

    #Scales numeric values
    scaler = StandardScaler()
    train_ling = scaler.fit_transform(train_ling_raw)
    eval_ling  = scaler.transform(eval_ling_raw)

    # Combines sparse TF-IDF and dense linguistic features
    # Used Claude to ensure properly combine sparse and dense features
    # add csr_matrix for embeddings
    X_train = hstack([train_tfidf, csr_matrix(train_ling), csr_matrix(train_embeddings)])
    X_eval  = hstack([eval_tfidf,  csr_matrix(eval_ling), csr_matrix(eval_embeddings)])

    return X_train, X_eval


# DSCI 571 lecture 6 referenced for code and concept
def _tune_and_fit(
    X_train,
    y_train: list[int],
    param_grid: dict = PARAM_GRID,
) -> LogisticRegression:
    """
    Run GridSearchCV over C values using 5-fold CV on train,
    scored by macro F1 (appropriate for imbalanced classes).
    Returns a fitted LogisticRegression with the best C.
    """
    base_model = LogisticRegression(
        max_iter=1000,
        solver="lbfgs",
        random_state=SEED,
        class_weight="balanced",  
    )

    gs = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        scoring="f1_macro",        
        cv=5,
        n_jobs=-1,
        refit=True,                
        verbose=0,
    )
    gs.fit(X_train, y_train)

    print(f"  Best C: {gs.best_params_['C']}  |  "
          f"CV macro-F1: {gs.best_score_:.4f}")
    return gs.best_estimator_


# API 
# Claude used as reference to match code to baseline_notebook.ipynb evaluation metrics and table
def run(
    train_rows: list[dict],
    dev_rows:   list[dict],
    task:       str = "opinion_label",
) -> tuple[list[int], list[int], list[float]]:
    """
    Train a logistic regression model on train_rows and evaluate on dev_rows.

    Parameters
    train_rows: list[dict]  
    dev_rows: list[dict]   
    task: str               

    Returns
    preds: list[int]   predictions (0 or 1)
    labels: list[int]  ground-truth labels
    probs: list[float] predicted probability for class 1 
    """
    valid_tasks = {"opinion_label", "misinformation_label"}
    if task not in valid_tasks:
        raise ValueError(f"task must be one of {valid_tasks}, got {task!r}")

    print(f"\n── Logistic Regression  [{task}] ──")

    # 1. Labels
    y_train = _extract_labels(train_rows, task)
    y_dev   = _extract_labels(dev_rows,   task)

    # 2. Features
    print("  Building features (TF-IDF, linguistic features, FastText embeddings)")
    X_train, X_dev = _build_features(train_rows, dev_rows)
    print(f"  Feature matrix: train={X_train.shape}, dev={X_dev.shape}")

    # 3. Hyperparameter search + fit train
    print("  Running GridSearchCV over C")
    model = _tune_and_fit(X_train, y_train)

    # 4. Predict on dev 
    preds  = model.predict(X_dev).tolist()
    probs  = model.predict_proba(X_dev)[:, 1].tolist()  # prob of class 1
    labels = y_dev

    return preds, labels, probs
