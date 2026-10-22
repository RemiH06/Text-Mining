"""
run_pipeline.py
===============

Runs the whole assignment end to end and writes every artifact to
``results/``:

1. Load IMDb and split train/dev/test                         (data.py)
2. Preprocess all reviews, cached to data/preprocessed.pkl     (preprocessing.py)
3. Train NB / LR / SVM for every n-gram config, score on dev  (features.py, models.py)
4. Refit each model's best config on train+dev, score on test (evaluation.py)
5. Error analysis of the best model on test                   (error_analysis.py)

Usage::

    python run_pipeline.py
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd

from data import DATA_DIR, load_imdb
from error_analysis import misclassified, tag_rates, top_features
from evaluation import (
    accuracy_by_group,
    add_length_bucket,
    compute_metrics,
    plot_confusion_matrix,
)
from features import NGRAM_CONFIGS
from models import build_pipeline, decision_scores, get_classifiers
from preprocessing import preprocess

RESULTS_DIR = Path(__file__).parent / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
CACHE_PATH = DATA_DIR / "preprocessed.pkl"


def load_preprocessed() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Splits with an extra ``clean`` column; tokenizing 50k reviews takes a while, so cache it."""
    if CACHE_PATH.exists():
        df = pd.read_pickle(CACHE_PATH)
    else:
        train, dev, test = load_imdb()
        df = pd.concat(
            [train.assign(split="train"), dev.assign(split="dev"), test.assign(split="test")],
            ignore_index=True,
        )
        print("Preprocessing 50,000 reviews...")
        df["clean"] = df["text"].map(preprocess)
        df.to_pickle(CACHE_PATH)
    return tuple(df[df["split"] == s].reset_index(drop=True) for s in ("train", "dev", "test"))


def compare_ngrams_on_dev(train: pd.DataFrame, dev: pd.DataFrame) -> pd.DataFrame:
    """Part 3: every classifier x every n-gram range, scored on dev."""
    rows = []
    for config_name, ngram_range in NGRAM_CONFIGS.items():
        for model_name, clf in get_classifiers().items():
            start = time.perf_counter()
            pipe = build_pipeline(clf, ngram_range).fit(train["clean"], train["label"])
            metrics = compute_metrics(dev["label"], pipe.predict(dev["clean"]))
            n_features = len(pipe.named_steps["vectorizer"].vocabulary_)
            elapsed = time.perf_counter() - start
            print(f"  {config_name:<11} {model_name:<20} acc={metrics['accuracy']:.4f} ({elapsed:.0f}s)")
            rows.append(
                {"ngrams": config_name, "model": model_name, "n_features": n_features,
                 **metrics, "fit_seconds": elapsed}
            )
    return pd.DataFrame(rows)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    train, dev, test = load_preprocessed()
    print(f"train={len(train)}  dev={len(dev)}  test={len(test)}")

    print("\nDev comparison (Part 3):")
    dev_results = compare_ngrams_on_dev(train, dev)
    dev_results.to_csv(RESULTS_DIR / "dev_ngram_comparison.csv", index=False)

    # Model selection uses dev only; test is touched once, below.
    best_configs = dev_results.loc[dev_results.groupby("model")["f1"].idxmax()]
    train_dev = pd.concat([train, dev], ignore_index=True)
    test = add_length_bucket(test)

    print("\nTest evaluation (Part 4):")
    test_rows, fitted = [], {}
    for _, row in best_configs.iterrows():
        clf = get_classifiers()[row["model"]]
        pipe = build_pipeline(clf, NGRAM_CONFIGS[row["ngrams"]])
        pipe.fit(train_dev["clean"], train_dev["label"])
        y_pred = pipe.predict(test["clean"])
        metrics = compute_metrics(test["label"], y_pred)
        print(f"  {row['model']:<20} ({row['ngrams']}) acc={metrics['accuracy']:.4f} f1={metrics['f1']:.4f}")
        test_rows.append({"model": row["model"], "ngrams": row["ngrams"], **metrics})
        fitted[row["model"]] = (pipe, y_pred)

        slug = row["model"].lower().replace(" ", "_")
        plot_confusion_matrix(
            test["label"], y_pred,
            title=f"{row['model']} ({row['ngrams']})",
            path=FIGURES_DIR / f"confusion_{slug}.png",
        )

    test_results = pd.DataFrame(test_rows).sort_values("f1", ascending=False)
    test_results.to_csv(RESULTS_DIR / "test_metrics.csv", index=False)

    # Optional part of Part 4 + Part 5, on the best model only.
    best_model = test_results.iloc[0]["model"]
    pipe, y_pred = fitted[best_model]
    print(f"\nError analysis on {best_model} (Part 5)")
    accuracy_by_group(test, y_pred, "length_bucket").to_csv(
        RESULTS_DIR / "accuracy_by_length.csv", index=False
    )
    if test["rating"].notna().any():  # the Hugging Face fallback has no ratings
        accuracy_by_group(test, y_pred, "rating").to_csv(
            RESULTS_DIR / "accuracy_by_rating.csv", index=False
        )
    errors = misclassified(test, y_pred, decision_scores(pipe, test["clean"]))
    errors[["id", "rating", "label", "pred", "confidence", "tags", "text"]].head(50).to_csv(
        RESULTS_DIR / "misclassified_examples.csv", index=False
    )
    tag_rates(test, errors).to_csv(RESULTS_DIR / "error_tag_rates.csv", index=False)
    top_features(pipe).to_csv(RESULTS_DIR / "top_features.csv", index=False)
    print(f"{len(errors)} errors out of {len(test)}. Artifacts written to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
