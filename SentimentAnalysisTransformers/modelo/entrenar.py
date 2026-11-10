"""Entrena RoBERTuito con todos los comentarios etiquetados y lo guarda para usarlo con predecir.py.

    python entrenar.py comentarios_aborto.csv modelo_postura

Mismos hiperparámetros y limpieza que la Parte 3 del notebook de Proyecto3. Su desempeño esperado es
el de la validación cruzada del notebook (F1 macro 0.635); este modelo final no tiene evaluación propia
porque se entrena con los 1,000 comentarios.
"""
import math
import re
import sys

import numpy as np
import pandas as pd
import torch
from torch import nn
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

MODELO = "pysentimiento/robertuito-base-uncased"
LABELS = ["aborto", "vida", "ninguno"]  # mismo orden que el notebook
MAX_LEN, EPOCHS, LR, BATCH, SEED = 128, 8, 3e-5, 8, 42
URL_RE = re.compile(r"https?://\S+|www\.\S+")


def clean_text(t: str) -> str:
    """La misma limpieza que el notebook: sin URLs, menciones ni espacios repetidos."""
    t = URL_RE.sub(" ", str(t))
    t = re.sub(r"@\w+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def main(csv: str, out: str):
    torch.manual_seed(SEED)
    rng = np.random.default_rng(SEED)
    dev = "cuda" if torch.cuda.is_available() else "cpu"

    df = pd.read_csv(csv).dropna(subset=["postura"])
    texts = df["text"].map(clean_text).tolist()
    y = torch.tensor(df["postura"].map(LABELS.index).to_numpy())
    print(f"{len(y)} comentarios en {dev}:", dict(zip(LABELS, torch.bincount(y, minlength=3).tolist())))

    tok = AutoTokenizer.from_pretrained(MODELO)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODELO, num_labels=3, id2label=dict(enumerate(LABELS)), label2id={l: i for i, l in enumerate(LABELS)}
    ).to(dev)

    # Pérdida ponderada inversamente a la frecuencia de cada clase, como en el notebook.
    counts = torch.bincount(y, minlength=3).float()
    loss_fn = nn.CrossEntropyLoss(weight=(len(y) / (3 * counts)).to(dev))
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    batches = math.ceil(len(y) / BATCH)
    sched = get_linear_schedule_with_warmup(opt, int(0.1 * EPOCHS * batches), EPOCHS * batches)

    for epoch in range(EPOCHS):
        model.train()
        perm, total = rng.permutation(len(y)), 0.0
        for i in range(0, len(perm), BATCH):
            b = perm[i:i + BATCH]
            enc = tok([texts[j] for j in b], truncation=True, max_length=MAX_LEN,
                      padding=True, return_tensors="pt").to(dev)
            loss = loss_fn(model(**enc).logits, y[b].to(dev))
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            total += loss.item()
        print(f"época {epoch + 1}/{EPOCHS}: pérdida {total / batches:.3f}")

    model.save_pretrained(out)
    tok.save_pretrained(out)
    print("guardado en", out)


if __name__ == "__main__":
    main(*sys.argv[1:3])
