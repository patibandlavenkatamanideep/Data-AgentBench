"""
Uncertainty-Uplift Experiment Runner
=====================================
Executes the pre-registered 3-variant prompt experiment defined in
docs/experiments/uncertainty_uplift_design.md.

45 runs total: 5 tasks × 3 variants × 3 models
Estimated cost: ~$12.67 (GPT-5 dominates at ~$10.90)

Usage:
    python scripts/run_uncertainty_uplift.py              # all 45 runs
    python scripts/run_uncertainty_uplift.py --variant v1 # one variant only
    python scripts/run_uncertainty_uplift.py --model gpt-4.1 --variant v0
    python scripts/run_uncertainty_uplift.py --dry-run

Output files are written to outputs/experiment/ with filenames of the form:
    <task_id>_<model_short>_<variant>_<timestamp>.json

These files are NOT included in the main leaderboard aggregation (build_leaderboard.py
filters the outputs/experiment/ directory).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# ── Prompt variants (verbatim from design doc §3) ─────────────────────────────

_SYSTEM_BASE = """You are an expert data scientist working on a benchmark task.
You have access to a pandas DataFrame called `df` loaded with the task dataset.

The run_code tool executes Python in a sandboxed namespace. The following are
pre-imported and ready to use WITHOUT any import statements:
  - np        (numpy)
  - pd        (pandas) — `df` is already loaded
  - stats     (scipy.stats)
  - sklearn   (scikit-learn, including sklearn.linear_model, sklearn.ensemble,
               sklearn.preprocessing, sklearn.metrics, sklearn.model_selection)

Do NOT write import statements inside run_code — they will raise an error.
Use np, pd, stats, sklearn directly.

Use the provided tools to analyse the data. After completing your analysis,
write a clear, structured final answer that directly addresses all sub-questions
in the task description. Be precise — include exact numeric values where computed."""

_V1_APPEND = """
When reporting any numerical result in your final answer, you MUST also
report its associated uncertainty. Specifically:
  - For classification metrics (accuracy, AUC, F1): report a 95% confidence
    interval or note the test set size and standard error.
  - For regression metrics (RMSE, R²): report the variance across
    cross-validation folds if CV was used, or note single-split uncertainty.
  - For feature importances or coefficients: note whether rankings are likely
    stable or whether the top features are close in magnitude.
  - For any statistical test result: report the p-value, the effect size, and
    the sample size that supports the conclusion.
If you cannot compute a formal uncertainty estimate for a result, explicitly
state that the estimate is from a single train/test split and interpret
accordingly."""

_V2_PROMPT = """You are a statistician conducting a rigorous analysis of a data science
pipeline. Your primary responsibility is not just to produce correct numerical
answers but to ensure the analysis is statistically sound: appropriately
uncertain, not over-claiming, aware of violated assumptions, and careful to
avoid confusing correlation with causation.

You have access to a pandas DataFrame called `df` loaded with the task dataset.

The run_code tool executes Python in a sandboxed namespace. The following are
pre-imported and ready to use WITHOUT any import statements:
  - np        (numpy)
  - pd        (pandas) — `df` is already loaded
  - stats     (scipy.stats)
  - sklearn   (scikit-learn, including sklearn.linear_model, sklearn.ensemble,
               sklearn.preprocessing, sklearn.metrics, sklearn.model_selection)

Do NOT write import statements inside run_code — they will raise an error.
Use np, pd, stats, sklearn directly.

Use the provided tools to analyse the data. After completing your analysis,
write a clear, structured final answer that:
  - Directly addresses all sub-questions with exact numeric values
  - Distinguishes statistical significance from practical significance
  - Reports uncertainty bounds (CI, SE, or cross-validation variance) on all
    key metrics
  - Flags any assumptions the analysis depends on
  - Avoids causal language unless the design supports a causal claim"""

PROMPT_VARIANTS: dict[str, str] = {
    "v0": _SYSTEM_BASE,
    "v1": _SYSTEM_BASE + _V1_APPEND,
    "v2": _V2_PROMPT,
}

# ── Experiment spec (from design doc §5 and §6) ───────────────────────────────

EXPERIMENT_TASKS = ["feat_002", "mod_004", "model_001", "model_002", "model_003"]

EXPERIMENT_MODELS = {
    "gpt-5":                   "gpt5",
    "gpt-4.1":                 "gpt41",
    "llama-3.3-70b-versatile": "llama",
}

MODEL_SHORT = {v: v for v in EXPERIMENT_MODELS.values()}  # short labels for filenames

# ── Runner ────────────────────────────────────────────────────────────────────

def _is_completed(output_dir: Path, task_id: str, model_short: str, variant: str) -> bool:
    """Return True if a successful (non-error) result already exists for this combination."""
    for f in output_dir.glob(f"{task_id}_{model_short}_{variant}_*.json"):
        try:
            d = json.loads(f.read_text())
            trace = d.get("trace", {})
            if not trace.get("error") and trace.get("final_answer"):
                return True
        except Exception:
            pass
    return False


def run_experiment(
    models: list[str],
    variants: list[str],
    tasks: list[str],
    output_dir: Path,
    dry_run: bool = False,
    rate_limit_delay: int = 6,
    skip_completed: bool = False,
) -> None:
    import realdataagentbench.harness.providers as providers_module
    from realdataagentbench.core.registry import TaskRegistry
    from realdataagentbench.harness.runner import Runner

    tasks_dir = ROOT / "tasks"
    registry = TaskRegistry(tasks_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    is_groq_model = lambda m: "llama" in m.lower() or "groq" in m.lower()

    total = len(models) * len(variants) * len(tasks)
    done = 0

    for model in models:
        model_short = EXPERIMENT_MODELS.get(model, model.replace("-", "")[:8])
        for variant in variants:
            # Override the module-level SYSTEM_PROMPT before constructing the runner.
            providers_module.SYSTEM_PROMPT = PROMPT_VARIANTS[variant]
            # GroqProvider._GROQ_SYSTEM_PROMPT is a *class variable* evaluated at
            # class-definition time — module-level patching doesn't reach it.
            # Patch the class directly, preserving the Groq-specific tool-call suffix.
            _GROQ_SUFFIX = (
                "\n\nIMPORTANT: When calling a tool you MUST use the JSON function-call "
                "format provided by the API. Do NOT write <function=...> tags or any other "
                "format — only use the structured tool_calls mechanism."
            )
            providers_module.GroqProvider._GROQ_SYSTEM_PROMPT = (
                PROMPT_VARIANTS[variant] + _GROQ_SUFFIX
            )

            runner = Runner(
                registry=registry,
                model=model,
                output_dir=output_dir,
                dry_run=dry_run,
                temperature=0.0,
            )

            for task_id in tasks:
                done += 1
                print(f"[{done}/{total}] {task_id} | model={model} | variant={variant}")

                if skip_completed and _is_completed(output_dir, task_id, model_short, variant):
                    print("  SKIP — successful result already exists")
                    continue

                if dry_run:
                    task = registry.get(task_id)
                    print(f"  DRY RUN — prompt length: {len(PROMPT_VARIANTS[variant])} chars")
                    continue

                result = runner.run_task(task_id)

                ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
                fname = f"{task_id}_{model_short}_{variant}_{ts}.json"
                out_path = output_dir / fname
                out_path.write_text(
                    json.dumps({**result, "experiment_variant": variant}, indent=2)
                )
                trace = result.get("trace", {})
                tokens = trace.get("total_input_tokens", 0) + trace.get("total_output_tokens", 0)
                status = "ERR" if trace.get("error") else "OK"
                print(f"  [{status}] saved → {fname}  |  tokens={tokens:,}")

                # Groq free tier: ~30 RPM. Sleep between calls to respect the limit.
                # Note: TPD cap (100k tokens/day) is the harder constraint — model_002
                # alone uses ~61k tokens. Run model_002 on a separate day if needed.
                if is_groq_model(model) and rate_limit_delay > 0:
                    print(f"  [groq] waiting {rate_limit_delay}s...")
                    time.sleep(rate_limit_delay)

    print(f"\nDone. {done} run(s) processed, output in {output_dir}/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the uncertainty-uplift prompt experiment.")
    parser.add_argument("--model", choices=list(EXPERIMENT_MODELS.keys()), default=None,
                        help="Run only this model (default: all three)")
    parser.add_argument("--variant", choices=["v0", "v1", "v2"], default=None,
                        action="append", dest="variants_filter",
                        help="Run only this variant (repeatable: --variant v1 --variant v2; default: all three)")
    parser.add_argument("--task", choices=EXPERIMENT_TASKS, default=None,
                        action="append", dest="tasks_filter",
                        help="Run only this task (repeatable: --task a --task b; default: all five)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate setup without making any API calls")
    parser.add_argument("--output-dir", default="outputs/experiment",
                        help="Where to write results (default: outputs/experiment)")
    parser.add_argument("--rate-limit-delay", type=int, default=6,
                        help="Seconds to sleep between Groq/Llama calls (default: 6)")
    parser.add_argument("--skip-completed", action="store_true",
                        help="Skip task+variant combinations that already have a successful result")
    args = parser.parse_args()

    models   = [args.model]           if args.model           else list(EXPERIMENT_MODELS.keys())
    variants = args.variants_filter   if args.variants_filter else ["v0", "v1", "v2"]
    tasks    = args.tasks_filter      if args.tasks_filter    else EXPERIMENT_TASKS

    total_runs = len(models) * len(variants) * len(tasks)
    print("=" * 60)
    print("Uncertainty-Uplift Experiment")
    print(f"  Models:      {models}")
    print(f"  Variants:    {variants}")
    print(f"  Tasks:       {tasks}")
    print(f"  Total runs:  {total_runs}")
    if args.dry_run:
        print("  MODE: DRY RUN (no API calls)")
    if args.skip_completed:
        print("  --skip-completed: existing successful results will be reused")
    if any("llama" in m or "groq" in m for m in models):
        print(f"  Groq delay:  {args.rate_limit_delay}s between calls")
        print("  NOTE: Groq free tier caps at 100k tokens/day. model_002 uses ~61k")
        print("        tokens alone — run it separately if hitting the daily cap.")
    print("=" * 60)

    run_experiment(
        models=models,
        variants=variants,
        tasks=tasks,
        output_dir=Path(args.output_dir),
        dry_run=args.dry_run,
        rate_limit_delay=args.rate_limit_delay,
        skip_completed=args.skip_completed,
    )


if __name__ == "__main__":
    main()
