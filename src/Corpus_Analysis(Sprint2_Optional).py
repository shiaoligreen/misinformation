# Fake vs. True News Corpus Statistics

### This notebook applies the statistics and corpus analysis techniques to two datasets:
### **Fake.csv** — fake news articles
### **True.csv** — true news articles

### https://www.kaggle.com/datasets/emineyetm/fake-news-detection-datasets?resource=download


import pandas as pd
import re
import matplotlib.pyplot as plt
from collections import Counter
import nltk

nltk.download('stopwords', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize



# Load Data 

fake_df = pd.read_csv('Fake.csv')
true_df = pd.read_csv('True.csv')

print("Fake News")
print(f"Shape: {fake_df.shape}")
print(fake_df.head(2))

print("\n\nTrue News")
print(f"Shape: {true_df.shape}")
print(true_df.head(2))

fake_texts = (fake_df['title'] + ' ' + fake_df['text']).tolist()
true_texts = (true_df['title'] + ' ' + true_df['text']).tolist()

print(f"\nFake articles: {len(fake_texts)}")
print(f"True articles: {len(true_texts)}")



# Tokenization 

def tokenize_raw(texts):
    """Tokenize into a lowercase word list."""
    all_text = ' '.join(texts)
    return re.findall(r"[a-zA-Z]+", all_text.lower())

fake_tokens_raw = tokenize_raw(fake_texts)
true_tokens_raw = tokenize_raw(true_texts)

fake_types_raw = set(fake_tokens_raw)
true_types_raw = set(true_tokens_raw)

print(f"\nFake News: \nTokens: {len(fake_tokens_raw):,} \nTypes: {len(fake_types_raw):,}")
print(f"\n\nTrue News: \nTokens: {len(true_tokens_raw):,} \nTypes: {len(true_types_raw):,}")



# Type-Token Ratio (TTR)

def type_token_ratio(tokens, num_words=None):
    """Calculate TTR from the first num_words tokens."""
    if num_words is None:
        num_words = len(tokens)
    subset = tokens[:num_words]
    return len(set(subset)) / len(subset)

sample_sizes = [1_000, 10_000, 50_000]

print("\nType-Token Ratio")
print(f"{'Sample Size':<15} {'Fake TTR':<15} {'True TTR':<15}")
for n in sample_sizes:
    print(f"{n:<15,} {type_token_ratio(fake_tokens_raw, n):<15.4f} {type_token_ratio(true_tokens_raw, n):<15.4f}")
print(f"{'Full corpus':<15} {type_token_ratio(fake_tokens_raw):<15.4f} {type_token_ratio(true_tokens_raw):<15.4f}")



# Corpus Statistics 

def corpus_stats(texts, tokens_raw, label):
    """Compute basic corpus statistics."""
    num_tokens = len(tokens_raw)
    num_types  = len(set(tokens_raw))
    num_chars  = sum(len(w) for w in tokens_raw)

    avg_word_len    = num_chars / num_tokens if num_tokens else 0
    all_sents       = [s for text in texts for s in sent_tokenize(text)]
    num_sents       = len(all_sents)
    avg_sent_len    = num_tokens / num_sents if num_sents else 0
    num_articles    = len(texts)
    avg_article_len = num_tokens / num_articles if num_articles else 0

    print(f"\n\n{label}")
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

fake_stats = corpus_stats(fake_texts, fake_tokens_raw, 'Fake News')
true_stats = corpus_stats(true_texts, true_tokens_raw, 'True News')



# Stopword Removal

stop_words = set(stopwords.words('english'))

def tokenize_content(texts):
    """Tokenize and remove stopwords."""
    all_text = ' '.join(texts)
    tokens = re.findall(r"[a-zA-Z]+", all_text.lower())
    return [t for t in tokens if t not in stop_words]

fake_tokens = tokenize_content(fake_texts)
true_tokens = tokenize_content(true_texts)

fake_types = set(fake_tokens)
true_types = set(true_tokens)

print(f"\nFake News: \nTokens: {len(fake_tokens):,} \nTypes: {len(fake_types):,}")
print(f"\n\nTrue News: \nTokens: {len(true_tokens):,} \nTypes: {len(true_types):,}")



# Zipf's Law 

fake_counts = Counter(fake_tokens)
true_counts = Counter(true_tokens)

print("\nTop 20 Most Frequent Words")
print(f"{'Rank':<6} {'Fake Word':<20} {'Fake Freq':<12} {'True Word':<20} {'True Freq'}")

for i, ((fw, fc), (tw, tc)) in enumerate(zip(fake_counts.most_common(20), true_counts.most_common(20)), 1):
    print(f"{i:<6} {fw:<20} {fc:<12,} {tw:<20} {tc:,}")



# N-gram Analysis

def get_ngrams(tokens, n):
    """Extract n-grams from a token list."""
    return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

fake_bigrams = Counter(get_ngrams(fake_tokens, 2))
true_bigrams = Counter(get_ngrams(true_tokens, 2))

print("\nFake News: \nTop 10 Bigrams\n")
for bg, count in fake_bigrams.most_common(10):
    print(f"  {' '.join(bg):<30} {count:,}")

print("\n\nTrue News: \nTop 10 Bigrams\n")
for bg, count in true_bigrams.most_common(10):
    print(f"  {' '.join(bg):<30} {count:,}")
