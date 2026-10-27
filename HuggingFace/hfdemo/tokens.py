"""Entrenamiento de tokenizers de juguete y tablas de comparación para la Parte 2."""
import pandas as pd
from tokenizers import Tokenizer, models, normalizers, pre_tokenizers, trainers

ESPECIALES = ["[UNK]", "[PAD]", "[CLS]", "[SEP]", "[MASK]"]


def entrenar_tokenizer(algoritmo: str, textos, vocab_size: int = 2000) -> Tokenizer:
    """Entrena BPE, WordPiece o Unigram (el algoritmo de SentencePiece) sobre `textos`."""
    if algoritmo == "BPE":
        tk = Tokenizer(models.BPE(unk_token="[UNK]"))
        trainer = trainers.BpeTrainer(vocab_size=vocab_size, special_tokens=ESPECIALES)
        tk.pre_tokenizer = pre_tokenizers.Whitespace()
    elif algoritmo == "WordPiece":
        tk = Tokenizer(models.WordPiece(unk_token="[UNK]"))
        trainer = trainers.WordPieceTrainer(vocab_size=vocab_size, special_tokens=ESPECIALES)
        tk.pre_tokenizer = pre_tokenizers.Whitespace()
    elif algoritmo == "Unigram":
        tk = Tokenizer(models.Unigram())
        trainer = trainers.UnigramTrainer(vocab_size=vocab_size, special_tokens=ESPECIALES, unk_token="[UNK]")
        tk.pre_tokenizer = pre_tokenizers.Metaspace()  # espacios como "▁", igual que SentencePiece
    else:
        raise ValueError(f"Algoritmo desconocido: {algoritmo}")
    tk.normalizer = normalizers.Lowercase()
    tk.train_from_iterator(textos, trainer)
    return tk


def tabla_tokens(tokenizadores: dict, texto: str) -> pd.DataFrame:
    """Una fila por tokenizer con sus tokens y cuántos son. Acepta `Tokenizer` o `AutoTokenizer`."""
    filas = []
    for nombre, tk in tokenizadores.items():
        toks = tk.encode(texto).tokens if isinstance(tk, Tokenizer) else tk.tokenize(texto)
        filas.append({"tokenizer": nombre, "n": len(toks), "tokens": " | ".join(toks)})
    return pd.DataFrame(filas).set_index("tokenizer")
