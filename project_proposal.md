# Project Proposal
**Project:** COLX_523: Misinformation — Linguistic Markers in False vs. Verified News Headlines

**Members:** Jennifer, Nicole, Shiao-li, Rachelle
---

We aim to build an annotated corpus that captures linguistic patterns distinguishing misinformation from verified news, drawing on multiple complementary datasets. Our goal is to produce a resource useful for researchers studying how language signals credibility — or the lack of it.

---

## Research Focus

**Question:** What linguistic markers distinguish false news headlines from verified ones?

**Hypothesis:** Headlines from misinformation sources will have measurable differences in linguistic features — such as higher use of superlatives, emotional language, vague sourcing, and clickbait phrasing — compared to fact-checked, verified headlines.

This annotation task operates at the **span and document level**: annotators will tag specific linguistic features within headlines (token/span), as well as classify the overall headline (document-level sentiment/framing category).

---

## Data Sources

We will draw on complementary datasets:

**1. Fake News Detection Datasets** ([Kaggle](https://www.kaggle.com/datasets/emineyetm/fake-news-detection-datasets))
A well-structured collection including LIAR, ISOT, and others with headline + body text and binary/multiclass labels. Good coverage of political and general news domains.

**2. MuMiN: A Large-Scale Multilingual Multimodal Fact-Checked Misinformation Social Network Dataset** ([mumin-dataset.github.io](https://mumin-dataset.github.io/))
A large-scale multilingual dataset linking social media posts to fact-checked claims. Introduces a multilingual and social-context dimension. **Note:** Integration of MuMiN requires refinement — we will scope our use to English-language subsets and headline-equivalent claim text in Sprint 1–2, and revisit multilingual expansion based on feasibility.

**Combined target size:** 

**Genre:** 

**Metadata:** 

**Legal status:** All datasets are publicly available for research use under their respective licenses (academic/non-commercial). Web scraping is not required — data is directly downloadable or API-accessible.

---

## Annotation Plan

**What we are annotating:** Individual news headlines and fact-checked claim texts.

**Annotation schema:** 


---

## Corpus Collection POC (Sprint 1 Goal)

- Write a script to load one document (headline + label) from each of the three datasets
- Confirm data access, formatting, and label compatibility across sources
- Outline a merging plan for combining datasets into a unified format

---


