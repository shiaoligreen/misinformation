# Corpus README
**Project:** COLX_523 — Linguistic Markers in False, Opinionated, and Verified News and Social Media Posts
**Members:** Jennifer, Nicole, Shiao-li, Rachelle

---

## Source

**Dataset:** Twitter Misinformation Dataset (roupenminassian)
**HuggingFace URL:** https://huggingface.co/datasets/roupenminassian/twitter-misinformation

Despite its name, this dataset is a compilation of four sources: the Fake and Real News Dataset (Kaggle), NLP Disaster Tweets (Kaggle), Natural Hazards Twitter Dataset, and the MuMiN Dataset. It contains text from both news articles and social media (Twitter).

---

## Collected Corpus Location

**GitHub repository:** 

The collected corpus is stored at `data/raw/complete_dataset.csv` within the repository.

---

## Format

- **File:** `complete_dataset.csv`
- **File format:** CSV 
- **Columns:**

| Column | Type | Description |
|--------|------|-------------|
| `text` | string | Full text of the news article or social media post |
| `label` | integer | Document-level class label: `0` = factual, `1` = misinformation |

---

## Corpus Statistics

| Metric | Value |
|--------|-------|
| Total documents | 102,761 |
| Total tokens (space-separated) | 19,947,798 |
| Unique word types | 162,964 |
| Total sentences | 770,787 |
| Average article length | 194.12 words |
| Average sentence length | 25.88 words |
| Average word length | 4.81 characters |

**Label distribution:**

| Label | Meaning | Count |
|-------|---------|-------|
| 0 | Factual | 67,182 |
| 1 | Misinformation | 35,579 |

---

## Known Problems

**Duplicate documents:** 16,737 exact duplicate rows were identified (by text). These have not been removed from the corpus at this stage and should be accounted for during annotation and analysis.

**Noise:** Some texts contain embedded URLs (e.g. `https://t.co/...`, `pic.twitter.com/...`) and social media artifacts such as Twitter handles and retweet markers. These appear in the top frequent words and bigrams (`https co`, `twitter com`, `pic twitter`) and may need to be filtered depending on the annotation task.

**Text Lengths:** The corpus contains texts of varying lengths — from short tweets and headlines (often under 20 words) to full news articles (potentially hundreds of words). This imbalance in text length across sources should be accounted for during analysis, as length alone may correlate with label or source type rather than linguistic content.
