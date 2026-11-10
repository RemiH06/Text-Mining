"""Etiquetado manual: lote por etiquetar y CSV final para el notebook de Proyecto3.

    python -m stance.manual lote   # data/por_etiquetar.csv: pendientes de las revisiones + comentarios nuevos
    python -m stance.manual unir   # data/comentarios_aborto.csv (comment_id, text, postura)

Etiquetas válidas: vida, aborto, ninguno. Para ir rápido se aceptan v, a y n.
Si se edita en Excel, guardar como "CSV UTF-8".
"""
import argparse
import sys

import pandas as pd

from .config import COMMENTS_CSV, DATA, PRO_ELECCION, SEED
from .label import MIN_WORDS, is_spanish, seed_side

REVISIONS = [DATA / "revision_diego.csv", DATA / "revision_remi.csv"]
LOTE_CSV = DATA / "por_etiquetar.csv"
FINAL_CSV = DATA / "comentarios_aborto.csv"
TARGET = 1000
MAX_WORDS = 150  # los muy largos hacen lento el etiquetado
MAX_PER_VIDEO = 60  # variedad: que ningún video domine el lote
VALID = {"vida", "aborto", "ninguno"}
SHORTCUTS = {"v": "vida", "a": "aborto", "n": "ninguno", "ninguna": "ninguno"}
COLS = ["comment_id", "text", "postura"]


def read_csv(path) -> pd.DataFrame:
    """Lee un CSV aunque Excel lo haya guardado en otra codificación o con punto y coma."""
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return pd.read_csv(path, sep=None, engine="python", encoding=encoding, dtype=str)
        except UnicodeDecodeError:
            continue
    raise SystemExit(f"No pude leer {path}")


def read_labeled(paths) -> pd.DataFrame:
    """Une los archivos; si un comentario aparece varias veces, gana la versión etiquetada."""
    df = pd.concat([read_csv(p)[COLS] for p in paths if p.exists()], ignore_index=True)
    postura = df["postura"].fillna("").str.strip().str.lower()
    df["postura"] = postura.replace(SHORTCUTS).replace("", pd.NA)
    df = df.sort_values("postura", na_position="last", kind="stable")
    return df.drop_duplicates("comment_id").reset_index(drop=True)


def make_lote():
    if LOTE_CSV.exists():
        raise SystemExit(f"{LOTE_CSV.name} ya existe; no lo sobrescribo para no borrar etiquetas.")
    revised = read_labeled(REVISIONS)
    pending = revised[revised["postura"].isna()]

    raw = pd.read_csv(COMMENTS_CSV).dropna(subset=["text"]).drop_duplicates("text")
    words = raw["text"].str.split().str.len()
    raw = raw[words.between(MIN_WORDS, MAX_WORDS) & ~raw["comment_id"].isin(revised["comment_id"])]
    raw = raw[raw["text"].map(is_spanish)]

    # Los proelección son escasos (12% de la primera muestra): entran primero los que tienen
    # una frase semilla de ese bando, que acierta 87%.
    seeds = raw["text"].map(seed_side)
    priority = raw[seeds == PRO_ELECCION]
    rest = raw[seeds != PRO_ELECCION].sample(frac=1, random_state=SEED)
    rest = rest.groupby("video_id").head(MAX_PER_VIDEO)
    new = pd.concat([priority, rest]).head(TARGET - len(revised))

    lote = pd.concat([pending[COLS], new[["comment_id", "text"]].assign(postura="")])
    lote = lote.sample(frac=1, random_state=SEED)  # mezclado, para no etiquetar en bloques
    lote.to_csv(LOTE_CSV, index=False, encoding="utf-8-sig")
    print(f"{LOTE_CSV.name}: {len(lote)} por etiquetar ({len(pending)} pendientes de las "
          f"revisiones, {len(new)} nuevos, {len(priority)} con semilla proelección)")


def unite():
    df = read_labeled(REVISIONS + [LOTE_CSV])
    invalid = df[df["postura"].notna() & ~df["postura"].isin(VALID)]
    if len(invalid):
        print("Etiquetas inválidas; corrígelas y vuelve a correr:")
        print(invalid[["comment_id", "postura"]].to_string(index=False))
        sys.exit(1)
    # Sin BOM: el notebook lee con pd.read_csv por defecto.
    df[COLS].to_csv(FINAL_CSV, index=False, encoding="utf-8")
    print(f"{FINAL_CSV.name}: {len(df)} comentarios, {df['postura'].notna().sum()} etiquetados")
    print(df["postura"].value_counts(dropna=False).to_string())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=["lote", "unir"])
    {"lote": make_lote, "unir": unite}[parser.parse_args().step]()


if __name__ == "__main__":
    main()
