# RealDataAgentBench

[![CI](https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions/workflows/ci.yml/badge.svg)](https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions)
[![Tests](https://img.shields.io/badge/tests-120%2B%20passing-brightgreen)](https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](https://github.com/patibandlavenkatamanideep/RealDataAgentBench/blob/main/LICENSE)

> **The benchmark that checks if LLM agents do real data science — not just get the right number.**

RealDataAgentBench (RDAB) evaluates LLM agents on statistically rigorous data science tasks: exploratory analysis, feature engineering, confounding detection, and imbalanced classification. Unlike most benchmarks, RDAB scores four independent dimensions — correctness, code quality, efficiency, and statistical validity — so you know *why* an agent succeeded or failed.

---

## Leaderboard (2026-04-09 · 6 shared tasks + 2 GPT-4o only)

| Task | Difficulty | claude-sonnet-4-6 | gpt-4o |
|------|-----------|:-----------------:|:------:|
| eda_001 — Income Distribution | Easy | **0.926** | 0.900 |
| eda_002 — Patient Records Audit | Medium | 0.700 | 0.750 |
| eda_003 — Confounding Detection | Hard | **0.928** | 0.830 |
| feat_001 — House Price Features | Easy | **0.749** | 0.657 |
| feat_002 — Employee Attrition | Medium | **0.797** | 0.711 |
| feat_003 — Retail Datetime Features | Medium | 0.727 | **0.837** |
| feat_004 — Credit Risk Selection | Hard | — *(pending)* | **0.768** |
| feat_005 — Fraud Imbalance | Hard | — *(pending)* | **0.802** |
| **Average (6 shared tasks)** | | **0.804** | 0.781 |

> Live leaderboard: [patibandlavenkatamanideep.github.io/RealDataAgentBench](https://patibandlavenkatamanideep.github.io/RealDataAgentBench/)

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

# 2. Add your API keys (.env file)
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
echo "OPENAI_API_KEY=sk-..."       >> .env

# 3. List all tasks
dab list

# 4. Dry-run (validates dataset loading, no API call)
dab run eda_001 --dry-run

# 5. Live run (default: claude-sonnet-4-6)
dab run eda_001

# 6. Run with a different model
dab run eda_001 --model gpt-4o
dab run eda_001 --model gpt-4o-mini
dab run eda_001 --model haiku

# 7. Score the result
dab score outputs/eda_001_<timestamp>.json

# 8. Run all tasks with one model
dab run --all --model gpt-4o-mini

# 9. See all supported models + API key status
dab models
```

---

## Tasks (18 total)

### Exploratory Data Analysis (3)

| ID | Title | Difficulty | Key Concepts |
|----|-------|-----------|-------------|
| eda_001 | Income Distribution Analysis | Easy | Skewness, log transform |
| eda_002 | Patient Records — Missing Data & Outlier Audit | Medium | Missing rates, IQR outliers |
| eda_003 | E-Commerce Confounding Variable Detection | Hard | Simpson's Paradox, partial correlation |

### Feature Engineering (5)

| ID | Title | Difficulty | Key Concepts |
|----|-------|-----------|-------------|
| feat_001 | Polynomial Feature Engineering for House Prices | Easy | Interaction terms, R² comparison |
| feat_002 | Categorical Encoding & Feature Selection | Medium | One-hot encoding, RF feature importance |
| feat_003 | Datetime Feature Extraction for Retail Sales | Medium | Datetime parsing, weekend effect |
| feat_004 | Feature Selection Pipeline for Credit Risk | Hard | Multicollinearity, ROC-AUC, Gradient Boosting |
| feat_005 | Feature Engineering for Imbalanced Fraud Detection | Hard | SMOTE, F1-score, class imbalance |

### Modeling (5)

| ID | Title | Difficulty | Key Concepts |
|----|-------|-----------|-------------|
| model_001 | Logistic Regression for Diabetes Prediction | Easy | Coefficients, ROC-AUC, feature ranking |
| model_002 | Random Forest for Wine Quality | Medium | Feature importance, CV tuning, F1 |
| model_003 | Ridge vs Lasso for Student Performance | Medium | Regularization, RMSE, sparsity |
| model_004 | Gradient Boosting for Customer Churn | Hard | Confusion matrix, CV AUC, model comparison |
| model_005 | Multi-Model Regression for Energy Consumption | Hard | RMSE comparison, CV R², feature importance |

### Statistical Inference (5)

| ID | Title | Difficulty | Key Concepts |
|----|-------|-----------|-------------|
| stat_001 | A/B Test — Conversion Rate Experiment | Easy | z-test, confidence intervals, lift |
| stat_002 | Clinical Trial — Drug Efficacy Test | Medium | t-test, Cohen's d, baseline balance |
| stat_003 | Salary Gap Analysis — Controlling for Confounders | Hard | OLS regression, pay gap, confounding |
| stat_004 | Time Series Decomposition — Sales Trend & Seasonality | Medium | Decomposition, trend, seasonality |
| stat_005 | Statistical Process Control — Manufacturing Defects | Hard | Cp index, drift detection, chi-squared |

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
realdataagentbench/
├── core/
│   ├── task.py           # Pydantic schema — validates every YAML field
│   └── registry.py       # Discovers, loads, and filters tasks
├── datasets/
│   └── generators/       # Seeded, reproducible dataset generators (18 datasets)
├── harness/
│   ├── tools.py          # Sandboxed agent tools (run_code, get_dataframe_info, get_column_stats)
│   ├── tracer.py         # Records every step, tool call, and token count
│   ├── agent.py          # Multi-model agentic loop (Claude, GPT-4o, GPT-4o-mini, Haiku)
│   ├── providers.py      # Unified BaseProvider for Anthropic + OpenAI
│   └── runner.py         # Orchestrates task → dataset → agent → trace → JSON
├── scoring/
│   ├── correctness.py    # Ground truth matching with alias expansion
│   ├── code_quality.py   # Static analysis of agent-generated code
│   ├── efficiency.py     # Token and step efficiency vs. budget
│   ├── stat_validity.py  # Statistical rigour signals
│   └── composite.py      # Weighted RDAB Score + ScoreCard
└── cli.py                # dab run / list / inspect / score / models
tasks/
├── eda/                  # 3 EDA tasks
├── feature_engineering/  # 5 feature engineering tasks
├── modeling/             # 5 modeling tasks
└── statistical_inference/ # 5 statistical inference tasks
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
2. Add a seeded generator in `realdataagentbench/datasets/generators/`
3. Register it in `realdataagentbench/datasets/__init__.py`
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
pytest tests/ --cov=realdataagentbench --cov-report=term-missing
```

---

## Roadmap

- [x] Phase 1 — Task schema, harness, scoring engine, 120 tests
- [x] Phase 2 — 8 tasks across EDA + Feature Engineering
- [x] Phase 3 — GitHub Pages leaderboard with auto-rebuild CI
- [x] Phase 4 — Multi-model support (GPT-4o, GPT-4o-mini, Claude Haiku, Claude Sonnet)
- [x] Phase 5 — 18 tasks across 4 categories (EDA, Feature Engineering, Modeling, Statistical Inference)
- [ ] 30+ tasks (visualization, NLP, time series categories)
- [ ] Human baseline scores
- [ ] arXiv paper

---

## Built by

[Venkata Manideep Patibandla](https://github.com/patibandlavenkatamanideep) — MS CS, University at Buffalo.
Built to demonstrate production-grade ML engineering and statistically honest LLM evaluation.
