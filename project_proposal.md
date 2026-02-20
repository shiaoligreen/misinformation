# Project Proposal
**Project:** COLX_523: Misinformation — Linguistic Markers in False vs. Verified News Headlines

**Members:** Jennifer, Nicole, Shiao-li, Rachelle
---

We aim to build an annotated corpus that captures linguistic patterns distinguishing misinformation, opinion/editorial, from verified news.  Our goal is to produce a dataset resource useful for researchers studying how language signals credibility — or the lack of it. We plan to enhance the Twitter Misinformation Dataset that is currently available on Hugging Face with the goal of contributing the enhanced dataset to Hugging Face.

---

## Research Focus

**Questions:** 

What linguistic markers distinguish false news headlines from verified ones?

Is there a way to distinguish a third category of information? Not all social media posts and news items exist as completely composed of fact or completely composed of misinformation. For example, a newspaper editorial likely contains facts, as well as opinions. Some social media posts are all about emotion without any facts and without any misinformation. 

**Hypothesis:**  
News and social media texts will have measurable differences in linguistic features — such as higher use of superlatives, emotional language, capitalization, vague sourcing, and clickbait phrasing, depending on whether the text aims to diseminate factual information, spread misinformation or express emotions and opinions.

The annotation task associated with this project operates at both the token span and document level: annotators will tag specific linguistic features within the text (token), as well as classify the overall category of the document (document-level sentiment).

---

## Data Sources

We will draw on the following Hugging Face dataset:

**Twitter Misinformation dataset** ([Hugging Face Roupeminassian Twitter Misinformation](https://huggingface.co/datasets/roupenminassian/twitter-misinformation))

In addition, we will perform some scrapping via Google News rss feed at https://news.google.com/rss/search?q=computational+linguistics

**Combined target size:** 

The Twitter Misinformation dataset has over 100,000 examples of text, with a total of 19,426,418 space-separated words from Twitter, as well as news sources. 

**Genre:** 

The genre is news and social media.

**Metadata:** 

The metadata provided in the dataset consists of either a 1 or 0, indicating misinformation or fact.

**Legal status:** All datasets are publicly available for research use under their respective licenses (academic/non-commercial). Web scraping is not required — data is directly downloadable or API-accessible.

---

## Annotation Plan

**What we are annotating:** 

Individual news stories as well as social media posts. 

**Annotation schema:** 
Consistent with the Twitter Misinformation dataset, we will use the following:

- 0 indicates a factual text

- 1 indicates misinformational text

We will add the following third class of categorization:

2 indicates a text primarily concerned with opinions and emotions.

We will add additional, still to be decided, metadata fields.

**Potential Markers to Annotate**

  *Lexical Markers*

  - Hedging language: words like "allegedly," "reportedly," "sources say" suggest caution and epistemic humility (often more credible)
  - Absolutist language: "always," "never," "everyone knows," "100%" often signal low credibility
  - Emotionally charged words: "disgusting," "outrageous," "terrifying" — misinformation tends to be more emotionally manipulative
  - Superlatives: "the worst ever," "the biggest," "the most incredible"

  *Syntactic Markers*

  - Sentence complexity: credible news tends to use more varied, complex sentence structures
  - Passive voice: formal journalism uses it more ("it was reported that...")
  - Question marks: rhetorical questions are more common in sensationalist content

  *Discourse Markers*

  - Attribution: credible text cites sources explicitly ("Reuters reported," "according to...")
  - Quotes: direct quotes with named sources signal credibility
  - Specificity: exact dates, numbers, named individuals vs. vague claims

  *Stylistic Markers*

  - ALL CAPS: common in low-credibility content
  - Exclamation marks: overuse signals sensationalism
  - Clickbait patterns: "You won't believe...", "Here's what they don't want you to know"
  - Spelling/grammar errors: correlated with lower credibility sources

  *Pragmatic Markers*

  - Presupposition: assuming facts not in evidence ("as we all know, Obama...")
  - Us vs. them framing: strong in-group/out-group language
  - Conspiracy framing: references to hidden agendas, cover-ups

  *Readability Metrics*

  - Flesch-Kincaid score: reading level; misinformation often skews simpler
  - Type-token ratio: vocabulary richness
  - Average word/sentence length


---

## Corpus Collection POC (Sprint 1 Goal)

- Write a script to load one document (headline + label) from each of the three datasets
- Confirm data access, formatting, and label compatibility across sources
- Outline a merging plan for combining datasets into a unified format

---


