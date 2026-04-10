"""Build leaderboard — aggregates all outputs/*.json into docs/results.json."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running as a script from any directory
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from realdataagentbench.core.registry import TaskRegistry
from realdataagentbench.harness.pricing import compute_cost  # single source of truth
from realdataagentbench.harness.providers import resolve_model  # normalise aliases
from realdataagentbench.scoring.composite import CompositeScorer


def build(
    outputs_dir: Path = ROOT / "outputs",
    docs_dir: Path = ROOT / "docs",
    tasks_dir: Path = ROOT / "tasks",
) -> None:
    docs_dir.mkdir(exist_ok=True)
    registry = TaskRegistry(tasks_dir)
    scorer = CompositeScorer()

    result_files = sorted(outputs_dir.glob("*.json"))
    if not result_files:
        print("No result files found in outputs/")
        return

    # Group by task_id — keep only the latest successful run per (task_id, model)
    runs: dict[tuple[str, str], dict] = {}
    for path in result_files:
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        if data.get("dry_run"):
            continue
        # Skip runs that produced no usable output (credit exhaustion, unrecovered errors)
        trace = data.get("trace", {})
        if trace.get("error") and not trace.get("final_answer"):
            continue
        task_id = data.get("task_id")
        model = resolve_model(data.get("model", "unknown"))  # normalise aliases
        if not task_id or task_id not in registry:
            continue
        key = (task_id, model)
        existing = runs.get(key)
        if not existing or data.get("run_at", "") > existing.get("run_at", ""):
            runs[key] = data

    # Score each run
    rows = []
    for (task_id, model), data in sorted(runs.items()):
        task = registry.get(task_id)
        card = scorer.score(task, data)
        trace = data.get("trace", {})
        input_tokens = trace.get("total_input_tokens", 0)
        output_tokens = trace.get("total_output_tokens", 0)
        cost_usd = compute_cost(model, input_tokens, output_tokens)
        rows.append({
            "task_id": task_id,
            "title": task.title,
            "difficulty": task.difficulty,
            "category": task.category,
            "model": model,
            "run_at": data.get("run_at", ""),
            "correctness": card.correctness,
            "code_quality": card.code_quality,
            "efficiency": card.efficiency,
            "stat_validity": card.stat_validity,
            "dab_score": card.dab_score,
            "total_tokens": input_tokens + output_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd,
            "num_steps": trace.get("num_steps", 0),
        })

    # Model-level summary
    model_summary: dict[str, dict] = {}
    for row in rows:
        m = row["model"]
        if m not in model_summary:
            model_summary[m] = {"scores": [], "costs": [], "model": m}
        model_summary[m]["scores"].append(row["dab_score"])
        model_summary[m]["costs"].append(row["cost_usd"])

    summaries = []
    for m, info in model_summary.items():
        scores = info["scores"]
        costs = info["costs"]
        summaries.append({
            "model": m,
            "avg_dab_score": round(sum(scores) / len(scores), 4),
            "avg_cost_usd": round(sum(costs) / len(costs), 6),
            "total_cost_usd": round(sum(costs), 4),
            "tasks_run": len(scores),
        })
    summaries.sort(key=lambda x: x["avg_dab_score"], reverse=True)

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_runs": len(rows),
        "model_summary": summaries,
        "runs": rows,
    }

    out_path = docs_dir / "results.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"Leaderboard written to {out_path} ({len(rows)} runs)")


if __name__ == "__main__":
    build()
