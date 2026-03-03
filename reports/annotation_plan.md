# Annotation Plan

## Annotation Motivation

Having looked at the data, we believe the following linguistic markers will strike a good balance between being informative and manageable/scalable.

### Stylistic Markers

Mark the span and/or count the occurrences of ALL CAPS words, words with typos, and exclamation marks (repeated would increase the count).

### Lexical Markers

Hedging language like "allegedly," "reportedly," "sources say" can be identified using this [lexicon](https://github.com/hedging-lrec/resources/blob/master/hedge_words.txt) resource available on GitHub.

To facilitate the 3rd label to be identified, we can use this emotion [lexicon](https://saifmohammad.com/WebPages/NRC-Emotion-Lexicon.htm) and count words that match each of the 8 emotion categories. Note that words can belong to multiple emotions.

## Annotation Guide

With all of the above annotations, it will make sense to normalise by text length, given that the length of text varies significantly between an article and a headline or tweet, which is maxed at 280 characters.

We will use Label Studio to carry out the annotation and do the initial 1000 items between us, before considering scaling it up by automating the process.

This will result in 6 additional columns in the dataset, which will store each of these additional annotations:

1. `all_caps`: 'NOW', 'STOP'
2. `exclamation_marks`: '!', '!!', '!'
3. `hedging`: 'allegedly', 'reportedly'
4. `adjectives`: 'disappointing', 'terrible'
5. `unk`: any unknown

Removed after pilot study:

- `typos`: 'wont', 'docter'
- `emotion`: words in any of the 8 emotion categories

### Discussion

For the `hedging` annotation, we are using a lexicon sourced from [A Lexicon-Based Approach for Detecting Hedges in Informal Text](https://aclanthology.org/2020.lrec-1.380/) (Islam et al., LREC 2020). It can be found here: https://github.com/hedging-lrec/resources/blob/master/hedge_words.txt.

For the `emotion` annotation, we had intended to use the nrclex library, which implements the NRC Emotion Lexicon (Mohammad & Turney, 2013).

Considerations for automated annotation vary. The most trustworthy for automation are the `all_caps` and `exclamation_marks` annotations, since they are character-level string operations and unambiguous. We will have to account for all caps in the case of acronyms (e.g. USA) where this is not emphatic.

The `hedging` and `emotion` annotations will be annotated based on two predefined lexica in order to minimize variance in human interpretations of the expressions of hedging and emotion.

However, there are limitations for automated annotation when relying on a lexicon to identify hedging. Automated processes may miss expressions of hedging that are syntactic in nature or operating across the entire text, without the presence of the specific words we have outlined in our lexicon.

A word level approach to annotating emotion is somewhat less exposed to this issue, as individual words are generally stable in their expression of emotion. Any ambiguity might be buffered by scoring across the 8 emotion categories.

The `typos` annotation may prove to be the most difficult to automate, particularly given the tweets in our data, which would be full of slang and informal language that are likely to be flagged by an automated spellchecker.

## Annotation Quantity

We will annotate 1000 items between us + one AI with 100% overlap. This distribution will allow there to be both pairwise and 5-way overlap.

| Annotator | 5-Way Overlap | Pairwise Overlaps | Solo Assignment (Human + AI) | Total Workload |
| :--- | :--- | :--- | :--- | :--- |
| **Jennifer** | 0–40 | 41–100 | 161–370 | 310 items |
| **Nicole** | 0–40 | 41–60, 101–140 | 371–580 | 310 items |
| **Rachelle** | 0–40 | 61–80, 101–120, 141–160 | 581–790 | 310 items |
| **Shiao-li** | 0–40 | 81–100, 121–160 | 791–1000 | 310 items |
| **AI** | 0–40 | 41–160 | 161–1000 | 1000 items |

## Pilot Study

The pilot study consists of 10 examples, across all types of data in our dataset. 2 samples each from:

- Reuters Articles
- Fake news
- Non-disaster tweets
- Disaster Tweets
- Google News Headline

After looking at the first item of the pilot study, we decided to remove the `typo` label because of slang and informal language.

We also decided to pivot from `emotion` to `adjectives` using specific suffixes (`-ful`, `-less`, `-ment`, `-ness`, `-ing`, `-ible`), given the size of the lexicon and making sure annotation is realistic while also not encoding words that may be less informative. (Not standalone like "more" or "less" — **only** when it appears as a suffix.)

The code to retrieve these items can be found here: https://github.ubc.ca/shiaolig/COLX_523_misinformation/blob/main/src/Pilot_Dataset_Builder.py

### Pilot Study Results

`.JSON` of annotation results with the span of text and the corresponding label can be found for the human and AI components, in `data/preprocessed`: https://github.ubc.ca/shiaolig/COLX_523_misinformation/tree/main/data/preprocessed

### Discussion

On the human side, we removed the `typos` and `emotion` annotations and added an `adjectives` annotation, and we iterated on the `adjectives` annotation to specify which suffixes to use. Additionally, for the hedging, we clarified that we should look to match the root of the word with our lexicon.

We also realised that there will be some items that will have no/blank annotations, but should still be submitted and recognised for this 'empty' state.

For the AI annotator, it correctly identified the `all_caps` and did not annotate ACL (an acronym to be excluded). It needed further clarification for the word "learning", to recognize that it shouldn't be annotated under `adjectives`.
