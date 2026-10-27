# Hugging Face Transformers: ecosistema y tokenización

Tarea 3 (equipo 3): presentación de las Partes 1 y 2 de la librería de Hugging Face.
Enunciado: `Hw-3 - HuggingFace.pdf`.

## Estructura

```
HuggingFace/
├── notebooks/
│   ├── 01_ecosistema.ipynb     # Parte 1: librerías, instalación CPU/GPU, pipelines, anatomía de un modelo
│   └── 02_tokenizacion.ipynb   # Parte 2: WordPiece/BPE/SentencePiece, AutoTokenizer, padding, map()
├── hfdemo/
│   ├── config.py               # Rutas, semilla, dispositivo y silencio de logs
│   ├── tokens.py               # Entrenar tokenizers de juguete y tablas de comparación
│   └── plots.py                # Plantilla de Plotly y gráficas
├── requirements.txt
└── outputs/                    # Modelo guardado por el notebook 01 (ignorado por git)
```

## Instalación

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; en Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m ipykernel install --user --name hf-mdt --display-name "Python (HuggingFace MdT)"
```

Todo corre en CPU. La primera ejecución descarga unos 1.2 GB de modelos a la caché de Hugging Face (`~/.cache/huggingface`); después funciona sin internet con `HF_HUB_OFFLINE=1`.

## Uso

Abrir los notebooks en VS Code o JupyterLab con el kernel `Python (HuggingFace MdT)` y ejecutar de arriba abajo. Cada uno tarda menos de 2 minutos en una laptop sin GPU, contando las descargas ya en caché.

Las gráficas son de Plotly: se ven en VS Code y JupyterLab, pero no en la vista previa de GitHub.

Versiones con las que se ejecutaron: transformers 5.20, datasets 5.1, tokenizers 0.23, torch 2.14 (CPU). Transformers 5 quitó varios pipelines (`question-answering`, `summarization`, `translation`), así que muchos tutoriales viejos fallan con esta versión.
