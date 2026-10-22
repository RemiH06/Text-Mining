"""
evaluation.py
=============

Part 4 of the assignment: metrics, confusion matrices, and the optional
breakdowns by review length and by polarity strength (original star rating).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)

LABEL_NAMES = ["negative", "positive"]

LENGTH_BINS = [0, 100, 200, 400, 800, float("inf")]
LENGTH_LABELS = ["<100", "100-199", "200-399", "400-799", "800+"]


def compute_metrics(y_true, y_pred) -> dict[str, float]:
    """Accuracy plus binary precision, recall and F1 for the positive class."""
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary"
    )
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def plot_confusion_matrix(y_true, y_pred, title: str, path: Path | None = None, ax=None):
    """Heatmap of the confusion matrix; saved to ``path`` when given."""
    cm = confusion_matrix(y_true, y_pred)
    own_figure = ax is None
    if own_figure:
        fig, ax = plt.subplots(figsize=(4, 3.5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=False,
        xticklabels=LABEL_NAMES,
        yticklabels=LABEL_NAMES,
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)
    if own_figure:
        fig.tight_layout()
        if path is not None:
            fig.savefig(path, dpi=150)
        plt.close(fig)
    return ax


def accuracy_by_group(df: pd.DataFrame, y_pred, by: str) -> pd.DataFrame:
    """Accuracy and support for each value of column ``by``.

    ``df`` needs ``label`` and ``by`` columns, aligned with ``y_pred``.
    """
    scored = df.assign(correct=(df["label"].to_numpy() == y_pred))
    return (
        scored.groupby(by, observed=True)["correct"]
        .agg(accuracy="mean", n="size")
        .reset_index()
    )


def add_length_bucket(df: pd.DataFrame, tokens_col: str = "clean") -> pd.DataFrame:
    """Add ``n_tokens`` and a categorical ``length_bucket`` column."""
    n_tokens = df[tokens_col].str.split().str.len()
    return df.assign(
        n_tokens=n_tokens,
        length_bucket=pd.cut(n_tokens, LENGTH_BINS, labels=LENGTH_LABELS, right=False),
    )
