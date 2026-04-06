"""
logreg_baseline.py
──────────────────
Logistic Regression baseline for COLX 523 / COLX 581 Sprint 1.

Concepts and code templates were used from past lecture notes (DSCI 572 lecture 2; DSCI 571 lecture 6, 8; COLX 521 lecture 4, 7). 
In addition, Claude was used in the implementation of the code and to supplement my existing knowledge of concepts, when needed. 
These citations have been noted and all comments are my own. 

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

def _build_features(
    train_rows: list[dict],
    eval_rows: list[dict],
) -> tuple[object, object]:
    """
    Fit TF-IDF on train text, transform both splits,
    then hstack with scaled features.

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

    # Linguistic features
    train_ling_raw = _extract_ling_features(train_rows)
    eval_ling_raw  = _extract_ling_features(eval_rows)

    #Scales numeric values
    scaler = StandardScaler()
    train_ling = scaler.fit_transform(train_ling_raw)
    eval_ling  = scaler.transform(eval_ling_raw)

    # Combines sparse TF-IDF and dense linguistic features
    # Used Claude to ensure properly combine sparse and dense features
    X_train = hstack([train_tfidf, csr_matrix(train_ling)])
    X_eval  = hstack([eval_tfidf,  csr_matrix(eval_ling)])

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
    print("  Building features (TF-IDF + linguistic)")
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
