# DataAgentBench

[![CI](https://github.com/patibandlavenkatamanideep/dataagentbench/actions/workflows/ci.yml/badge.svg)](https://github.com/patibandlavenkatamanideep/dataagentbench/actions)
[![Tests](https://img.shields.io/badge/tests-85%20passing-brightgreen)](https://github.com/patibandlavenkatamanideep/dataagentbench/actions)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**A benchmark for evaluating LLM agents on real data science tasks.**

DataAgentBench (DAB) measures how well LLM agents perform real data science work — exploratory data analysis, missing data handling, statistical validity, and confounding detection — using statistically rigorous, multi-dimensional scoring.

---

## Leaderboard (claude-sonnet-4-6 · 2026-04-09)

| Task | Difficulty | Correctness | Code Quality | Efficiency | Stat Validity | **DAB Score** |
|------|-----------|:-----------:|:------------:|:----------:|:-------------:|:-------------:|
| eda_001 — Income Distribution Analysis | Easy | 1.000 | 0.667 | 0.950 | 1.000 | **0.926** |
| eda_002 — Patient Records Audit | Medium | 0.667 | 0.771 | 0.970 | 0.500 | **0.700** |
| eda_003 — Confounding Detection | Hard | 1.000 | 0.825 | 0.696 | 1.000 | **0.928** |
| **Average** | | **0.889** | **0.754** | **0.872** | **0.833** | **0.851** |

> Scored with `claude-sonnet-4-6`. Token budgets calibrated from real runs (easy 20k, medium 50k, hard 30k).
> Live leaderboard: [patibandlavenkatamanideep.github.io/Data-AgentBench](https://patibandlavenkatamanideep.github.io/Data-AgentBench/)

---

## Quickstart

```bash
# 1. Install
git clone https://github.com/patibandlavenkatamanideep/dataagentbench
cd dataagentbench
pip install -e ".[dev]"

# 2. Add your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# 3. List tasks
dab list

# 4. Dry-run (no API call, validates dataset loading)
dab run eda_001 --dry-run

# 5. Live run
dab run eda_001

# 6. Score the result
dab score outputs/eda_001_<timestamp>.json

# 7. Run all tasks
dab run --all
```

---

## Tasks

| ID | Title | Difficulty | Category | Key Concepts |
|----|-------|-----------|----------|-------------|
| eda_001 | Income Distribution Analysis | Easy | EDA | Skewness, log transform |
| eda_002 | Patient Records — Missing Data & Outlier Audit | Medium | EDA | Missing rates, IQR outliers |
| eda_003 | E-Commerce Confounding Variable Detection | Hard | EDA | Simpson's Paradox, partial correlation |

---

## Scoring

Each task is scored across four independent dimensions, then combined into a weighted **DAB Score**:

| Dimension | What it measures | Typical weight |
|-----------|-----------------|:--------------:|
| **Correctness** | Ground truth match — skewness direction, missing columns, correlation sign, etc. | 40–50% |
| **Code Quality** | Vectorized ops, descriptive variable names, no raw loops, print output | 15–20% |
| **Efficiency** | Tokens and steps used vs. per-task budget | 15% |
| **Stat Validity** | Uncertainty reporting, appropriate statistical methods, correct interpretation | 15–30% |

Weights are defined per-task in the YAML. The final DAB Score is their weighted sum.

---

## Project Structure

```
dataagentbench/
├── core/
│   ├── task.py         # Pydantic schema — validates every YAML field
│   └── registry.py     # Discovers, loads, and filters tasks
├── datasets/
│   └── generators/     # Seeded, reproducible dataset generators
│       ├── income_distribution.py
│       ├── patient_records.py
│       └── ecommerce_transactions.py
├── harness/
│   ├── tools.py        # Sandboxed agent tools (run_code, get_dataframe_info, get_column_stats)
│   ├── tracer.py       # Records every step, tool call, and token count
│   ├── agent.py        # Claude agentic loop with tool use
│   └── runner.py       # Orchestrates task → dataset → agent → trace → JSON
├── scoring/
│   ├── correctness.py  # Ground truth matching with alias expansion
│   ├── code_quality.py # Static analysis of agent-generated code
│   ├── efficiency.py   # Token and step efficiency vs. budget
│   ├── stat_validity.py# Statistical rigour signals
│   └── composite.py    # Weighted DAB Score + ScoreCard
└── cli.py              # dab run / list / inspect / score
tasks/eda/              # Task YAML definitions (ground truth, scoring weights, eval config)
tests/                  # 85 offline tests — no API calls required
.github/workflows/      # CI: pytest on Python 3.10, 3.11, 3.12
```

---

## Adding a New Task

1. Create `tasks/<category>/<task_id>.yaml` following the [TASK_SPEC.md](TASK_SPEC.md) contract
2. Add a dataset generator in `dataagentbench/datasets/generators/`
3. Register the generator in `dataagentbench/datasets/__init__.py`
4. Add tests in `tests/`

The schema is validated by Pydantic on load — invalid tasks are rejected with clear error messages.

---

## Development

```bash
pip install -e ".[dev]"

# Run full test suite (offline, no API key needed)
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=dataagentbench --cov-report=term-missing
```

---

## Roadmap

- [ ] Phase 3 — GitHub Pages leaderboard (live DAB score table)
- [ ] Feature engineering tasks (feat_001–feat_005)
- [ ] Model comparison runs (GPT-4o, Gemini 1.5 Pro)
- [ ] Automated leaderboard updates via GitHub Actions

---

## Built by

[Venkata Manideep Patibandla](https://github.com/patibandlavenkatamanideep)

