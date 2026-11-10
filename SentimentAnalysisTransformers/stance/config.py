"""Rutas, consultas y frases semilla del dataset."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
VIDEOS_CSV = DATA / "videos.csv"
COMMENTS_CSV = DATA / "comments_raw.csv"
DATASET_CSV = DATA / "dataset.csv"
SEED = 42

PRO_ELECCION = "pro_eleccion"
PRO_VIDA = "pro_vida"
MIXTO = "mixto"  # noticieros y debates: solo cuentan los comentarios con frase semilla
LABELS = {PRO_VIDA: 0, PRO_ELECCION: 1}

# Cuota de la API: search.list cuesta 100 unidades y commentThreads.list 1, de 10,000 al día.
MAX_VIDEOS_PER_QUERY = 15
MAX_PAGES_PER_VIDEO = 5

QUERIES = {
    PRO_ELECCION: [
        "marea verde aborto legal México",
        "derecho a decidir aborto",
        "a favor de la despenalización del aborto",
        "marcha 28 septiembre aborto legal",
    ],
    PRO_VIDA: [
        "marcha por la vida aborto México",
        "argumentos provida contra el aborto",
        "testimonio provida aborto",
        "defender la vida no al aborto",
    ],
}

# Solo afirmaciones de postura en primera persona o consignas. Las menciones no sirven porque
# ambos bandos las escriben: "los provida son hipócritas", "los que están a favor del aborto",
# "Católicas por el derecho a decidir, qué burla". Los acentos van como clases porque se busca
# sobre el texto original, que debe conservarlos para el Transformer.
SEEDS = {
    PRO_ELECCION: [
        r"aborto legal,? (ya|seguro|libre|gratuito)",
        r"aborto libre",
        r"mi cuerpo,? mi decisi[oó]n",
        r"ser[aá] ley",
        r"s[ií] al aborto",
        r"(?<!no )(estoy|estamos) a favor del aborto",
        r"no (estoy|estamos) en contra del aborto",
        r"(soy|somos) pro[ -]?(aborto|elecci[oó]n)",
    ],
    PRO_VIDA: [
        r"no al aborto",
        r"s[ií] a la vida",
        r"(soy|somos) pro[ -]?vida",
        r"salvemos las dos vidas",
        r"(estoy|estamos) a favor de la vida",
        r"(?<!no )(estoy|estamos) en contra del aborto",
        r"no (estoy|estamos) a favor del aborto",
        r"(el )?aborto es (un )?(asesinato|crimen|homicidio)",
        r"abortar es (matar|asesinar)",
    ],
}
