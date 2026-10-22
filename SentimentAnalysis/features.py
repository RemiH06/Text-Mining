"""
features.py
===========

Part 2 of the assignment: represent each review as an n-gram count vector.

The text arriving here is already preprocessed (space-separated tokens), so
the vectorizer just splits on whitespace instead of re-tokenizing.

``NGRAM_CONFIGS`` lists the n-gram ranges compared in Part 3. Pure bigram and
trigram vectors are included to isolate what each order contributes on its
own; (1, 3) is the configuration the assignment asks for explicitly.
"""

from __future__ import annotations

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

NGRAM_CONFIGS: dict[str, tuple[int, int]] = {
    "unigram": (1, 1),
    "bigram": (2, 2),
    "trigram": (3, 3),
    "uni+bi": (1, 2),
    "uni+bi+tri": (1, 3),
}


def build_vectorizer(
    ngram_range: tuple[int, int] = (1, 3),
    min_df: int = 2,
    max_features: int | None = None,
    tfidf: bool = False,
) -> CountVectorizer:
    """Return an unfitted vectorizer for preprocessed text.

    min_df=2 drops n-grams that appear in a single review. With trigrams this
    removes most of the vocabulary (typos, one-off phrases) at almost no cost
    in accuracy, and keeps the matrices small enough for a laptop.
    """
    cls = TfidfVectorizer if tfidf else CountVectorizer
    return cls(
        ngram_range=ngram_range,
        min_df=min_df,
        max_features=max_features,
        tokenizer=str.split,
        token_pattern=None,
        lowercase=False,
    )
