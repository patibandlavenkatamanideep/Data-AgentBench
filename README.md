# RealDataAgentBench

[![CI](https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions/workflows/ci.yml/badge.svg)](https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions)
[![Tests](https://img.shields.io/badge/tests-120%2B%20passing-brightgreen)](https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](https://github.com/patibandlavenkatamanideep/RealDataAgentBench/blob/main/LICENSE)
[![Leaderboard](https://img.shields.io/badge/leaderboard-live-brightgreen)](https://patibandlavenkatamanideep.github.io/RealDataAgentBench/)

> **The benchmark that forces LLM agents to think like real statisticians — not just get the right number.**

This benchmark forces LLM agents to think like real statisticians, not just copy answers. It measures four things most benchmarks ignore: whether the agent's code is production-quality, whether it uses the right statistical methods, whether it works efficiently, and whether it actually gets the right answer.

- **18 tasks** across EDA, Feature Engineering, Modeling, and Statistical Inference
- **4 models benchmarked**: Claude Sonnet, GPT-4o, GPT-4o-mini, Claude Haiku — with real scores from real API runs
- **4-dimension scoring**: Correctness · Code Quality · Efficiency · Statistical Validity — so you know exactly *where* each model wins or fails

---

## Leaderboard (38 runs · 4 models · 18 tasks)

| Model | Avg RDAB Score | Tasks Run |
|-------|:--------------:|:---------:|
| **claude-sonnet-4-6** | **0.799** | 8 |
| gpt-4o-mini | 0.780 | 5 |
| gpt-4o | 0.779 | 17 |
| claude-haiku | 0.763 | 8 |

> Live leaderboard with per-task breakdowns: [patibandlavenkatamanideep.github.io/RealDataAgentBench](https://patibandlavenkatamanideep.github.io/RealDataAgentBench/)

---

## What it looks like

### 1. Live leaderboard table (GitHub Pages)

```
┌─────────────────────┬───────────┬───────────────────┬────────────┬────────────────┐
│ Task                │ Difficulty│ claude-sonnet-4-6 │  gpt-4o    │  claude-haiku  │
├─────────────────────┼───────────┼───────────────────┼────────────┼────────────────┤
│ eda_001 Income Dist │ Easy      │      0.933        │   0.900    │     0.920      │
│ eda_002 Patient Recs│ Medium    │      0.700        │   0.750    │     0.625      │
│ eda_003 Confounding │ Hard      │      0.944        │   0.830    │     0.831      │
│ feat_001 House Prices│ Easy     │      0.776        │   0.660    │     0.747      │
│ feat_002 Attrition  │ Medium    │      0.797        │   0.711    │     0.653      │
│ feat_003 Retail Sales│ Medium   │      0.727        │   0.837    │     0.855      │
│ feat_004 Credit Risk│ Hard      │      0.777        │   0.768    │     0.745      │
│ feat_005 Fraud Imbal│ Hard      │      0.742        │   0.802    │     0.728      │
├─────────────────────┼───────────┼───────────────────┼────────────┼────────────────┤
│ Average             │           │    **0.799**       │   0.779    │     0.763      │
└─────────────────────┴───────────┴───────────────────┴────────────┴────────────────┘
```

### 2. Agent thinking trace — GPT-4o on `stat_001` (A/B test analysis)

```python
# Step 4 — agent writes and runs this code autonomously
grouped = df.groupby('group')['converted'].mean()
control_rate   = grouped['control']    # 0.0820
treatment_rate = grouped['treatment']  # 0.1220

absolute_lift = treatment_rate - control_rate   # +0.040
relative_lift = absolute_lift / control_rate    # +48.8%

from scipy import stats
control_n    = len(df[df['group'] == 'control'])
treatment_n  = len(df[df['group'] == 'treatment'])
z, p = stats.proportions_ztest(
    [int(treatment_rate * treatment_n), int(control_rate * control_n)],
    [treatment_n, control_n]
)
print(f"z={z:.3f}  p={p:.4f}  significant={'YES' if p < 0.05 else 'NO'}")
# → z=2.847  p=0.0044  significant=YES
```

> Agent scored **0.912** on this task — reported lift, z-test, CI, and revenue per user.

### 3. CLI in action

```
$ dab run eda_001 --model gpt-4o

Running eda_001 (model=gpt-4o, dry_run=False)

Complete.
  Steps: 9  |  Tokens: 11432

$ dab score outputs/eda_001_20260409T094920.json

              ScoreCard — eda_001
┏━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┓
┃ Dimension     ┃ Score ┃ Weight ┃ Contribution ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━┩
│ Correctness   │ 1.000 │   0.50 │        0.500 │
│ Code Quality  │ 0.750 │   0.20 │        0.150 │
│ Efficiency    │ 1.000 │   0.15 │        0.150 │
│ Stat Validity │ 1.000 │   0.15 │        0.150 │
│ RDAB Score    │ 0.950 │   1.00 │        0.950 │
└───────────────┴───────┴────────┴──────────────┘
```

### 4. Project structure

```
RealDataAgentBench/
├── realdataagentbench/
│   ├── core/              # Task schema (Pydantic) + registry
│   ├── datasets/
│   │   └── generators/    # 18 seeded, reproducible generators
│   ├── harness/           # Agent loop + multi-model providers
│   │   ├── providers.py   # Claude, GPT-4o, GPT-4o-mini, Haiku
│   │   └── tools.py       # run_code, get_dataframe_info, get_column_stats
│   └── scoring/           # Correctness · Code Quality · Efficiency · Stat Validity
├── tasks/
│   ├── eda/               # 3 tasks
│   ├── feature_engineering/ # 5 tasks
│   ├── modeling/          # 5 tasks
│   └── statistical_inference/ # 5 tasks
├── tests/                 # 120 offline tests — no API key needed
├── scripts/
│   └── build_leaderboard.py
└── docs/                  # GitHub Pages leaderboard (auto-rebuilt by CI)
```

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
