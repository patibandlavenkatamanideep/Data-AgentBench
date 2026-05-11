"""Re-score all local output traces with the patched stat_validity scorer.

Produces a before/after diff table grouped by model and category, showing
where the numeric-evidence check changed scores.

Usage:
    python scripts/rescore_stat_validity.py [--outputs-dir outputs]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from realdataagentbench.scoring.stat_validity import StatValidityScorer
from realdataagentbench.core.registry import TaskRegistry


def _old_score(answer: str, category: str) -> float:
    """Replicate the pre-patch binary Check 1 for comparison."""
    import re
    UNCERTAINTY_PATTERNS = [
        r"\bp[\s-]*value\b", r"\bconfidence interval\b", r"\bci\b",
        r"\bstandard deviation\b", r"\bstandard error\b",
        r"\bp\s*=\s*0\.", r"\br\s*=\s*[-+]?\d",
        r"\bapproximately\b", r"\baround\b", r"\brange\b",
        r"\buncertain", r"\bbootstrap\b",
        r"\bprediction interval\b", r"\bvariance\b",
        r"\bstability\b", r"\bstable\b",
        r"\brobust", r"\breliabilit",
        r"\berror bar", r"\bmargin of error\b",
        r"\bstd\b",
    ]
    ans = answer.lower()
    uncertainty = any(re.search(p, ans) for p in UNCERTAINTY_PATTERNS)
    # For old scorer, Check 1 contributes 0.25 if True, 0 if False.
    # Checks 2-4 are the same — to isolate the diff, only compare Check 1 contribution.
    # New: Check 1 contributes uncertainty_float/4; old: 0.25 if any match else 0.
    new_scorer = StatValidityScorer()
    new_r = new_scorer.score_detailed(answer, category)
    old_check1 = 0.25 if uncertainty else 0.0
    new_check1 = new_r.reports_uncertainty / 4
    old_total = round(new_r.score - new_check1 + old_check1, 4)
    return old_total, new_r.score, new_r.reports_uncertainty


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs-dir", default="outputs",
                        help="Directory with run JSON files (default: outputs)")
    args = parser.parse_args()

    outputs_dir = ROOT / args.outputs_dir
    if not outputs_dir.exists():
        print(f"outputs dir not found: {outputs_dir}")
        sys.exit(1)

    registry = TaskRegistry(ROOT / "tasks")
    scorer = StatValidityScorer()

    # model → category → list of (old, new)
    by_model_cat: dict[str, dict[str, list[tuple[float, float]]]] = defaultdict(lambda: defaultdict(list))
    # model → list of (old, new) across all categories
    by_model: dict[str, list[tuple[float, float]]] = defaultdict(list)
    # category → list of (old, new)
    by_cat: dict[str, list[tuple[float, float]]] = defaultdict(list)

    n_files = 0
    n_no_answer = 0

    result_files = sorted(outputs_dir.glob("*.json"))
    for f in result_files:
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue

        trace = d.get("trace", {})
        answer = trace.get("final_answer", "") or ""
        if not answer:
            n_no_answer += 1
            continue

        # Infer task_id from filename
        task_id = f.stem.rsplit("_", 1)[0]
        # Remove timestamp suffix: stem is like feat_002_20260409T060731
        parts = f.stem.split("_")
        # Find the part that looks like a timestamp (YYYYMMDDTHHmmss)
        ts_idx = next((i for i, p in enumerate(parts) if len(p) == 15 and p[8] == "T"), None)
        if ts_idx is None:
            continue
        task_id = "_".join(parts[:ts_idx])

        try:
            task = registry.get(task_id)
        except Exception:
            continue

        category = task.category
        model = d.get("model", "unknown")

        old_s, new_s, unc_val = _old_score(answer, category)
        by_model[model].append((old_s, new_s))
        by_cat[category].append((old_s, new_s))
        by_model_cat[model][category].append((old_s, new_s))
        n_files += 1

    print(f"Scored {n_files} traces ({n_no_answer} skipped — no final answer)\n")

    # ── Per-model summary ────────────────────────────────────────────────────
    print("=" * 70)
    print("STAT VALIDITY: OLD vs NEW scorer — per model (mean across all tasks)")
    print("=" * 70)
    print(f"{'Model':<32} {'Old':>7} {'New':>7} {'Δ':>7}  {'N':>5}")
    print("-" * 70)

    rows = []
    for model, pairs in sorted(by_model.items()):
        old_mean = sum(o for o, _ in pairs) / len(pairs)
        new_mean = sum(n for _, n in pairs) / len(pairs)
        delta = new_mean - old_mean
        rows.append((model, old_mean, new_mean, delta, len(pairs)))

    rows.sort(key=lambda r: -r[2])
    for model, old_m, new_m, delta, n in rows:
        print(f"{model:<32} {old_m:>7.3f} {new_m:>7.3f} {delta:>+7.3f}  {n:>5}")

    # ── Per-category summary ─────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("STAT VALIDITY: OLD vs NEW — per category")
    print("=" * 70)
    print(f"{'Category':<25} {'Old':>7} {'New':>7} {'Δ':>7}  {'N':>5}")
    print("-" * 70)
    for cat, pairs in sorted(by_cat.items()):
        old_m = sum(o for o, _ in pairs) / len(pairs)
        new_m = sum(n for _, n in pairs) / len(pairs)
        delta = new_m - old_m
        print(f"{cat:<25} {old_m:>7.3f} {new_m:>7.3f} {delta:>+7.3f}  {len(pairs):>5}")

    # ── By model × category ──────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("STAT VALIDITY: OLD vs NEW — model × category (top 5 models)")
    print("=" * 70)
    top_models = [r[0] for r in rows[:6]]
    cats = sorted(by_cat.keys())
    header = f"{'Model':<28}" + "".join(f"  {c[:6]:>6}" for c in cats)
    print(header)
    print("-" * len(header))
    for model in top_models:
        row = f"{model:<28}"
        for cat in cats:
            pairs = by_model_cat[model].get(cat, [])
            if pairs:
                new_m = sum(n for _, n in pairs) / len(pairs)
                old_m = sum(o for o, _ in pairs) / len(pairs)
                delta = new_m - old_m
                row += f"  {delta:>+6.3f}"
            else:
                row += "    —   "
        print(row)


if __name__ == "__main__":
    main()
