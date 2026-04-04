"""
Tweet preprocessing pipeline.

Steps:
   tweet-preprocessor tokenize() — replaces with special tokens:
       @mention   → $MENTION$
       URL        → $URL$
       #hashtag   → $HASHTAG$
       :) smileys → $SMILEY$
       😊 emojis  → $EMOJI$
       numbers    → $NUMBER$
     Note: 'RT' is left as-is (preprocessor treats it as a reserved word
     but does NOT replace it by default in tokenize() mode).

   Strip the '$' delimiters from preprocessor tokens so TweetTokenizer
     keeps them as single word tokens:
       $MENTION$ → MENTION,  $URL$ → URL,  etc.

   NLTK TweetTokenizer(reduce_len=True) — word tokenization.
     reduce_len collapses repeated chars to max 3 (e.g. "sooooo" → "sooo").
"""

import re

import preprocessor as p
from nltk.tokenize import TweetTokenizer

#learned about the existence of TweetTokenizer from Gemini. 
_tokenizer   = TweetTokenizer(reduce_len=True)

#regex help from Gemini
_STRIP_DOLLARS = re.compile(r'\$([A-Z]+)\$')


def preprocess(text: str) -> list[str]:
    """Return a list of tokens for a single tweet/post."""
    cleaned = p.tokenize(text)
    cleaned = _STRIP_DOLLARS.sub(r'\1', cleaned)   # $URL$ → URL, $MENTION$ → MENTION, …
    return _tokenizer.tokenize(cleaned)
