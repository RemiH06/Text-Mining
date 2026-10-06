"""
alignment.py
============

From-scratch implementations of two classic dynamic-programming sequence
alignment algorithms:

- Needleman-Wunsch (global alignment)
- Smith-Waterman   (local alignment)

Both build an (n+1) x (m+1) score matrix plus a traceback matrix, and both
support the default DNA scoring scheme required by the assignment:

    match    = +2
    mismatch = -1
    gap      = -2

Running this file directly (``python alignment.py``) aligns all 10 DNA pairs
from ``sequences.py`` with both algorithms and default scoring, prints a
summary, and writes every artifact (scores, aligned sequences, heatmap
figures, a parameter-sensitivity study, and an optional Biopython
comparison) into ``results/``.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from sequences import DNA_PAIRS

RESULTS_DIR = Path(__file__).parent / "results"
FIGURES_DIR = RESULTS_DIR / "figures"

# Traceback move codes.
DIAG, UP, LEFT, STOP = "D", "U", "L", "0"


@dataclass
class AlignmentResult:
    algorithm: str
    score: int
    aligned_seq1: str
    aligned_seq2: str
    score_matrix: np.ndarray
    traceback_matrix: np.ndarray
    path: list = field(default_factory=list)
    start: tuple = (0, 0)
    end: tuple = (0, 0)

    def match_line(self) -> str:
        return format_match_line(self.aligned_seq1, self.aligned_seq2)

    def identity(self) -> float:
        """Fraction of aligned columns (excluding gaps) that are identical."""
        matches = sum(
            1
            for a, b in zip(self.aligned_seq1, self.aligned_seq2)
            if a == b and a != "-"
        )
        aligned_cols = sum(
            1 for a, b in zip(self.aligned_seq1, self.aligned_seq2) if a != "-" and b != "-"
        )
        return matches / aligned_cols if aligned_cols else 0.0

    def pretty(self, width: int = 60) -> str:
        """Render the alignment in wrapped blocks, biopython-pairwise2 style."""
        lines = []
        a, m, b = self.aligned_seq1, self.match_line(), self.aligned_seq2
        for i in range(0, len(a), width):
            lines.append(a[i : i + width])
            lines.append(m[i : i + width])
            lines.append(b[i : i + width])
            lines.append("")
        return "\n".join(lines).rstrip()


def format_match_line(aligned_seq1: str, aligned_seq2: str) -> str:
    """'|' for a match, '.' for a mismatch, ' ' wherever either side is a gap."""
    chars = []
    for a, b in zip(aligned_seq1, aligned_seq2):
        if a == "-" or b == "-":
            chars.append(" ")
        elif a == b:
            chars.append("|")
        else:
            chars.append(".")
    return "".join(chars)


def _substitution_score(a: str, b: str, match: int, mismatch: int) -> int:
    return match if a == b else mismatch


def needleman_wunsch(
    seq1: str, seq2: str, match: int = 2, mismatch: int = -1, gap: int = -2
) -> AlignmentResult:
    """Global alignment (Needleman-Wunsch) built from scratch with numpy."""
    n, m = len(seq1), len(seq2)
    score = np.zeros((n + 1, m + 1), dtype=int)
    trace = np.full((n + 1, m + 1), "", dtype=object)

    for i in range(1, n + 1):
        score[i, 0] = score[i - 1, 0] + gap
        trace[i, 0] = UP
    for j in range(1, m + 1):
        score[0, j] = score[0, j - 1] + gap
        trace[0, j] = LEFT

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diag = score[i - 1, j - 1] + _substitution_score(seq1[i - 1], seq2[j - 1], match, mismatch)
            up = score[i - 1, j] + gap
            left = score[i, j - 1] + gap
            best = max(diag, up, left)
            score[i, j] = best
            # Preference order diag > up > left keeps traceback deterministic on ties.
            if best == diag:
                trace[i, j] = DIAG
            elif best == up:
                trace[i, j] = UP
            else:
                trace[i, j] = LEFT

    aligned1, aligned2, path = [], [], []
    i, j = n, m
    path.append((i, j))
    while i > 0 or j > 0:
        move = trace[i, j]
        if move == DIAG:
            aligned1.append(seq1[i - 1])
            aligned2.append(seq2[j - 1])
            i, j = i - 1, j - 1
        elif move == UP:
            aligned1.append(seq1[i - 1])
            aligned2.append("-")
            i -= 1
        else:  # LEFT
            aligned1.append("-")
            aligned2.append(seq2[j - 1])
            j -= 1
        path.append((i, j))
    aligned1.reverse()
    aligned2.reverse()
    path.reverse()

    return AlignmentResult(
        algorithm="Needleman-Wunsch",
        score=int(score[n, m]),
        aligned_seq1="".join(aligned1),
        aligned_seq2="".join(aligned2),
        score_matrix=score,
        traceback_matrix=trace,
        path=path,
        start=(0, 0),
        end=(n, m),
    )


def smith_waterman(
    seq1: str, seq2: str, match: int = 2, mismatch: int = -1, gap: int = -2
) -> AlignmentResult:
    """Local alignment (Smith-Waterman) built from scratch with numpy."""
    n, m = len(seq1), len(seq2)
    score = np.zeros((n + 1, m + 1), dtype=int)
    trace = np.full((n + 1, m + 1), STOP, dtype=object)

    best_score = 0
    best_pos = (0, 0)

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diag = score[i - 1, j - 1] + _substitution_score(seq1[i - 1], seq2[j - 1], match, mismatch)
            up = score[i - 1, j] + gap
            left = score[i, j - 1] + gap
            best = max(0, diag, up, left)
            score[i, j] = best
            if best == 0:
                trace[i, j] = STOP
            elif best == diag:
                trace[i, j] = DIAG
            elif best == up:
                trace[i, j] = UP
            else:
                trace[i, j] = LEFT
            if best > best_score:
                best_score = best
                best_pos = (i, j)

    aligned1, aligned2, path = [], [], []
    i, j = best_pos
    end_pos = (i, j)
    path.append((i, j))
    while i > 0 and j > 0 and trace[i, j] != STOP:
        move = trace[i, j]
        if move == DIAG:
            aligned1.append(seq1[i - 1])
            aligned2.append(seq2[j - 1])
            i, j = i - 1, j - 1
        elif move == UP:
            aligned1.append(seq1[i - 1])
            aligned2.append("-")
            i -= 1
        else:  # LEFT
            aligned1.append("-")
            aligned2.append(seq2[j - 1])
            j -= 1
        path.append((i, j))
    start_pos = (i, j)
    aligned1.reverse()
    aligned2.reverse()
    path.reverse()

    return AlignmentResult(
        algorithm="Smith-Waterman",
        score=int(best_score),
        aligned_seq1="".join(aligned1),
        aligned_seq2="".join(aligned2),
        score_matrix=score,
        traceback_matrix=trace,
        path=path,
        start=start_pos,
        end=end_pos,
    )


# ----------------------------------------------------------------------------
# Visualization
# ----------------------------------------------------------------------------

def plot_alignment_matrix(
    result: AlignmentResult,
    seq1: str,
    seq2: str,
    title: str | None = None,
    ax=None,
    max_ticks: int = 60,
):
    """Heatmap of the DP score matrix with the traceback path overlaid."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    created_fig = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 7))
        created_fig = True

    sns.heatmap(
        result.score_matrix,
        ax=ax,
        cmap="viridis",
        cbar_kws={"label": "score"},
    )

    ys = [p[0] + 0.5 for p in result.path]
    xs = [p[1] + 0.5 for p in result.path]
    ax.plot(xs, ys, color="red", linewidth=2, marker="o", markersize=2, label="traceback path")

    ax.set_xlabel(f"Sequence 2 (len={len(seq2)})")
    ax.set_ylabel(f"Sequence 1 (len={len(seq1)})")
    step_x = max(1, len(seq2) // max_ticks)
    step_y = max(1, len(seq1) // max_ticks)
    ax.set_xticks([j + 0.5 for j in range(0, len(seq2) + 1, step_x)])
    ax.set_xticklabels([("-" + seq2)[j] for j in range(0, len(seq2) + 1, step_x)], rotation=90)
    ax.set_yticks([i + 0.5 for i in range(0, len(seq1) + 1, step_y)])
    ax.set_yticklabels([("-" + seq1)[i] for i in range(0, len(seq1) + 1, step_y)], rotation=0)
    ax.set_title(title or f"{result.algorithm} score matrix (score={result.score})")
    ax.legend(loc="upper right")

    if created_fig:
        fig.tight_layout()
        return fig
    return ax.figure


# ----------------------------------------------------------------------------
# Batch runner used for the `results/` deliverable
# ----------------------------------------------------------------------------

def run_all_pairs(match: int = 2, mismatch: int = -1, gap: int = -2) -> list[dict]:
    """Run both algorithms on all 10 pairs with the given scoring scheme."""
    rows = []
    for pair in DNA_PAIRS:
        seq1, seq2 = pair["seq1"], pair["seq2"]
        nw = needleman_wunsch(seq1, seq2, match, mismatch, gap)
        sw = smith_waterman(seq1, seq2, match, mismatch, gap)
        rows.append(
            {
                "pair_id": pair["id"],
                "len_seq1": len(seq1),
                "len_seq2": len(seq2),
                "nw_score": nw.score,
                "nw_identity": round(nw.identity(), 4),
                "sw_score": sw.score,
                "sw_identity": round(sw.identity(), 4),
                "sw_local_len": len(sw.aligned_seq1),
                "nw_result": nw,
                "sw_result": sw,
            }
        )
    return rows


def _write_alignments_txt(rows: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            nw, sw = row["nw_result"], row["sw_result"]
            f.write(f"{'=' * 78}\nPair {row['pair_id']}\n{'=' * 78}\n")
            f.write(f"\n--- Needleman-Wunsch (global) | score = {nw.score} ---\n")
            f.write(nw.pretty() + "\n")
            f.write(f"\n--- Smith-Waterman (local) | score = {sw.score} "
                    f"| region seq1[{sw.start[0]}:{sw.end[0]}] seq2[{sw.start[1]}:{sw.end[1]}] ---\n")
            f.write(sw.pretty() + "\n\n")


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)

    print("Running Needleman-Wunsch and Smith-Waterman on all 10 pairs "
          "(match=+2, mismatch=-1, gap=-2)...")
    rows = run_all_pairs()

    # --- scores_summary.csv ---
    import csv

    summary_path = RESULTS_DIR / "scores_summary.csv"
    fieldnames = ["pair_id", "len_seq1", "len_seq2", "nw_score", "nw_identity",
                  "sw_score", "sw_identity", "sw_local_len"]
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in fieldnames})
    print(f"Wrote {summary_path}")

    for row in rows:
        print(
            f"  Pair {row['pair_id']:>2}: NW score={row['nw_score']:>4} "
            f"(identity={row['nw_identity']:.2%})  |  "
            f"SW score={row['sw_score']:>4} (identity={row['sw_identity']:.2%}, "
            f"local_len={row['sw_local_len']})"
        )

    # --- alignments.txt ---
    _write_alignments_txt(rows, RESULTS_DIR / "alignments.txt")
    print(f"Wrote {RESULTS_DIR / 'alignments.txt'}")

    # --- heatmap figures for a couple of representative pairs ---
    import matplotlib
    matplotlib.use("Agg")

    for pair_id in (1, 3):
        row = next(r for r in rows if r["pair_id"] == pair_id)
        pair = DNA_PAIRS[pair_id - 1]
        fig = plot_alignment_matrix(row["nw_result"], pair["seq1"], pair["seq2"])
        fig_path = FIGURES_DIR / f"pair{pair_id}_needleman_wunsch.png"
        fig.savefig(fig_path, dpi=150)
        print(f"Wrote {fig_path}")

        fig = plot_alignment_matrix(row["sw_result"], pair["seq1"], pair["seq2"])
        fig_path = FIGURES_DIR / f"pair{pair_id}_smith_waterman.png"
        fig.savefig(fig_path, dpi=150)
        print(f"Wrote {fig_path}")

    # --- parameter sensitivity on 3 selected pairs ---
    run_parameter_sensitivity()

    # --- optional Biopython comparison ---
    run_biopython_comparison()


PARAMETER_SETS = [
    {"name": "default", "match": 2, "mismatch": -1, "gap": -2},
    {"name": "harsh_gap", "match": 2, "mismatch": -1, "gap": -6},
    {"name": "lenient_mismatch", "match": 2, "mismatch": 0, "gap": -2},
    {"name": "strict_mismatch", "match": 1, "mismatch": -3, "gap": -2},
]

SENSITIVITY_PAIR_IDS = [1, 3, 7]


def run_parameter_sensitivity() -> None:
    """Part 3: re-run alignment on 3 selected pairs under several scoring
    schemes and report how the results change."""
    import csv

    out_path = RESULTS_DIR / "parameter_sensitivity.csv"
    fieldnames = ["pair_id", "param_set", "match", "mismatch", "gap",
                  "nw_score", "nw_identity", "nw_gaps",
                  "sw_score", "sw_identity", "sw_local_len"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for pair_id in SENSITIVITY_PAIR_IDS:
            pair = next(p for p in DNA_PAIRS if p["id"] == pair_id)
            for params in PARAMETER_SETS:
                nw = needleman_wunsch(pair["seq1"], pair["seq2"],
                                       params["match"], params["mismatch"], params["gap"])
                sw = smith_waterman(pair["seq1"], pair["seq2"],
                                     params["match"], params["mismatch"], params["gap"])
                writer.writerow({
                    "pair_id": pair_id,
                    "param_set": params["name"],
                    "match": params["match"],
                    "mismatch": params["mismatch"],
                    "gap": params["gap"],
                    "nw_score": nw.score,
                    "nw_identity": round(nw.identity(), 4),
                    "nw_gaps": nw.aligned_seq1.count("-") + nw.aligned_seq2.count("-"),
                    "sw_score": sw.score,
                    "sw_identity": round(sw.identity(), 4),
                    "sw_local_len": len(sw.aligned_seq1),
                })
    print(f"Wrote {out_path}")


def run_biopython_comparison() -> None:
    """Part 4 (bonus): compare against Biopython's pairwise aligner and
    report score + timing differences."""
    import csv

    try:
        from Bio import Align
    except ImportError:
        print("Biopython not installed; skipping bonus comparison "
              "(pip install biopython).")
        return

    aligner = Align.PairwiseAligner()
    aligner.match_score = 2
    aligner.mismatch_score = -1
    aligner.open_gap_score = -2
    aligner.extend_gap_score = -2

    out_path = RESULTS_DIR / "biopython_comparison.csv"
    fieldnames = ["pair_id", "mode",
                  "custom_score", "biopython_score", "score_match",
                  "custom_time_s", "biopython_time_s"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for pair in DNA_PAIRS:
            seq1, seq2 = pair["seq1"], pair["seq2"]

            aligner.mode = "global"
            t0 = time.perf_counter()
            nw = needleman_wunsch(seq1, seq2)
            custom_time = time.perf_counter() - t0
            t0 = time.perf_counter()
            bio_score = aligner.score(seq1, seq2)
            bio_time = time.perf_counter() - t0
            writer.writerow({
                "pair_id": pair["id"], "mode": "global",
                "custom_score": nw.score, "biopython_score": bio_score,
                "score_match": nw.score == bio_score,
                "custom_time_s": round(custom_time, 6),
                "biopython_time_s": round(bio_time, 6),
            })

            aligner.mode = "local"
            t0 = time.perf_counter()
            sw = smith_waterman(seq1, seq2)
            custom_time = time.perf_counter() - t0
            t0 = time.perf_counter()
            bio_score = aligner.score(seq1, seq2)
            bio_time = time.perf_counter() - t0
            writer.writerow({
                "pair_id": pair["id"], "mode": "local",
                "custom_score": sw.score, "biopython_score": bio_score,
                "score_match": sw.score == bio_score,
                "custom_time_s": round(custom_time, 6),
                "biopython_time_s": round(bio_time, 6),
            })
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
