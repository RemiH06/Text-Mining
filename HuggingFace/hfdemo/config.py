"""Configuración común a los notebooks: rutas, semilla, dispositivo y silencio de logs."""
import warnings
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
SEED = 42


def setup(seed: int = SEED) -> torch.device:
    """Silencia avisos y barras de progreso, fija la semilla y devuelve el mejor dispositivo."""
    warnings.filterwarnings("ignore")
    from transformers import set_seed
    from transformers.utils import logging as hf_logging
    import datasets

    hf_logging.set_verbosity_error()
    hf_logging.disable_progress_bar()
    datasets.disable_progress_bars()
    set_seed(seed)
    OUT.mkdir(exist_ok=True)

    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")
