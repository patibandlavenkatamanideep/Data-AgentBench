# RealDataAgentBench

[![CI](https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions/workflows/ci.yml/badge.svg)](https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions)
[![Tests](https://img.shields.io/badge/tests-120%20passing-brightgreen)](https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](https://github.com/patibandlavenkatamanideep/RealDataAgentBench/blob/main/LICENSE)

> **The benchmark that checks if LLM agents do real data science — not just get the right number.**

RealDataAgentBench (RDAB) evaluates LLM agents on statistically rigorous data science tasks: exploratory analysis, feature engineering, confounding detection, and imbalanced classification. Unlike most benchmarks, RDAB scores four independent dimensions — correctness, code quality, efficiency, and statistical validity — so you know *why* an agent succeeded or failed.

---

## Leaderboard (claude-sonnet-4-6 · 2026-04-09)

| Task | Difficulty | Correctness | Code Quality | Efficiency | Stat Validity | **RDAB Score** |
|------|-----------|:-----------:|:------------:|:----------:|:-------------:|:--------------:|
| eda_001 — Income Distribution | Easy | 1.000 | 0.667 | 0.950 | 1.000 | **0.926** |
| eda_002 — Patient Records Audit | Medium | 0.667 | 0.771 | 0.970 | 0.500 | **0.700** |
| eda_003 — Confounding Detection | Hard | 1.000 | 0.825 | 0.696 | 1.000 | **0.928** |
| feat_001 — House Price Features | Easy | 1.000 | 0.756 | 0.150 | 0.500 | **0.749** |
| feat_002 — Employee Attrition | Medium | 1.000 | 0.733 | 1.000 | 0.250 | **0.797** |
| **Average (claude-sonnet-4-6)** | | **0.933** | **0.750** | **0.753** | **0.650** | **0.820** |

> More models coming. Live leaderboard: [patibandlavenkatamanideep.github.io/RealDataAgentBench](https://patibandlavenkatamanideep.github.io/RealDataAgentBench/)

---

## Why RDAB is different

Most data science agent benchmarks ask: *"Did the agent get the right answer?"*

RDAB asks four harder questions:

| Dimension | What it catches |
|-----------|----------------|
| **Correctness** | Did the agent find the right skewness, correlation sign, missing columns? |
| **Code Quality** | Did it use vectorized ops? Descriptive names? No raw loops? |
| **Efficiency** | Did it waste 10x the token budget to answer a simple question? |
| **Stat Validity** | Did it report uncertainty? Use appropriate tests? Avoid confusing correlation with causation? |

An agent can score 1.0 on correctness and 0.2 on statistical validity — and that tells you something real about where it fails.

---

## Quickstart

```bash
# 1. Install
git clone https://github.com/patibandlavenkatamanideep/RealDataAgentBench
cd RealDataAgentBench
pip install -e ".[dev]"

# 2. Add your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# 3. List all tasks
dab list

# 4. Dry-run (validates dataset loading, no API call)
dab run eda_001 --dry-run

# 5. Live run
dab run eda_001

# 6. Score the result
dab score outputs/eda_001_<timestamp>.json

# 7. Run all tasks
dab run --all
```

---

## Tasks (8 total)

| ID | Title | Difficulty | Category | Key Concepts |
|----|-------|-----------|----------|-------------|
| eda_001 | Income Distribution Analysis | Easy | EDA | Skewness, log transform |
| eda_002 | Patient Records — Missing Data & Outlier Audit | Medium | EDA | Missing rates, IQR outliers |
| eda_003 | E-Commerce Confounding Variable Detection | Hard | EDA | Simpson's Paradox, partial correlation |
| feat_001 | Polynomial Feature Engineering for House Prices | Easy | Feature Engineering | Interaction terms, R² comparison |
| feat_002 | Categorical Encoding & Feature Selection | Medium | Feature Engineering | One-hot encoding, RF feature importance |
| feat_003 | Datetime Feature Extraction for Retail Sales | Medium | Feature Engineering | Datetime parsing, weekend effect |
| feat_004 | Feature Selection Pipeline for Credit Risk | Hard | Feature Engineering | Multicollinearity, ROC-AUC, Gradient Boosting |
| feat_005 | Feature Engineering for Imbalanced Fraud Detection | Hard | Feature Engineering | SMOTE, F1-score, class imbalance |

---

## Scoring

Each task is scored across four independent dimensions, then combined into a weighted **RDAB Score**:

| Dimension | What it measures | Typical weight |
|-----------|-----------------|:--------------:|
| **Correctness** | Ground truth match — skewness direction, missing columns, correlation sign, etc. | 40–50% |
| **Code Quality** | Vectorized ops, descriptive variable names, no raw loops, print output | 15–20% |
| **Efficiency** | Tokens and steps used vs. per-task budget | 15% |
| **Stat Validity** | Uncertainty reporting, appropriate statistical methods, correct interpretation | 15–30% |

Weights are defined per-task in the YAML. The final RDAB Score is their weighted sum.

---

## Project Structure

```
dataagentbench/
├── core/
│   ├── task.py           # Pydantic schema — validates every YAML field
│   └── registry.py       # Discovers, loads, and filters tasks
├── datasets/
│   └── generators/       # Seeded, reproducible dataset generators (8 datasets)
├── harness/
│   ├── tools.py          # Sandboxed agent tools (run_code, get_dataframe_info, get_column_stats)
│   ├── tracer.py         # Records every step, tool call, and token count
│   ├── agent.py          # Claude agentic loop with tool use
│   └── runner.py         # Orchestrates task → dataset → agent → trace → JSON
├── scoring/
│   ├── correctness.py    # Ground truth matching with alias expansion
│   ├── code_quality.py   # Static analysis of agent-generated code
│   ├── efficiency.py     # Token and step efficiency vs. budget
│   ├── stat_validity.py  # Statistical rigour signals
│   └── composite.py      # Weighted RDAB Score + ScoreCard
└── cli.py                # dab run / list / inspect / score
tasks/
├── eda/                  # 3 EDA tasks
└── feature_engineering/  # 5 feature engineering tasks
tests/                    # 120 offline tests — no API calls required
scripts/
└── build_leaderboard.py  # Aggregates outputs/ → docs/results.json
docs/
└── index.html            # GitHub Pages leaderboard (auto-rebuilt by CI)
.github/workflows/        # CI: pytest on Python 3.10/3.11/3.12 + leaderboard rebuild
```

---

## Adding a New Task

1. Create `tasks/<category>/<task_id>.yaml` following [TASK_SPEC.md](TASK_SPEC.md)
2. Add a seeded generator in `dataagentbench/datasets/generators/`
3. Register it in `dataagentbench/datasets/__init__.py`
4. Add tests in `tests/`
5. Run `pytest tests/ -v` — all 120 must pass before opening a PR

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

---

## Development

```bash
pip install -e ".[dev]"

# Full test suite (offline, no API key needed)
pytest tests/ -v

# With coverage
pytest tests/ --cov=dataagentbench --cov-report=term-missing
```

---

## Roadmap

- [x] Phase 1 — Task schema, harness, scoring engine, 120 tests
- [x] Phase 2 — 8 tasks across EDA + Feature Engineering
- [x] Phase 3 — GitHub Pages leaderboard with auto-rebuild CI
- [ ] Multi-model support (GPT-4o, Gemini 1.5 Pro, Llama-3)
- [ ] 30+ tasks (modeling, visualization, inference categories)
- [ ] Human baseline scores
- [ ] arXiv paper

---

## Built by

[Venkata Manideep Patibandla](https://github.com/patibandlavenkatamanideep) — MS CS, University at Buffalo.
Built to demonstrate production-grade ML engineering and statistically honest LLM evaluation.
