# Annotation Schema

1. Download Docker (https://www.docker.com/products/docker-desktop/) and have it open.
2. Follow instructions at this Label Studio link (https://labelstud.io/learn/getting-started-with-label-studio/setting-up-label-studio/)

```powershell
docker run -it -p 8080:8080 -v pwd/mydata:/label-studio/data heartexlabs/label-studio:latest
```

3. Launch the local server and create an account.
4. Create a new project.
5. Import the .csv of text to label.
6. Use the model template for Named Entity Recognition and replace labels with the following:

```
all_caps
exclamation_marks
hedging
adjectives
unk
```

7. Select the label first, and then drag the cursor over the selection of text that applies. You will need to re-select the label each time you start labeling a new span.
8. It's ok if there's nothing to add/annotate, still submit it to show you have reviewed it.
9. For `all_caps`, please match words that are all capitalized. Don't include acronyms or single letters/characters that are capitalized.
10. For `exclamation_marks`, please annotate any number of exclamation marks.
11. For the `hedging` annotation, match based on the lexicon sourced from *A Lexicon-Based Approach for Detecting Hedges in Informal Text* (Islam et al., LREC 2020).
    It can be found here: https://github.com/hedging-lrec/resources/blob/master/hedge_words.txt.
12. For `adjectives`, match words containing these specific suffixes:
    - `-ful`, `-less`, `-ment`, `-ness`, `-ing`, `-ible`
    - Example: "terrible", "disappointing"
    - Do not match on standalone words like "less", match only when it appears as a suffix. If any of these words have one of the specified suffixes, but are not used as an adjective in the text, do not annotate.
13. For `unk`, we anticipate that there may be ambiguous words that are pertinent, but don't clearly meet the existing categories. Use this annotation to mark those instances.
14. Once completing an instance, remember to click **Submit** to save the specific annotation.
15. Once completed all instances, click **Export** to download the annotated data, and choose `.JSON`.
