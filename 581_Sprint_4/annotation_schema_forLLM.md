# Annotation Schema

Annotation tags:
all_caps
exclamation_marks
hedging
adjectives
unk


1. For `all_caps`, please match words that are all capitalized. Don't include acronyms or single letters/characters that are capitalized.
2. For `exclamation_marks`, please annotate any number of exclamation marks.
3. For the `hedging` annotation, we are using a lexicon sourced from A Lexicon-Based Approach for Detecting Hedges in Informal Text (Islam et al., LREC 2020). It can be found here: https://github.com/hedging-lrec/resources/blob/master/hedge_words.txt. Match on the root of the word, e.g. presume / presumptive.
4. For `adjectives`, match words containing these specific suffixes:
    - `-ful`, `-less`, `-ment`, `-ness`, `-ing`, `-ible`
    - Example: "terrible", "disappointing"
    - Do not match on standalone words like "less", match only when it appears as a suffix. If any of these words have one of the specified suffixes, but are not used as an adjective in the text, do not annotate.
5. For `unk`, annotate any profanity. 
