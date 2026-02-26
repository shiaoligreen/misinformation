"""
Corpus_Analysis(Sprint2_Optional).py

Fake vs. True News Corpus Statistics
Applies corpus analysis techniques to:
  - Fake.csv            — external reference dataset (Kaggle)
  - True.csv            — external reference dataset (Kaggle) 
  - complete_dataset.csv — combined project corpus (local, data/raw/)

Source: https://www.kaggle.com/datasets/emineyetm/fake-news-detection-datasets

SETUP — before running this script:
  pip install gdown
"""

import pandas as pd
import re
import matplotlib.pyplot as plt
from collections import Counter
import nltk
import os
import gdown

nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize



# Load Data

# External reference datasets (Kaggle, via Google Drive)
# Downloaded at runtime to /tmp/ — outside this repository, not committed to git.
print("Downloading Fake.csv from Google Drive ...")
FAKE_CSV_PATH = "/tmp/Fake.csv"
gdown.download(id="1dgqVckR7EVKP6aBcdp-6A4pgVbJzITLO", output=FAKE_CSV_PATH, quiet=False)

print("Downloading True.csv from Google Drive ...")
TRUE_CSV_PATH = "/tmp/True.csv"
gdown.download(id="1CmudATI6Jv0CaPKSvB_gN2Bd0z3OS2pw", output=TRUE_CSV_PATH, quiet=False)

# Project corpus (relative to this script in src/) 
script_dir = os.path.dirname(os.path.abspath(__file__))
COMPLETE_DATASET_PATH = os.path.join(script_dir, "..", "data", "raw", "complete_dataset.csv")


fake_df = pd.read_csv(FAKE_CSV_PATH)
true_df = pd.read_csv(TRUE_CSV_PATH)
complete_df = pd.read_csv(COMPLETE_DATASET_PATH)

print("\nFake News")
print(f"Shape: {fake_df.shape}")
print(fake_df.head(2))

print("\nTrue News")
print(f"Shape: {true_df.shape}")
print(true_df.head(2))

print("\nComplete Dataset")
print(f"Shape: {complete_df.shape}")
print(complete_df.head(2))

# Fake/True combine title + text (complete_dataset has text only)
fake_texts     = (fake_df['title'] + ' ' + fake_df['text']).tolist()
true_texts     = (true_df['title'] + ' ' + true_df['text']).tolist()
complete_texts = complete_df['text'].astype(str).tolist()

print(f"\nFake articles:     {len(fake_texts):,}")
print(f"True articles:     {len(true_texts):,}")
print(f"Complete articles: {len(complete_texts):,}")



# Data Quality — complete_dataset.csv only
# (label distribution, nulls, and duplicates are specific to our corpus)
print("\n\nData Quality: complete_dataset.csv")
print(f"\nLabel distribution:\n{complete_df['label'].value_counts().sort_index()}")
print(f"\nMissing values:\n{complete_df[['text', 'label']].isnull().sum()}")
print(f"\nExact duplicate rows (by text): {complete_df.duplicated(subset='text').sum()}")



# Tokenization

def tokenize_raw(texts):
    """Tokenize into a lowercase word list (no stopword removal)."""
    all_text = ' '.join(texts)
    return re.findall(r"[a-zA-Z]+", all_text.lower())

fake_tokens_raw     = tokenize_raw(fake_texts)
true_tokens_raw     = tokenize_raw(true_texts)
complete_tokens_raw = tokenize_raw(complete_texts)

fake_types_raw     = set(fake_tokens_raw)
true_types_raw     = set(true_tokens_raw)
complete_types_raw = set(complete_tokens_raw)

print(f"\n\nTokenization")
print(f"\nFake News:\n  Tokens: {len(fake_tokens_raw):,}\n  Types:  {len(fake_types_raw):,}")
print(f"\nTrue News:\n  Tokens: {len(true_tokens_raw):,}\n  Types:  {len(true_types_raw):,}")
print(f"\nComplete Dataset:\n  Tokens: {len(complete_tokens_raw):,}\n  Types:  {len(complete_types_raw):,}")



# Type-Token Ratio (TTR)

def type_token_ratio(tokens, num_words=None):
    """Calculate TTR from the first num_words tokens."""
    if num_words is None:
        num_words = len(tokens)
    subset = tokens[:num_words]
    return len(set(subset)) / len(subset)

# Use sample sizes that are valid for all three datasets
max_sample = min(len(fake_tokens_raw), len(true_tokens_raw), len(complete_tokens_raw))
sample_sizes = [n for n in [1_000, 10_000, 50_000] if n <= max_sample]

print(f"\n\nType-Token Ratio")
print(f"{'Sample Size':<15} {'Fake TTR':<15} {'True TTR':<15} {'Complete TTR':<15}")
for n in sample_sizes:
    print(f"{n:<15,} "
          f"{type_token_ratio(fake_tokens_raw, n):<15.4f} "
          f"{type_token_ratio(true_tokens_raw, n):<15.4f} "
          f"{type_token_ratio(complete_tokens_raw, n):<15.4f}")
print(f"{'Full corpus':<15} "
      f"{type_token_ratio(fake_tokens_raw):<15.4f} "
      f"{type_token_ratio(true_tokens_raw):<15.4f} "
      f"{type_token_ratio(complete_tokens_raw):<15.4f}")



# Corpus Statistics

def corpus_stats(texts, tokens_raw, label):
    """Compute basic corpus statistics."""
    num_tokens      = len(tokens_raw)
    num_types       = len(set(tokens_raw))
    num_chars       = sum(len(w) for w in tokens_raw)
    avg_word_len    = num_chars / num_tokens if num_tokens else 0
    all_sents       = [s for text in texts for s in sent_tokenize(text)]
    num_sents       = len(all_sents)
    avg_sent_len    = num_tokens / num_sents if num_sents else 0
    num_articles    = len(texts)
    avg_article_len = num_tokens / num_articles if num_articles else 0

    print(f"\n{label}")
    print(f"  Articles:          {num_articles:>10,}")
    print(f"  Total tokens:      {num_tokens:>10,}")
    print(f"  Unique types:      {num_types:>10,}")
    print(f"  Total sentences:   {num_sents:>10,}")
    print(f"  Avg word length:   {avg_word_len:>10.2f} chars")
    print(f"  Avg sentence len:  {avg_sent_len:>10.2f} words")
    print(f"  Avg article len:   {avg_article_len:>10.2f} words")

    return {
        'label': label, 'articles': num_articles, 'tokens': num_tokens,
        'types': num_types, 'sentences': num_sents, 'avg_word_len': avg_word_len,
        'avg_sent_len': avg_sent_len, 'avg_article_len': avg_article_len
    }

print(f"\n\nCorpus Statistics")
fake_stats     = corpus_stats(fake_texts,     fake_tokens_raw,     'Fake News')
true_stats     = corpus_stats(true_texts,     true_tokens_raw,     'True News')
complete_stats = corpus_stats(complete_texts, complete_tokens_raw, 'Complete Dataset')



# Stopword Removal

stop_words = set(stopwords.words('english'))

def tokenize_content(texts):
    """Tokenize and remove stopwords."""
    all_text = ' '.join(texts)
    tokens = re.findall(r"[a-zA-Z]+", all_text.lower())
    return [t for t in tokens if t not in stop_words]

fake_tokens     = tokenize_content(fake_texts)
true_tokens     = tokenize_content(true_texts)
complete_tokens = tokenize_content(complete_texts)

fake_types     = set(fake_tokens)
true_types     = set(true_tokens)
complete_types = set(complete_tokens)

print(f"\n\nTokenization (stopwords removed)")
print(f"\nFake News:\n  Tokens: {len(fake_tokens):,}\n  Types:  {len(fake_types):,}")
print(f"\nTrue News:\n  Tokens: {len(true_tokens):,}\n  Types:  {len(true_types):,}")
print(f"\nComplete Dataset:\n  Tokens: {len(complete_tokens):,}\n  Types:  {len(complete_types):,}")



# Zipf's Law

fake_counts     = Counter(fake_tokens)
true_counts     = Counter(true_tokens)
complete_counts = Counter(complete_tokens)

print(f"\n\nTop 20 Most Frequent Words (stopwords removed)")
print(f"\n{'Rank':<6} {'Fake Word':<20} {'Fake Freq':<12} {'True Word':<20} {'True Freq':<12} {'Complete Word':<20} {'Complete Freq'}")
for i, ((fw, fc), (tw, tc), (cw, cc)) in enumerate(
    zip(fake_counts.most_common(20),
        true_counts.most_common(20),
        complete_counts.most_common(20)), 1
):
    print(f"{i:<6} {fw:<20} {fc:<12,} {tw:<20} {tc:<12,} {cw:<20} {cc:,}")



# N-gram Analysis

def get_ngrams(tokens, n):
    """Extract n-grams from a token list."""
    return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

fake_bigrams     = Counter(get_ngrams(fake_tokens, 2))
true_bigrams     = Counter(get_ngrams(true_tokens, 2))
complete_bigrams = Counter(get_ngrams(complete_tokens, 2))

print(f"\n\nTop 10 Bigrams (stopwords removed)")

print("\nFake News")
for bg, count in fake_bigrams.most_common(10):
    print(f"  {' '.join(bg):<30} {count:,}")

print("\nTrue News")
for bg, count in true_bigrams.most_common(10):
    print(f"  {' '.join(bg):<30} {count:,}")

print("\nComplete Dataset")
for bg, count in complete_bigrams.most_common(10):
    print(f"  {' '.join(bg):<30} {count:,}")
