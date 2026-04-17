"""
Run missing tasks for existing models + benchmark new models.
Skips tasks already completed. Prints cost summary at the end.

Coverage status (2026-04-17 after batch 2):
  gpt-4o-mini  and gpt-4.1-nano tasks re-run with --max-steps override.
  Root cause: both models exceed YAML max_steps (take 2-5x more steps than
  calibration models). Fix: per-task step budget in PLAN below.

  claude-opus-4-6       17/23  — 6 remaining (~$11.52) ← needs Anthropic credits
  claude-sonnet-4-6      9/23  — 14 remaining (~$6.66) ← needs Anthropic credits
  claude-haiku-4-5       8/23  — 15 remaining (~$0.94) ← needs Anthropic credits
"""
import subprocess, sys, json, time
from pathlib import Path

ROOT = Path(__file__).parent.parent
VENV_PYTHON = str(ROOT / ".venv/bin/python")
RESULTS = ROOT / "docs/results.json"

# ── load already-completed runs ──────────────────────────────────────────────
with open(RESULTS) as f:
    data = json.load(f)

done = set()
for r in data["runs"]:
    done.add((r["model"], r["task_id"]))

ALL_TASKS = sorted(set(r["task_id"] for r in data["runs"]))

# ── what to run ───────────────────────────────────────────────────────────────
# PLAN entries: (model, [(task_id, max_steps_override), ...])
# max_steps_override = None → use YAML default; int → override
# Step budgets set to observed_max + 40 headroom.
PLAN = [
    # gpt-4o-mini: 3 tasks, observed up to 51 steps, YAML max 20-25
    ("gpt-4o-mini", [
        ("mod_001",   80),
        ("model_001", 80),
        ("model_003", 90),
    ]),
    # gpt-4.1-nano: 4 tasks, observed up to 104 steps, YAML max 25-40
    ("gpt-4.1-nano", [
        ("feat_003",  100),
        ("mod_004",   110),
        ("model_005", 140),
        ("stat_004",  None),   # only 10 steps observed; YAML default is fine
    ]),
    # ── Anthropic models — uncomment after adding credits ────────────────────
    # 6 tasks — Anthropic Opus, ~$11.52 total
    # ("claude-opus-4-6", [
    #     ("model_005", None),
    #     ("stat_001", None), ("stat_002", None), ("stat_003", None),
    #     ("stat_004", None), ("stat_005", None),
    # ]),
    # 14 tasks — Anthropic Sonnet, ~$6.66 total
    # ("claude-sonnet-4-6", [
    #     ("mod_001", None), ("mod_003", None), ("mod_004", None), ("mod_005", None),
    #     ("model_001", None), ("model_002", None), ("model_003", None),
    #     ("model_004", None), ("model_005", None),
    #     ("stat_001", None), ("stat_002", None), ("stat_003", None),
    #     ("stat_004", None), ("stat_005", None),
    # ]),
    # 15 tasks — Anthropic Haiku, ~$0.94 total
    # ("claude-haiku-4-5-20251001", [
    #     ("mod_001", None), ("mod_002", None), ("mod_003", None),
    #     ("mod_004", None), ("mod_005", None),
    #     ("model_001", None), ("model_002", None), ("model_003", None),
    #     ("model_004", None), ("model_005", None),
    #     ("stat_001", None), ("stat_002", None), ("stat_003", None),
    #     ("stat_004", None), ("stat_005", None),
    # ]),
]

# ── runner ────────────────────────────────────────────────────────────────────
total_ran = 0
errors = []

for model, tasks in PLAN:
    to_run = [(t, ms) for t, ms in tasks if (model, t) not in done]
    if not to_run:
        print(f"[SKIP] {model} — all tasks already done")
        continue
    print(f"\n{'='*60}")
    print(f"MODEL: {model}  ({len(to_run)} tasks to run)")
    print(f"{'='*60}")
    for task, max_steps in to_run:
        step_note = f" [max-steps={max_steps}]" if max_steps else ""
        print(f"  → {task}{step_note} ... ", end="", flush=True)
        t0 = time.time()
        cmd = [VENV_PYTHON, "-m", "realdataagentbench.cli", "run", task, "--model", model]
        if max_steps:
            cmd += ["--max-steps", str(max_steps)]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
        elapsed = time.time() - t0
        if result.returncode == 0:
            score_line = [l for l in result.stdout.splitlines() if "RDAB" in l or "Score" in l]
            score_str = score_line[-1].strip() if score_line else ""
            print(f"OK ({elapsed:.0f}s)  {score_str}")
            total_ran += 1
        else:
            err = result.stderr[-300:] if result.stderr else result.stdout[-300:]
            print(f"FAILED — {err.strip()[:120]}")
            errors.append((model, task, err.strip()[:200]))

print(f"\n{'='*60}")
print(f"DONE — {total_ran} tasks run successfully, {len(errors)} errors")
if errors:
    print("\nFailed runs:")
    for model, task, err in errors:
        print(f"  {model} / {task}: {err[:100]}")

# ── rebuild leaderboard ───────────────────────────────────────────────────────
if total_ran > 0:
    print("\nRebuilding leaderboard...")
    r = subprocess.run(
        [VENV_PYTHON, str(ROOT / "scripts/build_leaderboard.py")],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    if r.returncode == 0:
        print("Leaderboard rebuilt OK")
    else:
        print(f"Leaderboard rebuild failed: {r.stderr[-200:]}")
