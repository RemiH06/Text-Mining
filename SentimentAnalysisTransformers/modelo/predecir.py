"""Clasifica la postura sobre el aborto de un texto en español.

    python predecir.py                  # modo interactivo: escribe un texto por línea, vacío para salir
    python predecir.py "texto a clasificar"

Usa el modelo de modelo_postura/, que se genera con entrenar.py.
"""
import sys
from pathlib import Path

from transformers import pipeline

from entrenar import MAX_LEN, clean_text

NOMBRES = {"vida": "provida", "aborto": "proaborto", "ninguno": "sin postura"}
clasificador = pipeline("text-classification", model=str(Path(__file__).parent / "modelo_postura"), top_k=None)


def clasificar(texto: str) -> str:
    scores = clasificador([clean_text(texto)], truncation=True, max_length=MAX_LEN)[0]
    scores = sorted(scores, key=lambda s: -s["score"])
    detalle = ", ".join(f"{NOMBRES[s['label']]} {s['score']:.0%}" for s in scores)
    return f"{NOMBRES[scores[0]['label']].upper()}  ({detalle})"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(clasificar(" ".join(sys.argv[1:])))
    else:
        while texto := input("\ntexto> ").strip():
            print(clasificar(texto))
