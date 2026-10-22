"""
error_analysis.py
=================

Part 5 of the assignment: pull out misclassified reviews and tag them with
simple linguistic cues so the manual inspection has something to start from.

The tags are heuristics, not ground truth. They point at the usual suspects
for a bag-of-n-grams model:

- negation:   "not bad", "never boring" flip the polarity of the next words,
              which an n-gram only captures if the exact phrase was seen.
- contrast:   "the cast is great, but the film is a mess": the verdict
              usually follows the connective, but counts weigh both halves.
- sarcasm:    exaggerated praise markers ("oh great", "yeah right") or
              scare quotes; positive words used to mean the opposite.
- mixed:      the original rating is 4 or 7, the closest to neutral that
              IMDb keeps, so the review is lukewarm by construction.
"""

from __future__ import annotations

import re

import pandas as pd

_PATTERNS = {
    "negation": re.compile(r"\b(not|no|never|nothing|hardly|barely)\b"),
    "contrast": re.compile(r"\b(but|however|although|though|yet|despite)\b"),
    "sarcasm": re.compile(r"\b(oh great|yeah right|so called|as if|brilliant idea)\b|\"[^\"]{1,25}\""),
}


def tag_review(clean_text: str, raw_text: str, rating: int) -> list[str]:
    """Linguistic cue tags for one review."""
    tags = [name for name, rx in _PATTERNS.items() if name != "sarcasm" and rx.search(clean_text)]
    if _PATTERNS["sarcasm"].search(raw_text.lower()):
        tags.append("sarcasm?")
    if rating in (4, 7):
        tags.append("mixed")
    return tags


def misclassified(df: pd.DataFrame, y_pred, scores) -> pd.DataFrame:
    """Errors sorted from most to least confident, with cue tags.

    The most confident mistakes are the most instructive: the model was sure
    and still wrong, so something systematic is going on.
    """
    errors = df.assign(pred=y_pred, score=scores)
    errors = errors[errors["label"] != errors["pred"]].copy()
    errors["confidence"] = errors["score"].abs()
    errors["tags"] = [
        tag_review(c, r, k) for c, r, k in zip(errors["clean"], errors["text"], errors["rating"])
    ]
    return errors.sort_values("confidence", ascending=False)


def tag_rates(df: pd.DataFrame, errors: pd.DataFrame) -> pd.DataFrame:
    """How often each cue appears among errors vs. the whole evaluation set.

    A cue that is much more frequent among errors is a likely cause of them.
    """
    all_tags = [
        tag_review(c, r, k) for c, r, k in zip(df["clean"], df["text"], df["rating"])
    ]
    names = ["negation", "contrast", "sarcasm?", "mixed"]
    return pd.DataFrame(
        {
            "tag": names,
            "pct_of_errors": [errors["tags"].apply(lambda t, n=n: n in t).mean() for n in names],
            "pct_of_all": [sum(n in t for t in all_tags) / len(all_tags) for n in names],
        }
    )


def top_features(pipeline, k: int = 20) -> pd.DataFrame:
    """Most positive and most negative n-grams of a linear model."""
    vocab = pipeline.named_steps["vectorizer"].get_feature_names_out()
    clf = pipeline.named_steps["classifier"]
    if hasattr(clf, "coef_"):
        weights = clf.coef_[0]
    else:  # MultinomialNB: log-probability ratio between classes
        weights = clf.feature_log_prob_[1] - clf.feature_log_prob_[0]
    order = weights.argsort()
    return pd.DataFrame(
        {
            "negative_ngram": vocab[order[:k]],
            "negative_weight": weights[order[:k]],
            "positive_ngram": vocab[order[::-1][:k]],
            "positive_weight": weights[order[::-1][:k]],
        }
    )
