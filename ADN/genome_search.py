"""
genome_search.py
=================

Extra addition (not part of the original assignment PDF): checks whether
each of the 20 DNA sequences supplied in `sequences.py` (10 pairs x
seq1/seq2) actually occurs in a *real* human genome reference, using our
own `smith_waterman()` from `alignment.py` as the search engine.

Reference used: the revised Cambridge Reference Sequence for the human
mitochondrial genome (NCBI accession NC_012920.1, ~16,569 bp). This is the
same reference the assignment PDF itself points to ("Use the Homo sapiens
mitochondrial DNA sequences..."). The full human *nuclear* genome
(~3.1 Gbp) is not a realistic fit for a from-scratch O(nm) aligner or for
this exercise, so mtDNA is used as the practical "human genome" reference.

For each of the 20 sequences we run local alignment (Smith-Waterman)
against both strands of the reference (the sequence itself and its
reverse complement) and flag it as a genuine match only if the alignment
covers most of the query length at close to the maximum possible score
(a perfect match). This matters because several of the assignment's pairs
are short low-complexity repeats (e.g. `AGCT` x N), which can produce a
misleadingly "decent" raw alignment score almost anywhere by chance -- the
coverage + pct-of-max-score thresholds are a simple, from-scratch stand-in
for the statistical significance (E-value) that a real tool like BLAST
would compute.
"""

from __future__ import annotations

import csv
import time
import urllib.request
from pathlib import Path

from alignment import smith_waterman
from sequences import DNA_PAIRS

DATA_DIR = Path(__file__).parent / "data"
RESULTS_DIR = Path(__file__).parent / "results"

MTDNA_ACCESSION = "NC_012920.1"  # Homo sapiens mitochondrion, complete genome (rCRS)
MTDNA_PATH = DATA_DIR / "human_mtDNA_NC_012920.1.fasta"
EFETCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    f"?db=nuccore&id={MTDNA_ACCESSION}&rettype=fasta&retmode=text"
)

# A hit is only reported as a genuine match if it reaches this fraction of
# the query's theoretical maximum score (a perfect match) *and* covers at
# least this fraction of the query length.
MATCH_SCORE_THRESHOLD = 0.90
COVERAGE_THRESHOLD = 0.90

_COMPLEMENT = str.maketrans("ACGT", "TGCA")


def reverse_complement(seq: str) -> str:
    return seq.translate(_COMPLEMENT)[::-1]


def fetch_human_mtdna(force: bool = False) -> str:
    """Download (and cache locally) the human mitochondrial reference genome."""
    DATA_DIR.mkdir(exist_ok=True)
    if MTDNA_PATH.exists() and not force:
        raw = MTDNA_PATH.read_text()
    else:
        with urllib.request.urlopen(EFETCH_URL, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
        MTDNA_PATH.write_text(raw)
    lines = raw.splitlines()
    seq = "".join(line.strip() for line in lines if not line.startswith(">"))
    return seq.upper()


def search_sequence_in_genome(
    query: str, genome: str, match: int = 2, mismatch: int = -1, gap: int = -2
) -> dict:
    """Local-align `query` against `genome` on both strands; return the
    best-scoring hit plus coverage/identity stats needed for a verdict."""
    max_possible_score = match * len(query)
    best = None
    for strand, q in (("forward", query), ("reverse_complement", reverse_complement(query))):
        result = smith_waterman(q, genome, match, mismatch, gap)
        record = {
            "strand": strand,
            "score": result.score,
            "pct_of_max_score": result.score / max_possible_score,
            "identity": result.identity(),
            "aligned_len": len(result.aligned_seq1),
            "coverage": len(result.aligned_seq1) / len(query),
            "genome_start": result.start[1],
            "genome_end": result.end[1],
        }
        if best is None or record["score"] > best["score"]:
            best = record
    return best


def run_search(match: int = 2, mismatch: int = -1, gap: int = -2) -> list[dict]:
    genome = fetch_human_mtdna()
    rows = []
    for pair in DNA_PAIRS:
        for which in ("seq1", "seq2"):
            query = pair[which]
            t0 = time.perf_counter()
            hit = search_sequence_in_genome(query, genome, match, mismatch, gap)
            elapsed = time.perf_counter() - t0
            is_match = (
                hit["pct_of_max_score"] >= MATCH_SCORE_THRESHOLD
                and hit["coverage"] >= COVERAGE_THRESHOLD
            )
            rows.append(
                {
                    "pair_id": pair["id"],
                    "sequence": which,
                    "query_len": len(query),
                    **hit,
                    "found_in_mtDNA": is_match,
                    "search_time_s": round(elapsed, 3),
                }
            )
    return rows


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    print(f"Fetching/loading human mitochondrial genome ({MTDNA_ACCESSION})...")
    genome = fetch_human_mtdna()
    print(f"Reference length: {len(genome)} bp\n")

    print(
        "Searching all 20 sequences (10 pairs x seq1/seq2) against it with "
        "Smith-Waterman (forward + reverse-complement strand)..."
    )
    rows = run_search()

    out_path = RESULTS_DIR / "human_genome_search.csv"
    fieldnames = [
        "pair_id", "sequence", "query_len", "strand", "score",
        "pct_of_max_score", "identity", "aligned_len", "coverage",
        "genome_start", "genome_end", "found_in_mtDNA", "search_time_s",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in fieldnames})
    print(f"\nWrote {out_path}")

    n_found = sum(r["found_in_mtDNA"] for r in rows)
    print(
        f"{n_found} / {len(rows)} sequences look like genuine matches in human mtDNA "
        f"(>= {MATCH_SCORE_THRESHOLD:.0%} of max score, >= {COVERAGE_THRESHOLD:.0%} coverage).\n"
    )
    for row in rows:
        verdict = "MATCH" if row["found_in_mtDNA"] else "no match"
        print(
            f"  Pair {row['pair_id']:>2} {row['sequence']}: best={row['strand']:<19} "
            f"score={row['score']:>4} ({row['pct_of_max_score']:.1%} of max) "
            f"identity={row['identity']:.1%} coverage={row['coverage']:.1%}  -> {verdict}"
        )


if __name__ == "__main__":
    main()
