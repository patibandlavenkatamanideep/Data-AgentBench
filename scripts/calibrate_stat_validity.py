"""Calibrate the lexical stat-validity scorer against an LLM judge.

Samples agent answer files from outputs/, scores each with both the lexical
scorer and the LLM judge, then reports:
  - Per-criterion agreement (%) and Cohen's kappa
  - Pearson correlation between total scores
  - Cases with the largest disagreement

Usage:
  python scripts/calibrate_stat_validity.py              # 20 random samples
  python scripts/calibrate_stat_validity.py --n 40       # 40 samples
  python scripts/calibrate_stat_validity.py --model claude-haiku-4-5-20251001
  python scripts/calibrate_stat_validity.py --out calibration_report.json
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from realdataagentbench.core.registry import TaskRegistry
from realdataagentbench.scoring.stat_validity import StatValidityScorer
from realdataagentbench.scoring.llm_judge import LLMJudgeScorer


def cohen_kappa(a: list[int], b: list[int]) -> float:
    """Cohen's kappa for two binary raters."""
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    pa1 = sum(a) / n
    pb1 = sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


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
    return num / (dx * dy)


def load_samples(outputs_dir: Path, registry: TaskRegistry, n: int) -> list[dict]:
    """Load up to n valid answer files, stratified by category."""
    files = sorted(outputs_dir.glob("*.json"))
    valid = []
    for path in files:
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        if data.get("dry_run"):
            continue
        trace = data.get("trace", {})
        answer = trace.get("final_answer", "")
        if not answer or (trace.get("error") and not answer):
            continue
        task_id = data.get("task_id")
        if not task_id or task_id not in registry:
            continue
        task = registry.get(task_id)
        valid.append({
            "file": str(path.name),
            "task_id": task_id,
            "category": task.category,
            "description": task.description,
            "answer": answer,
        })

    # Stratified sample: equal representation across categories
    by_cat: dict[str, list] = {}
    for item in valid:
        by_cat.setdefault(item["category"], []).append(item)

    sample = []
    cats = list(by_cat.keys())
    per_cat = max(1, n // len(cats))
    for cat in cats:
        pool = by_cat[cat]
        random.shuffle(pool)
        sample.extend(pool[:per_cat])

    random.shuffle(sample)
    return sample[:n]


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate stat-validity scorer vs LLM judge")
    parser.add_argument("--n", type=int, default=20, help="Number of answers to sample (default: 20)")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001", help="LLM judge model")
    parser.add_argument("--out", default=None, help="Write JSON report to this path")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set. Export it before running calibration.")
        sys.exit(1)

    registry = TaskRegistry(ROOT / "tasks")
    outputs_dir = ROOT / "outputs"

    if not any(outputs_dir.glob("*.json")):
        print(f"ERROR: No result files in {outputs_dir}. Run some benchmarks first.")
        sys.exit(1)

    samples = load_samples(outputs_dir, registry, args.n)
    if not samples:
        print("ERROR: No valid answer files found.")
        sys.exit(1)

    print(f"Calibrating on {len(samples)} samples (model={args.model})")
    print(f"Categories: {dict((c, sum(1 for s in samples if s['category']==c)) for c in sorted(set(s['category'] for s in samples)))}")
    print()

    lexical = StatValidityScorer()
    judge = LLMJudgeScorer(model=args.model, api_key=api_key)

    CRITERIA = ["reports_uncertainty", "uses_appropriate_test", "interprets_correctly", "avoids_p_hacking_signals"]

    results = []
    total_input_tokens = 0
    total_output_tokens = 0

    for i, s in enumerate(samples, 1):
        print(f"  [{i:2d}/{len(samples)}] {s['task_id']} ({s['category']})...", end=" ", flush=True)
        lex_result = lexical.score_detailed(s["answer"], category=s["category"])
        try:
            llm_result = judge.score(s["answer"], category=s["category"], task_description=s["description"])
        except Exception as e:
            print(f"SKIP (judge error: {e})")
            continue

        total_input_tokens += llm_result.input_tokens
        total_output_tokens += llm_result.output_tokens

        llm_sv = llm_result.stat_validity
        print(f"lex={lex_result.score:.2f}  llm={llm_sv.score:.2f}")

        results.append({
            "task_id": s["task_id"],
            "category": s["category"],
            "file": s["file"],
            "lexical": {
                "score": lex_result.score,
                "reports_uncertainty": int(lex_result.reports_uncertainty),
                "uses_appropriate_test": int(lex_result.uses_appropriate_test),
                "interprets_correctly": int(lex_result.interprets_correctly),
                "avoids_p_hacking_signals": int(lex_result.avoids_p_hacking_signals),
            },
            "llm_judge": {
                "score": llm_sv.score,
                "reports_uncertainty": int(llm_sv.reports_uncertainty),
                "uses_appropriate_test": int(llm_sv.uses_appropriate_test),
                "interprets_correctly": int(llm_sv.interprets_correctly),
                "avoids_p_hacking_signals": int(llm_sv.avoids_p_hacking_signals),
            },
            "score_delta": round(llm_sv.score - lex_result.score, 4),
        })

    if not results:
        print("No results collected.")
        sys.exit(1)

    # --- Aggregate stats ---
    lex_scores = [r["lexical"]["score"] for r in results]
    llm_scores = [r["llm_judge"]["score"] for r in results]
    r_pearson = pearson(lex_scores, llm_scores)

    criterion_stats = {}
    for crit in CRITERIA:
        lex_vals = [r["lexical"][crit] for r in results]
        llm_vals = [r["llm_judge"][crit] for r in results]
        pct_agree = sum(a == b for a, b in zip(lex_vals, llm_vals)) / len(results)
        kappa = cohen_kappa(lex_vals, llm_vals)
        criterion_stats[crit] = {
            "pct_agreement": round(pct_agree, 4),
            "cohen_kappa": round(kappa, 4) if not math.isnan(kappa) else None,
            "lexical_positive_rate": round(sum(lex_vals) / len(lex_vals), 4),
            "judge_positive_rate": round(sum(llm_vals) / len(llm_vals), 4),
        }

    # Cases with largest disagreement
    disagreements = sorted(results, key=lambda r: abs(r["score_delta"]), reverse=True)[:5]

    est_cost_usd = (total_input_tokens * 0.80 + total_output_tokens * 4.0) / 1_000_000
    mean_lex = sum(lex_scores) / len(lex_scores)
    mean_llm = sum(llm_scores) / len(llm_scores)

    report = {
        "n_samples": len(results),
        "judge_model": args.model,
        "seed": args.seed,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "estimated_cost_usd": round(est_cost_usd, 4),
        "score_correlation_pearson": round(r_pearson, 4) if not math.isnan(r_pearson) else None,
        "mean_lexical_score": round(mean_lex, 4),
        "mean_judge_score": round(mean_llm, 4),
        "mean_score_delta_judge_minus_lexical": round(mean_llm - mean_lex, 4),
        "criterion_stats": criterion_stats,
        "top_disagreements": [
            {k: v for k, v in d.items() if k != "file"}
            for d in disagreements
        ],
        "all_results": results,
    }

    print()
    print("=" * 60)
    print(f"CALIBRATION REPORT — {len(results)} samples")
    print("=" * 60)
    print(f"Pearson correlation (lex vs judge): {r_pearson:.3f}")
    print(f"Mean lexical score: {mean_lex:.3f}  |  Mean judge score: {mean_llm:.3f}")
    print(f"Bias (judge − lexical): {mean_llm - mean_lex:+.3f}")
    print()
    print("Per-criterion stats:")
    for crit, stats in criterion_stats.items():
        kappa = stats['cohen_kappa']
        kappa_str = f"{kappa:.3f}" if kappa is not None else "N/A"
        print(f"  {crit:<30}  agree={stats['pct_agreement']:.1%}  κ={kappa_str}  "
              f"lex+={stats['lexical_positive_rate']:.1%}  llm+={stats['judge_positive_rate']:.1%}")
    print()
    print(f"Estimated judge cost: ${est_cost_usd:.4f} ({total_input_tokens:,} in, {total_output_tokens:,} out)")
    print()
    print("Largest disagreements:")
    for d in disagreements:
        print(f"  {d['task_id']} ({d['category']})  lex={d['lexical']['score']:.2f}  llm={d['llm_judge']['score']:.2f}  Δ={d['score_delta']:+.2f}")

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(json.dumps(report, indent=2))
        print(f"\nReport written to {out_path}")

    print()
    print("Interpretation guide:")
    print("  κ > 0.8 → almost perfect agreement (safe to use lexical scorer)")
    print("  κ 0.6–0.8 → substantial agreement (lexical scorer usable with known bias)")
    print("  κ < 0.6 → moderate/poor agreement (consider replacing with judge)")


if __name__ == "__main__":
    main()
