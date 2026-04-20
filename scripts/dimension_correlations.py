"""Compute and print the scorer-to-scorer correlation matrix.

Reads docs/results.json and reports Pearson correlations between the four
scoring dimensions across all task-model pairs. Optionally saves a PNG
heatmap if matplotlib is available.

Usage:
  python scripts/dimension_correlations.py
  python scripts/dimension_correlations.py --out docs/corr_matrix.png
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


DIMS = ["correctness", "code_quality", "efficiency", "stat_validity"]
LABELS = ["Correctness", "Code Quality", "Efficiency", "Stat Validity"]


def pearson(x: list[float], y: list[float]) -> float:
    n = len(x)
    if n < 2:
        return float("nan")
    mx, my = sum(x) / n, sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    dx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    dy = math.sqrt(sum((yi - my) ** 2 for yi in y))
    if dx == 0 or dy == 0:
        return float("nan")
    return round(num / (dx * dy), 4)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None, help="Save heatmap PNG to this path")
    parser.add_argument("--results", default=str(ROOT / "docs" / "results.json"))
    args = parser.parse_args()

    data = json.loads(Path(args.results).read_text())
    runs = data["runs"]
    n = len(runs)
    print(f"Computing correlations across {n} task-model pairs\n")

    vectors = {dim: [r[dim] for r in runs] for dim in DIMS}

    # Build correlation matrix
    matrix: list[list[float]] = []
    for d1 in DIMS:
        row = []
        for d2 in DIMS:
            row.append(pearson(vectors[d1], vectors[d2]))
        matrix.append(row)

    # Print text table
    col_w = 14
    header = " " * 16 + "".join(f"{lbl:>{col_w}}" for lbl in LABELS)
    print(header)
    print("-" * (16 + col_w * len(LABELS)))
    for i, lbl in enumerate(LABELS):
        row_str = f"{lbl:<16}"
        for j in range(len(DIMS)):
            v = matrix[i][j]
            cell = f"{v:.4f}" if not math.isnan(v) else " NaN "
            row_str += f"{cell:>{col_w}}"
        print(row_str)

    print()
    print("Interpretation:")
    print("  r > 0.7  → dimensions track each other closely (redundant information)")
    print("  r < 0.3  → dimensions are largely independent (each adds unique signal)")
    print()

    # Highlight notable pairs
    pairs = []
    for i in range(len(DIMS)):
        for j in range(i + 1, len(DIMS)):
            v = matrix[i][j]
            pairs.append((abs(v), v, LABELS[i], LABELS[j]))
    pairs.sort(reverse=True)

    print("Sorted pairs (highest correlation first):")
    for _, v, l1, l2 in pairs:
        flag = " ← high correlation" if abs(v) > 0.7 else (" ← low / independent" if abs(v) < 0.25 else "")
        print(f"  {l1} × {l2}: r = {v:+.4f}{flag}")

    # Optionally save heatmap
    if args.out:
        try:
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            print("\nmatplotlib not installed — skipping PNG output")
            return

        arr = np.array(matrix)
        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(arr, vmin=-1, vmax=1, cmap="RdYlGn")
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        ax.set_xticks(range(len(LABELS)))
        ax.set_yticks(range(len(LABELS)))
        ax.set_xticklabels(LABELS, rotation=30, ha="right", fontsize=9)
        ax.set_yticklabels(LABELS, fontsize=9)
        for i in range(len(DIMS)):
            for j in range(len(DIMS)):
                v = arr[i, j]
                color = "white" if abs(v) > 0.6 else "black"
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=10, color=color, fontweight="bold")
        ax.set_title(f"Scorer Correlation Matrix — RDAB ({n} runs)", fontsize=11, pad=12)
        plt.tight_layout()
        plt.savefig(args.out, dpi=150, bbox_inches="tight")
        print(f"\nHeatmap saved to {args.out}")


if __name__ == "__main__":
    main()
