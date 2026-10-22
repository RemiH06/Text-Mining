"""
data.py
=======

Downloads and loads the IMDb Large Movie Review Dataset (Maas et al., 2011).

The archive comes from Stanford and is extracted into ``data/aclImdb/``.
Each review is a plain-text file under ``{train,test}/{pos,neg}/``; the file
name ``<id>_<rating>.txt`` also carries the original 1-10 star rating, which
we keep because it lets us analyse performance by polarity strength (Part 4).

If Stanford's server does not answer, we fall back to the Hugging Face copy
(``stanfordnlp/imdb``): same reviews and labels, but without the star
rating, so ``rating`` is NaN and the polarity-strength analysis is skipped.

The official split is 25k train / 25k test. The assignment also asks for a
dev set, so we carve one out of the training reviews (stratified, fixed
seed) and leave the test set untouched until the final evaluation.
"""

from __future__ import annotations

import shutil
import tarfile
import urllib.request
from pathlib import Path
from urllib.error import URLError

import pandas as pd
from sklearn.model_selection import train_test_split

DATA_DIR = Path(__file__).parent / "data"
DATASET_URL = "https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"
ARCHIVE_PATH = DATA_DIR / "aclImdb_v1.tar.gz"
EXTRACTED_DIR = DATA_DIR / "aclImdb"

HF_URL = "https://huggingface.co/datasets/stanfordnlp/imdb/resolve/main/plain_text/{split}-00000-of-00001.parquet"
HF_DIR = DATA_DIR / "hf"

TIMEOUT_SECONDS = 15
RANDOM_STATE = 42


def _download(url: str, path: Path) -> None:
    """Stream ``url`` to ``path``; the .part file avoids caching half a download."""
    partial = path.with_name(path.name + ".part")
    with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response, open(partial, "wb") as out:
        shutil.copyfileobj(response, out)
    partial.replace(path)


def download_imdb(force: bool = False) -> Path:
    """Download and extract the dataset once; later calls reuse the cache."""
    if EXTRACTED_DIR.exists() and not force:
        return EXTRACTED_DIR

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE_PATH.exists() or force:
        print(f"Downloading {DATASET_URL} (~84 MB)...")
        _download(DATASET_URL, ARCHIVE_PATH)

    print(f"Extracting into {DATA_DIR}...")
    with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
        # The "data" filter rejects absolute paths and "../" entries.
        tar.extractall(DATA_DIR, filter="data")
    return EXTRACTED_DIR


def _load_split(split: str) -> pd.DataFrame:
    """Read every review of one official split into a DataFrame."""
    rows = []
    for label_name, label in (("pos", 1), ("neg", 0)):
        for path in (EXTRACTED_DIR / split / label_name).glob("*.txt"):
            review_id, rating = path.stem.split("_")
            rows.append(
                {
                    "id": f"{split}_{label_name}_{review_id}",
                    "text": path.read_text(encoding="utf-8"),
                    "label": label,
                    "rating": int(rating),
                }
            )
    return pd.DataFrame(rows)


def _load_hf_split(split: str) -> pd.DataFrame:
    """Same columns as _load_split, read from the Hugging Face parquet."""
    path = HF_DIR / f"{split}.parquet"
    if not path.exists():
        HF_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Downloading Hugging Face {split} split...")
        _download(HF_URL.format(split=split), path)
    df = pd.read_parquet(path)
    return df.assign(id=[f"{split}_{i}" for i in range(len(df))], rating=float("nan"))[
        ["id", "text", "label", "rating"]
    ]


def load_imdb(dev_size: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (train, dev, test) DataFrames with columns id, text, label, rating.

    label is 1 for positive and 0 for negative.
    """
    try:
        download_imdb()
        full_train, test = _load_split("train"), _load_split("test")
    except (URLError, TimeoutError) as err:
        print(f"Stanford unreachable ({err}); using the Hugging Face copy without ratings.")
        full_train, test = _load_hf_split("train"), _load_hf_split("test")
    train, dev = train_test_split(
        full_train,
        test_size=dev_size,
        stratify=full_train["label"],
        random_state=RANDOM_STATE,
    )
    return train.reset_index(drop=True), dev.reset_index(drop=True), test


if __name__ == "__main__":
    train, dev, test = load_imdb()
    for name, df in (("train", train), ("dev", dev), ("test", test)):
        print(f"{name:>5}: {len(df):>6} reviews, {df['label'].mean():.0%} positive")
