"""Etiquetado débil del dataset y muestra de revisión a ciegas.

    python -m stance.label

Una frase semilla manda sobre el bando del video, porque en un video provida también comenta
gente proelección. Las semillas se borran del texto para que el modelo no las use de atajo.
"""
import re

import pandas as pd
from langdetect import DetectorFactory, LangDetectException, detect

from .config import COMMENTS_CSV, DATA, DATASET_CSV, LABELS, MIXTO, SEED, SEEDS

MIN_WORDS = 5
MAX_PER_VIDEO = 150
SHARED = 50  # revisados por ambos, para medir el acuerdo
OWN = 75  # exclusivos de cada quien: 50 + 75 + 75 = 200

DetectorFactory.seed = SEED
_SEEDS = {side: re.compile("|".join(p), re.IGNORECASE) for side, p in SEEDS.items()}
_ALL_SEEDS = re.compile("|".join(_SEEDS[s].pattern for s in _SEEDS), re.IGNORECASE)
_URL = re.compile(r"https?://\S+")


def seed_side(text: str) -> str | None:
    """Bando de las semillas del comentario; None si no hay o si se contradicen."""
    sides = [side for side, pattern in _SEEDS.items() if pattern.search(text)]
    return sides[0] if len(sides) == 1 else None


def has_both_seeds(text: str) -> bool:
    return all(pattern.search(text) for pattern in _SEEDS.values())


def strip_seeds(text: str) -> str:
    return " ".join(_ALL_SEEDS.sub(" ", _URL.sub(" ", text)).split())


def is_spanish(text: str) -> bool:
    try:
        return detect(text) == "es"
    except LangDetectException:
        return False


def build_dataset(comments: pd.DataFrame) -> pd.DataFrame:
    df = comments.dropna(subset=["text"]).copy()
    df = df[~df["text"].map(has_both_seeds)]
    seeds = df["text"].map(seed_side)
    df["stance"] = seeds.fillna(df["side"])
    df["label_source"] = seeds.notna().map({True: "seed", False: "video"})
    df = df[df["stance"] != MIXTO]
    df["text_model"] = df["text"].map(strip_seeds)

    df = df[df["text_model"].str.split().str.len() >= MIN_WORDS]
    df = df.drop_duplicates(subset="text_model")
    df = df[df["text_model"].map(is_spanish)]

    # Primero las etiquetas por semilla, que son más confiables. El tope por video evita que el
    # modelo aprenda a reconocer unos cuantos videos en vez de la postura.
    shuffled = df.sample(frac=1, random_state=SEED)
    ranked = shuffled.sort_values("label_source", kind="stable")
    ranked = ranked.groupby("video_id").head(MAX_PER_VIDEO)
    n = ranked["stance"].value_counts().min()
    balanced = ranked.groupby("stance", group_keys=False).head(n)
    return balanced.assign(label=balanced["stance"].map(LABELS)).reset_index(drop=True)


def review_samples(dataset: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Muestras a ciegas: no incluyen la etiqueta débil para no sesgar a quien revisa."""
    per_side = (SHARED + 2 * OWN) // 2
    sample = dataset.groupby("stance", group_keys=False).sample(per_side, random_state=SEED)
    sample = sample.sample(frac=1, random_state=SEED)[["comment_id", "text"]].assign(postura="")
    shared = sample.iloc[:SHARED]
    return {
        "remi": pd.concat([shared, sample.iloc[SHARED:SHARED + OWN]]),
        "diego": pd.concat([shared, sample.iloc[SHARED + OWN:]]),
    }


def main():
    dataset = build_dataset(pd.read_csv(COMMENTS_CSV))
    dataset.to_csv(DATASET_CSV, index=False)
    for name, sample in review_samples(dataset).items():
        sample.to_csv(DATA / f"revision_{name}.csv", index=False, encoding="utf-8-sig")
    print(pd.crosstab(dataset["stance"], dataset["label_source"], margins=True).to_string())


if __name__ == "__main__":
    main()
