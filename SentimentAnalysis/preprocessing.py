"""
preprocessing.py
================

Part 1 of the assignment: turn a raw review into a clean token list.

Pipeline, in order:

1. Strip the ``<br />`` HTML tags that appear throughout IMDb reviews.
2. Lowercase.
3. Expand contractions ending in ``n't`` into ``not`` ("didn't" -> "did not"),
   so that negation survives punctuation removal as its own token.
4. Tokenize with NLTK's ``TreebankWordTokenizer`` (no model download needed).
5. Strip punctuation from token edges and drop tokens left empty.
6. Optionally drop stopwords, but never negation words: "not good" and
   "good" mean opposite things, and bigrams/trigrams can only capture that
   if "not" is still there.
"""

from __future__ import annotations

import re
import string

from nltk.tokenize import TreebankWordTokenizer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

_tokenizer = TreebankWordTokenizer()

_HTML_TAG = re.compile(r"<[^>]+>")
_NEGATED_CONTRACTION = re.compile(r"(\w+)n't\b")
_PUNCT = string.punctuation + "’“”"

NEGATION_WORDS = frozenset(
    {"no", "not", "nor", "never", "none", "nobody", "nothing", "neither", "nowhere", "cannot"}
)
# sklearn's list includes negations; removing them would erase exactly the
# signal n-grams are supposed to capture.
STOPWORDS = frozenset(ENGLISH_STOP_WORDS) - NEGATION_WORDS


def clean_text(text: str) -> str:
    """Steps 1-3: remove HTML, lowercase, expand n't contractions."""
    text = _HTML_TAG.sub(" ", text).lower()
    text = text.replace("can't", "can not").replace("won't", "will not")
    return _NEGATED_CONTRACTION.sub(r"\1 not", text)


def tokenize(text: str, remove_stopwords: bool = False) -> list[str]:
    """Full pipeline: raw review -> list of tokens."""
    # Treebank only splits the period at the very end of the input, so
    # mid-text tokens like "it." still carry punctuation: strip their edges.
    tokens = (t.strip(_PUNCT) for t in _tokenizer.tokenize(clean_text(text)))
    tokens = [t for t in tokens if t]
    if remove_stopwords:
        tokens = [t for t in tokens if t not in STOPWORDS]
    return tokens


def preprocess(text: str, remove_stopwords: bool = False) -> str:
    """Tokens joined by spaces, the format CountVectorizer consumes in features.py."""
    return " ".join(tokenize(text, remove_stopwords))


if __name__ == "__main__":
    sample = "I didn't like it.<br /><br />The acting wasn't BAD, but the plot? Not great!"
    print(tokenize(sample))
    print(tokenize(sample, remove_stopwords=True))
