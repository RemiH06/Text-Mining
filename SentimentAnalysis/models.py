"""
models.py
=========

Part 3 of the assignment: the three classifiers, each wrapped in a sklearn
``Pipeline`` together with its vectorizer, so fitting on raw (preprocessed)
text and predicting on new text is a single call and the vocabulary is
always learned from the training split only.

- Multinomial Naive Bayes: the classic baseline for word counts.
- Logistic Regression: discriminative, gives calibrated-ish probabilities.
- Linear SVM: usually the strongest of the three on sparse n-grams.
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from features import build_vectorizer

RANDOM_STATE = 42


def get_classifiers() -> dict:
    """Fresh, unfitted classifiers keyed by display name."""
    return {
        "Naive Bayes": MultinomialNB(alpha=1.0),
        # Raw counts are unscaled, so both solvers need more iterations than
        # the default to converge on the larger n-gram vocabularies.
        "Logistic Regression": LogisticRegression(max_iter=5000, random_state=RANDOM_STATE),
        "Linear SVM": LinearSVC(C=0.1, max_iter=10000, random_state=RANDOM_STATE),
    }


def build_pipeline(classifier, ngram_range: tuple[int, int], **vectorizer_kwargs) -> Pipeline:
    return Pipeline(
        [
            ("vectorizer", build_vectorizer(ngram_range, **vectorizer_kwargs)),
            ("classifier", classifier),
        ]
    )


def decision_scores(pipeline: Pipeline, texts) -> np.ndarray:
    """Signed confidence for the positive class, comparable within one model.

    LinearSVC has no predict_proba, so we use decision_function for every
    model that has it and fall back to log-odds for Naive Bayes.
    """
    if hasattr(pipeline, "decision_function"):
        return pipeline.decision_function(texts)
    log_proba = pipeline.predict_log_proba(texts)
    return log_proba[:, 1] - log_proba[:, 0]
