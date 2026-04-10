<p align="center">
  <img src="docs/logo.svg" alt="RealDataAgentBench logo" width="700" />
</p>

<p align="center">
  <strong>Forces LLM agents to think like real statisticians — not just get the right number.</strong>
</p>

<p align="center">
  <a href="https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions"><img src="https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions/workflows/ci.yml"><img src="https://img.shields.io/badge/tests-150%20passing-brightgreen" alt="Tests"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python"></a>
  <a href="https://github.com/patibandlavenkatamanideep/RealDataAgentBench/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License"></a>
  <a href="https://patibandlavenkatamanideep.github.io/RealDataAgentBench/"><img src="https://img.shields.io/badge/leaderboard-live-brightgreen" alt="Leaderboard"></a>
</p>

> Inspired by real-world failures in LLM-generated analysis — misinterpreted A/B tests, data leakage in pipelines, causal claims drawn from observational data.

---

## TL;DR

**RealDataAgentBench (RDAB)** is an open-source benchmark for evaluating whether LLM agents can perform real-world data science workflows with statistical rigor — not just pattern-match to a correct-looking answer.

→ **23 tasks** across EDA, modeling, inference, and ML engineering  
→ **4-dimensional scoring** — correctness, code quality, efficiency, statistical validity  
→ **Tracks cost per task** to find the best model for real-world usage  
→ **10 models benchmarked** — GPT-5, GPT-4.1, GPT-4o, Claude Sonnet, Gemini 2.5, Grok, Llama, and more  

Run it locally in under 5 minutes to compare any model on real data science work.

---

## Why RDAB is different

Most data science agent benchmarks ask: *"Did the agent get the right answer?"*

RDAB asks four harder questions:

| Dimension | What it catches |
|-----------|----------------|
| **Correctness** | Did the agent find the right skewness, correlation sign, missing columns? |
| **Code Quality** | Did it use vectorized ops? Descriptive names? No raw loops? |
| **Efficiency** | Did it waste 10× the token budget to answer a simple question? |
| **Stat Validity** | Did it report uncertainty? Use appropriate tests? Avoid confusing correlation with causation? |

An agent can score **1.0 on correctness and 0.2 on statistical validity** — and that tells you something real about where it fails.

---

## Key Findings

From 163 runs across 10 models and 23 tasks:

- **Frontier models often fail statistical validity** — high correctness scores mask poor uncertainty reporting, missing confidence intervals, and causal claims drawn from observational data
- **Lower-cost models close the gap fast** — GPT-4.1 scores within 3% of GPT-5 at ~15× lower cost per task ($0.038 vs $0.596)
- **Performance varies significantly by category** — no single model dominates across EDA, modeling, and inference; the best model per category differs
- **Reasoning models don't always win** — GPT-4o outscores Claude Opus on many tasks despite being far cheaper ($0.042 vs $1.92 per task)

---

## Concrete failure example

> A model achieved **0.95 correctness but 0.28 statistical validity** on `stat_003` (Salary Gap Analysis):
> - Reported a salary gap number without controlling for confounders (education, tenure, role)
> - Drew a causal conclusion ("women are paid less *because of* gender") from an OLS coefficient
> - Omitted confidence intervals and p-value interpretation
> - Passed the numeric check — failed the statistical reasoning check

This is the gap RDAB is designed to measure.

---

## Leaderboard (10 models · 163 runs · 23 tasks)

| Rank | Model | Avg RDAB Score | Tasks Run | Avg Cost / Task |
|:----:|-------|:--------------:|:---------:|:---------------:|
| 1 | **gpt-5** | **0.812** | 23 / 23 | $0.5957 |
| 2 | gpt-4.1 | 0.791 | 23 / 23 | $0.0384 |
| 3 | gpt-4o | 0.785 | 22 / 23 | $0.0424 |
| 4 | claude-sonnet-4-6 | 0.784 | 9 / 23 | $0.4758 |
| 5 | gpt-4o-mini | 0.780 | 5 / 23 | $0.0038 |
| 6 | claude-haiku-4-5 | 0.763 | 8 / 23 | $0.0625 |
| 7 | claude-opus-4-6 | 0.751 | 17 / 23 | $1.9197 |
| 8 | llama-3.3-70b | 0.748 | 11 / 23 | $0.0023 |
| 9 | grok-3-mini | 0.626 | 23 / 23 | $0.0024 |
| 10 | gemini-2.5-flash | 0.614 | 22 / 23 | $0.0015 |

> Live leaderboard with per-task breakdowns and category filters: [patibandlavenkatamanideep.github.io/RealDataAgentBench](https://patibandlavenkatamanideep.github.io/RealDataAgentBench/)

---

## Who is this for?

- **ML / GenAI engineers** evaluating LLM agents on structured analytical tasks
- **Data teams** comparing models for analytical workflows before committing to an API contract
- **Researchers** studying statistical reasoning and validity in LLM outputs
- **Engineers** who want a production-grade benchmark they can clone, extend, and run on their own data

---

## What it looks like

### 1. Live leaderboard — 163 runs across 10 models with cost column

![Leaderboard screenshot](docs/screenshots/leaderboard.png)

> **→ [Open live leaderboard](https://patibandlavenkatamanideep.github.io/RealDataAgentBench/)** — filterable by category, sortable by score or cost.

### 2. Agent thinking trace — GPT-4o on `eda_001` (Income Distribution Analysis)

![Agent trace screenshot](docs/screenshots/agent_trace.png)

> Agent scored **0.900** on this task — autonomously called `get_dataframe_info`, `get_column_stats`, reported skewness direction, and recommended log transform.

### 3. CLI in action — `dab run eda_001 --model gpt-4o`

![Terminal screenshot](docs/screenshots/terminal_run.png)

### 4. Project folder structure

![Project structure screenshot](docs/screenshots/project_structure.png)

---

## Quickstart

```bash
# 1. Install
git clone https://github.com/patibandlavenkatamanideep/RealDataAgentBench
cd RealDataAgentBench
pip install -e ".[dev]"

# 2. Add your API keys (.env file)
cp .env.example .env
# then fill in the keys you have

# 3. List all tasks
dab list

# 4. Dry-run (validates dataset loading, no API call)
dab run eda_001 --dry-run

# 5. Live run (default: claude-sonnet-4-6)
dab run eda_001

# 6. Run with a different model
dab run eda_001 --model gpt-4o
dab run eda_001 --model gpt-4.1
dab run eda_001 --model gpt-5

# 7. Run with Groq (free tier — no credit card needed)
#    Get your key at https://console.groq.com, add GROQ_API_KEY to .env
dab run eda_001 --model groq              # llama-3.3-70b-versatile
dab run eda_001 --model llama-8b          # fastest, cheapest

# 8. Cap spend with --budget (stops run if cost exceeds limit)
dab run eda_001 --model gpt-4o --budget 0.05
dab run --all --model groq --budget 0.10

# 9. Score the result
dab score outputs/eda_001_<timestamp>.json

# 10. Run all tasks with one model
dab run --all --model gpt-4.1

# 11. See all supported models + API key status
dab models
```

---

## Tasks (23 total)

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

### ML Engineering (5)

| ID | Title | Difficulty | Key Concepts |
|----|-------|-----------|-------------|
| mod_001 | Data Leakage Detection in Model Selection | Easy | Target leakage, correlation, AUC drop |
| mod_002 | K-Fold Cross-Validation vs Single Hold-Out | Easy | CV variance, small dataset evaluation |
| mod_003 | Probability Calibration for Heart Disease Prediction | Medium | Brier score, Platt scaling, reliability |
| mod_004 | Ensemble Voting vs Individual Models | Medium | VotingClassifier, soft voting, F1 |
| mod_005 | Nested Cross-Validation for Unbiased Tuning | Hard | Selection bias, GridSearchCV, nested CV |

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
│   ├── agent.py          # Multi-model agentic loop
│   ├── providers.py      # Unified BaseProvider — Anthropic, OpenAI, Groq, xAI, Google
│   ├── pricing.py        # Single source of truth for cost per 1M tokens
│   └── runner.py         # Orchestrates task → dataset → agent → trace → JSON
├── scoring/
│   ├── correctness.py    # Ground truth matching with alias expansion
│   ├── code_quality.py   # Static analysis of agent-generated code
│   ├── efficiency.py     # Token and step efficiency vs. budget
│   ├── stat_validity.py  # Statistical rigour signals
│   └── composite.py      # Weighted RDAB Score + ScoreCard
└── cli.py                # dab run / list / inspect / score / models
tasks/
├── eda/                  # 3 tasks
├── feature_engineering/  # 5 tasks
├── modeling/             # 5 tasks
├── statistical_inference/ # 5 tasks
└── ml_engineering/       # 5 tasks (leakage, CV, calibration, ensemble, nested CV)
tests/                    # 150 offline tests — no API calls required
scripts/
└── build_leaderboard.py  # Aggregates outputs/ → docs/results.json
docs/
└── index.html            # GitHub Pages leaderboard (auto-rebuilt by CI)
.github/workflows/        # CI: pytest on Python 3.10–3.13 + leaderboard rebuild
```

---

## Adding a New Task

1. Create `tasks/<category>/<task_id>.yaml` following [TASK_SPEC.md](TASK_SPEC.md)
2. Add a seeded generator in `realdataagentbench/datasets/generators/`
3. Register it in `realdataagentbench/datasets/__init__.py`
4. Add tests in `tests/`
5. Run `pytest tests/ -v` — all tests must pass before opening a PR

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

- [x] Phase 1 — Task schema, harness, scoring engine, 150 tests
- [x] Phase 2 — 8 tasks across EDA + Feature Engineering
- [x] Phase 3 — GitHub Pages leaderboard with auto-rebuild CI
- [x] Phase 4 — Multi-model support (GPT-4o, GPT-4o-mini, Claude Haiku, Claude Sonnet)
- [x] Phase 5 — 23 tasks across 5 categories including ML Engineering (leakage, calibration, nested CV)
- [x] Phase 6 — Cost per run ($) in leaderboard; category filters; 150 tests
- [x] Phase 7 — 10 models: GPT-5, GPT-4.1, Grok-3-mini, Gemini 2.5 Flash, Llama 3.3 via Groq; 163 total runs
- [ ] 30+ tasks (visualization, NLP, time series categories)
- [ ] Human baseline scores
- [ ] arXiv paper

---

## For Companies — Choose the Right Model

RDAB helps teams identify the most cost-effective model for statistically sound data science workflows — before committing to an API contract.

**Real numbers from 163 runs across 10 models and 23 tasks:**

| Model | Avg RDAB Score | Avg Cost / Task |
|-------|:--------------:|:---------------:|
| **gpt-5** | **0.812** | $0.5957 |
| gpt-4.1 | 0.791 | $0.0384 |
| gpt-4o | 0.785 | $0.0424 |
| gpt-4o-mini | 0.780 | $0.0038 |
| grok-3-mini | 0.626 | $0.0024 |
| gemini-2.5-flash | 0.614 | $0.0015 |

GPT-5 leads — but GPT-4.1 scores within 3% at **15× lower cost**. GPT-4o-mini scores within 4% of GPT-5 at **150× lower cost**. For a team running hundreds of analysis tasks a week, that compounds fast.

> **Bottom line:** The best model for your use case isn't always the most expensive one. Run RDAB on your own data, check the cost column, and choose accordingly.

---

## Built by

[Venkata Manideep Patibandla](https://github.com/patibandlavenkatamanideep)  
Built to demonstrate production-grade ML engineering and statistically honest LLM evaluation.
