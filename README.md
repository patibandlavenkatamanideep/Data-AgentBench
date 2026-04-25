<p align="center">
  <img src="docs/logo.svg" alt="RealDataAgentBench logo" width="700" />
</p>

<p align="center">
  <strong>Most LLMs get the right answer. RDAB checks if they did it the right way.</strong>
</p>

<p align="center">
  <a href="https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions"><img src="https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions/workflows/ci.yml"><img src="https://img.shields.io/badge/tests-168%20passing-brightgreen" alt="Tests"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python"></a>
  <a href="https://github.com/patibandlavenkatamanideep/RealDataAgentBench/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License"></a>
  <a href="https://patibandlavenkatamanideep.github.io/RealDataAgentBench/"><img src="https://img.shields.io/badge/leaderboard-live-brightgreen" alt="Leaderboard"></a>
  <a href="SCORING_SPEC.md"><img src="https://img.shields.io/badge/scoring-fully%20transparent-blue" alt="Scoring spec"></a>
  <a href="tasks/"><img src="https://img.shields.io/badge/tasks-39%20(6%20real%20data)-orange" alt="Tasks"></a>
</p>

> **Frontier models score 0.83–1.00 on correctness across data science tasks.**  
> **Stat-validity ranges from 0.45 (feature engineering) to 0.87 (EDA and stat inference) — models know when statistical language is expected but not when it's warranted.**  
> The gap is largest where it's least visible: modeling and feature engineering tasks where models report outputs but skip uncertainty quantification.

---

## What RDAB is

**RealDataAgentBench (RDAB)** is an open-source benchmark that evaluates whether LLM agents do data science work that is not just *correct* but *statistically sound* — reporting uncertainty, using appropriate tests, and avoiding causal overreach.

Built with transparent scoring specs, reproducible datasets, real-world data tasks, and a pre-registered controlled experiment.

→ **39 tasks** — 33 synthetic + **6 real-data tasks** (UCI Breast Cancer, Iris, Diabetes, Wine — real clinical and scientific datasets)  
→ **4-dimensional scoring** — correctness, code quality, efficiency, statistical validity  
→ **12 models at full coverage** — current leaderboard reflects 326 runs on the original 23-task set; tasks 24–39 are defined but not yet run across all models  
→ **[Fully transparent scoring](SCORING_SPEC.md)** — every formula, regex, threshold, and known limitation documented; independently verifiable without reading source code  
→ **[Pre-registered experiment](docs/experiments/uncertainty_uplift_design.md)** — controlled test of uncertainty prompting uplift, committed before execution

Clone it, add your API key, and run any model in under 5 minutes.

---

## Why This Benchmark Exists

Most data science agent benchmarks ask one question: *"Did the agent get the right answer?"*

That is not enough. A model that reports `AUC = 0.84` without a confidence interval, computes the right feature importances without noting rank instability, or runs a regression without checking whether the design supports a causal claim — that model is **not safe to deploy** in analytical workflows where decisions are made on its outputs.

RDAB was built to measure the gap between *numerically correct* and *analytically trustworthy*. The four dimensions:

| Dimension | What it catches |
|-----------|----------------|
| **Correctness** | Did the agent find the right skewness, correlation sign, missing columns? |
| **Code Quality** | Did it use vectorized ops? Descriptive names? No raw loops? |
| **Efficiency** | Did it waste 10× the token budget to answer a simple question? |
| **Stat Validity** | Did it report uncertainty? Use appropriate tests? Avoid confusing correlation with causation? |

An agent can score **1.0 on correctness and 0.25 on statistical validity on the same task** — and that delta tells you exactly where it fails in production.

---

## Business Impact — Why Statistical Validity Matters at Scale

The correctness–validity gap is not an academic curiosity. In production data science workflows, it has direct consequences:

**If a model reports feature importances without stability notes:**
A data team ranks features incorrectly because ranks 2 and 3 are within noise — and ships a model that drops a relevant predictor. The model is numerically "correct" at the time of analysis but operationally wrong.

**If a model reports AUC = 0.84 without a confidence interval on a 150-sample test set:**
A 95% CI on 150 samples is approximately ±0.08. An AUC of 0.84 could plausibly be 0.76 — which changes the go/no-go decision on model deployment.

**If a model reports a salary gap without controlling for confounders:**
A 22% pay gap finding drives an HR investigation. Controlled for job level and tenure, the gap is 3.1% — still worth addressing, but the response is very different. The model correctly computed the raw gap. It failed to note what the raw number means.

**Across a team running 500 analyses per month:**
If 60% of outputs lack appropriate uncertainty bounds (consistent with RDAB's finding that modeling and feature engineering tasks average 0.45–0.51 stat-validity while correctness exceeds 0.83), that is 300 analysis outputs per month where a decision-maker has no basis for knowing how much to trust the number. At scale, this degrades the value of agentic data workflows.

RDAB gives you a number for this risk before you commit to a provider.

---

## Who This Is For

| Role | How RDAB helps |
|------|---------------|
| **ML / GenAI engineers** | Evaluate agent candidates on structured analytical tasks before deploying to a pipeline |
| **Data science leads** | Compare models on the dimensions that matter for your team's workflow — not just accuracy |
| **AI researchers** | Study statistical reasoning and validity in LLM outputs with a reproducible, transparent framework |
| **Hiring managers / technical evaluators** | A live benchmark with published methodology and real numbers is a concrete portfolio signal |

---

## RDAB vs Existing Benchmarks

The table below compares design features. **No head-to-head empirical runs have been executed across benchmarks** — these are design-intent differences, not validated performance comparisons.

| Feature | **RDAB** | AgentBench | DA-Code | ScienceAgentBench | HELM |
|---------|:--------:|:----------:|:-------:|:-----------------:|:----:|
| Statistical validity dimension | ✓ | ✗ | ✗ | Partial | ✗ |
| Seeded reproducible datasets | ✓ | ✓ | ✗ | ✗ | ✓ |
| Per-run cost tracking | ✓ | ✗ | ✗ | ✗ | ✗ |
| Fully local (no external download) | ✓ | ✗ | ✗ | ✗ | ✗ |
| Category-aware scoring | ✓ | ✗ | ✗ | Partial | Partial |
| LLM-as-judge calibration | ✓ | ✗ | ✗ | ✗ | ✗ |
| 95% CI on leaderboard | ✓ | ✗ | ✗ | ✗ | ✗ |
| Open source harness | ✓ | ✓ | ✓ | ✗ | ✓ |
| Real-data tasks | ✓ | ✗ | ✓ | ✓ | ✗ |

**The core differentiator:** RDAB measures *how* an agent reasons, not just *what* it outputs. A model that reports AUC = 0.84 without a confidence interval scores well on correctness-only benchmarks but poorly on RDAB's statistical validity dimension — capturing a class of reasoning failures that existing benchmarks don't measure.

---

## Why RDAB is credible

- **Every score is independently reproducible.** [SCORING_SPEC.md](SCORING_SPEC.md) documents every formula, regex, threshold, and known limitation. No source code reading required.
- **Known limitations are disclosed.** The stat-validity scorer is lexical — it detects vocabulary, not reasoning quality. A calibration script (`scripts/calibrate_stat_validity.py`) measures agreement between the lexical scorer and an LLM judge, giving a quantified bound on the gap.
- **Partial-coverage models are excluded from ranking.** Any model with <80% task coverage is flagged and excluded from the ranked leaderboard. Their scores are not averaged against different task sets. Currently all 12 models have completed the original 23-task set at 100% coverage.
- **Datasets are real where it matters.** Six tasks use publicly licensed real-world datasets (UCI Breast Cancer, Iris, Diabetes, Wine) with ground truths computed independently from the data.
- **The key experiment is pre-registered.** The uncertainty prompting uplift experiment has committed outcome interpretations before any runs are executed.

---

## Benchmark Methodology

### Data modes

**`dab run <task> --dry-run`** — Validates that the dataset generator loads correctly and the task YAML parses without error. No API call is made. No model output is produced. Use this to verify your environment.

**`dab run <task>`** — Live mode. Makes a real API call to the model provider. The agent receives a sandboxed Python execution environment with the seeded dataset pre-loaded, and iterates through tool calls until it produces a final answer or hits the step/timeout limit. Every tool call, token count, and final answer is recorded in the trace JSON.

There is no "simulation mode" or pre-cached response replay. Every score in the leaderboard is from a live model run with a real API call. The trace files in `outputs/` are the raw records.

### Data handling

RDAB uses seeded synthetic generators and publicly licensed datasets (UCI/sklearn). All datasets are generated or loaded locally at runtime — no user-uploaded data is involved. Trace outputs are written to your local `outputs/` directory. API calls to model providers (OpenAI, Anthropic, etc.) are governed by those providers' own privacy policies.

Synthetic datasets are generated from seeded NumPy/Pandas operations — they do not contain or approximate any real person's data. Real-data tasks use publicly licensed datasets (UCI/sklearn) that are already in the public domain or licensed for open use (see [SCORING_SPEC.md §11](SCORING_SPEC.md)).

### Synthetic data: limitations and transparency

33 of 39 tasks use seeded synthetic generators. Limitations:

- **Distribution artifacts:** Synthetic distributions are idealized (e.g., log-normal income). Real-world data is messier and harder to analyze correctly.
- **No ground-truth validation against reality:** The "correct" skewness or correlation is defined by the generator — not by any external authority.
- **Memorization risk:** A model could in principle achieve perfect correctness on synthetic tasks if it memorized the generator's output patterns from training data. The 6 real-data tasks (using independently verifiable UCI/sklearn datasets) are not subject to this risk.

These limitations are documented. The stat-validity gap (modeling and feature engineering tasks averaging 0.45–0.51 despite correctness ≥ 0.83) is not a synthetic-data artifact — it appears on both synthetic and real-data tasks, and the scoring rubric is identical across both.

### Scoring independence

The four scorers (`correctness`, `code_quality`, `efficiency`, `stat_validity`) each run independently on the trace JSON. They do not share state. The composite RDAB Score is a weighted average of their outputs using per-task weights defined in the task YAML.

Ground truth for synthetic tasks is pre-computed at task-creation time and stored in the YAML `ground_truth:` block. Ground truth for real-data tasks is computed from the actual sklearn dataset and is independently verifiable. Neither requires reading RDAB source code.

---

## 🔍 Key Findings

From 326 runs across 12 models and 23 tasks — patterns observed in actual benchmark output, not hypothetical.

---

> **💡 Insight 1: Statistical validity gaps are category-dependent, not uniform**
>
> Stat-validity scores vary sharply by task category: **EDA = 0.87, stat inference = 0.86, ML engineering = 0.59, modeling = 0.51, feature engineering = 0.45**. Models do well when the task name signals that statistics are expected. They underperform when statistical rigour is appropriate but not cued — such as reporting uncertainty on feature importances or adding confidence intervals to model evaluation metrics.
>
> Notably, Claude models lead on stat-validity (Sonnet: 0.71, Haiku: 0.70) while trailing GPT models on overall RDAB score — suggesting the dimensions measure genuinely different capabilities.
>
> The scorer-to-scorer correlation analysis (`scripts/dimension_correlations.py`) shows correctness × stat-validity at r = 0.48, with all other dimension pairs below r = 0.25 — confirming the four dimensions capture largely independent signals.
>
> **→ Aggregate leaderboard position masks category-level capability gaps.**

---

> **💡 Insight 2: No single model dominates across categories**
>
> | Category | Best Model | Avg RDAB |
> |----------|-----------|:--------:|
> | EDA | gpt-4.1 | 0.890 |
> | Feature Engineering | gpt-4.1 | 0.829 |
> | Statistical Inference | gpt-4.1 | **0.917** |
> | ML Engineering | gpt-4o | 0.805 |
> | Modeling | llama-3.3-70b | **0.765** |
>
> Llama 3.3-70b (free via Groq) outperforms GPT-5, GPT-4.1, and all Claude models on modeling — driven by more methodical, step-by-step code structure.
>
> **→ Category matters. Benchmark before you commit to a provider.**

---

> **💡 Insight 3: Claude models massively over-spend tokens**
>
> Claude Haiku: **608,861 tokens** on `feat_005` (efficiency = 0.13). Claude Sonnet: **375,920 tokens** on `feat_004`. GPT-4.1 and Llama completed the same tasks in under 30,000 tokens with higher correctness. The Anthropic models explore more — but conclude less efficiently.
>
> **→ Token count is a capability signal, not just a cost one.**

---

> **💡 Insight 4: grok-3-mini has a hard sklearn blind spot**
>
> Grok-3-mini scores **correctness = 0.00** on 7 of 23 tasks — every one involving sklearn. The model retried failed imports and returned empty answers rather than adapting to the pre-injected namespace. Its 0.626 overall score hides a bimodal distribution: near-perfect on EDA, zero on anything requiring a trained model.
>
> **→ Aggregate scores can mask catastrophic failure on task subsets.**

---

> **💡 Insight 5: GPT-4.1 is the most cost-efficient serious contender**
>
> GPT-4.1 leads EDA, Feature Engineering, and Statistical Inference outright — at **$0.038/task** vs GPT-5's $0.596 (single-run estimates; cost varies with task complexity and model verbosity — run multiple times for reliable cost comparisons). That's approximately 15× cheaper for comparable output quality.
>
> **→ The best model for your use case is rarely the most expensive one.**

---

---

## Statistical Validity Experiment (pre-registered)

The category-level stat-validity gap is RDAB's headline result — feature engineering and modeling tasks score 0.45–0.51 even when correctness is 0.83+. Before claiming this as a model capability gap, two alternative explanations need empirical testing:

1. **Scorer artifact hypothesis:** The gap is entirely explained by the lexical scorer's pattern list. Better prompting to use the right vocabulary closes it.
2. **Prompting gap hypothesis:** Models can produce statistically rigorous outputs when asked explicitly — the gap is real but addressable.

We have **pre-registered** a controlled experiment (45 runs, ~$12.67 total) to test hypothesis 2:

| Variant | Prompt change | Purpose |
|---|---|---|
| **V0 (baseline)** | Current production prompt | Control |
| **V1 (uncertainty)** | + explicit CI/SE/p-value instruction | Tests whether direct instruction closes the gap |
| **V2 (statistician)** | Change persona to "statistician" + structured output rules | Tests whether role-framing changes output style |

**Tasks:** 5 non-EDA tasks with lowest mean stat_validity and correctness ≥ 0.60  
**Models:** GPT-5, GPT-4.1, Llama 3.3-70B (frontier, mid-tier, small)  
**Primary outcome:** Δstat_validity(V1/V2 vs V0) per model, with correctness guard

The experiment design is fully pre-registered in [docs/experiments/uncertainty_uplift_design.md](docs/experiments/uncertainty_uplift_design.md), including the exact prompt text, pre-committed outcome interpretations, and qualitative review criteria to distinguish genuine reasoning improvement from lexical mimicry.

**Status:** Design locked. Execution scheduled after the multi-run CI baseline is in place to ensure a clean comparison.

---

## Observed failure patterns

**Pattern 1 — Correct number, wrong reasoning** (`feat_002`, `feat_003`, `model_001–003`):
Every model computes the right feature importances, encodes correctly, or fits the right coefficients — then stops. No model spontaneously adds: which features are statistically indistinguishable, whether the importance ranking is stable across folds, or whether the model is overfit. On these specific tasks: Correctness = 1.0, Stat Validity = 0.25.

**→ Principle:** Correct answer ≠ statistically sound reasoning.

**Pattern 2 — Token spiral without convergence** (Claude models, `feat_004`, `feat_005`, `model_003`):
Claude Opus and Haiku enter a loop of calling `get_column_stats` on every column one-by-one, then re-running the same `run_code` block with minor variations. They produce correct intermediate outputs but take 5–15× more tokens than GPT-4o to reach the same conclusion. Efficiency scores as low as 0.12–0.13.

**→ Principle:** Exploration ≠ efficiency — agents need stopping criteria.

**Pattern 3 — sklearn blind spot** (grok-3-mini, all modeling tasks):
Grok-3-mini attempts to import sklearn inside `run_code`, hits the sandbox restriction, then either retries imports repeatedly or gives up and returns a non-answer. The model never adapts to the pre-injected namespace. Result: 7 zero-correctness runs on tasks it could theoretically solve.

**→ Principle:** Namespace adaptation is a real capability gap, not a sandbox quirk.

**Pattern 4 — Gemini over-truncates** (`mod_003`, `model_002`, `feat_005`):
Gemini 2.5 Flash produces structurally correct code but truncates its final answer before reporting key metrics. Average correctness = 0.58 despite reasonable reasoning steps — the model reaches the right place but doesn't output the conclusion in a scoreable form.

**→ Principle:** Output completeness is as important as output correctness.

---

## Leaderboard — 326 runs · 12 models · 23 tasks

All 12 models completed all 23 original tasks (100% coverage). **Ranking eligibility requires ≥80% task coverage** — see [SCORING_SPEC.md §10](SCORING_SPEC.md#10-ranking-eligibility--coverage-threshold). Scores below reflect the fixed category-aware stat-validity scorer; rankings shifted from the prior scorer (notably gpt-5 dropped from #2 to #8).

**Note:** Rankings shown are single-run point estimates. 95% confidence intervals are available in the [live leaderboard](https://patibandlavenkatamanideep.github.io/RealDataAgentBench/) and results.json. Wide CIs reflect n=1 per task — use `dab run --runs 3` to compute tighter estimates.

| Rank | Model | Avg RDAB Score | Avg Cost / Task | Stat Validity |
|:----:|-------|:--------------:|:---------------:|:-------------:|
| 1 | **gpt-4.1-mini** | **0.854** | $0.0127 | 0.641 |
| 2 | gpt-4o | 0.823 | $0.0428 | 0.658 |
| 3 | gpt-4.1 | 0.823 | $0.0388 | 0.630 |
| 4 | claude-sonnet-4-6 | 0.822 | $0.3170 | **0.714** |
| 5 | claude-opus-4-6 | 0.816 | $1.6276 | 0.685 |
| 6 | llama-3.3-70b | 0.814 | $0.0020 | 0.652 |
| 7 | gpt-4o-mini | 0.790 | $0.0169 | 0.696 |
| 8 | gpt-5 | 0.763 | $0.6713 | 0.630 |
| 9 | claude-haiku-4-5 | 0.757 | $0.0483 | 0.701 |
| 10 | gpt-4.1-nano | 0.659 | $0.0126 | 0.630 |
| 11 | grok-3-mini | 0.639 | $0.0045 | 0.516 |
| 12 | gemini-2.5-flash | 0.623 | $0.0014 | 0.478 |

> Live leaderboard with CI bounds, per-task breakdowns, and category filters: [patibandlavenkatamanideep.github.io/RealDataAgentBench](https://patibandlavenkatamanideep.github.io/RealDataAgentBench/)

---

## 🧠 What this means

Three conclusions that hold across all 326 runs:

- **High correctness does not imply reliable analysis** — a model can score 1.0 on correctness and 0.45 on statistical validity on the same feature-engineering task. Getting the number right is necessary but not sufficient.
- **Model selection should be category-driven, not ranking-driven** — the #1 overall model loses to a free Groq model on modeling tasks. Aggregate leaderboard position is a starting point, not a decision.
- **Cost-performance tradeoffs are large enough to change production architecture** — GPT-4.1 delivers near-identical quality to GPT-5 at 15× lower cost. At scale, that gap determines whether agentic data workflows are economically viable.

---

## Who is this for?

- **ML / GenAI engineers** evaluating LLM agents on structured analytical tasks
- **Data teams** comparing models for analytical workflows before committing to an API contract
- **Researchers** studying statistical reasoning and validity in LLM outputs
- **Engineers** who want an open benchmark they can clone, extend, and run on their own data

---

## What it looks like

### 1. Live leaderboard — 326 runs across 12 models with CI bounds and cost column

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

## ⚡ 60-second demo

```bash
dab run eda_001 --model gpt-4.1 --budget 0.02
dab score outputs/eda_001_*.json
```

You'll see: score breakdown across all four dimensions · token usage · statistical validity gaps.

No dataset download needed — generators are seeded and reproducible.

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

# 11. Run 3× per task for 95% CI estimates (triples cost but gives defensible uncertainty bounds)
#     Use --temperature 0 for deterministic outputs — reduces variance noise in CI estimation
dab run eda_001 --model gpt-4.1 --runs 3 --temperature 0
dab run --all --model gpt-4.1 --runs 3 --temperature 0

# 12. See all supported models + API key status
dab models
```

---

## Tasks (39 total — 33 synthetic · 6 real-data)

The 6 real-data tasks (`eda_004`, `eda_005`, `feat_006`, `model_006`, `stat_006`, `mod_006`) use
**real, publicly licensed datasets** from UCI and sklearn's built-in collection. Ground truths are
independently computed from the actual data — not from a generator — and are reproducible by
running `sklearn.datasets.load_*()` directly. See `tasks/*/` for YAML specs and
`realdataagentbench/datasets/generators/real_*.py` for the loaders.

### Exploratory Data Analysis (7 — 5 synthetic · 2 real)

| ID | Title | Difficulty | Key Concepts |
|----|-------|-----------|-------------|
| eda_001 | Income Distribution Analysis | Easy | Skewness, log transform |
| eda_002 | Patient Records — Missing Data & Outlier Audit | Medium | Missing rates, IQR outliers |
| eda_003 | E-Commerce Confounding Variable Detection | Hard | Simpson's Paradox, partial correlation |
| eda_004 ⭐ | **[Real]** Breast Cancer Wisconsin — Feature Distribution & Malignancy Predictors | Medium | Real UCI data, correlation, class imbalance |
| eda_005 ⭐ | **[Real]** Iris Dataset — Species Separability & Feature Importance | Easy | Real Fisher (1936) data, linear separability |
| eda_006 | Salary Survey — Compensation Distribution & Benchmark Analysis | Easy | Skewness, log transform, department comparison |
| eda_007 | Manufacturing Quality — Process Variation & Defect Analysis | Medium | Std dev by machine, defect rate, correlation |

### Feature Engineering (8 — 7 synthetic · 1 real)

| ID | Title | Difficulty | Key Concepts |
|----|-------|-----------|-------------|
| feat_001 | Polynomial Feature Engineering for House Prices | Easy | Interaction terms, R² comparison |
| feat_002 | Categorical Encoding & Feature Selection | Medium | One-hot encoding, RF feature importance |
| feat_003 | Datetime Feature Extraction for Retail Sales | Medium | Datetime parsing, weekend effect |
| feat_004 | Feature Selection Pipeline for Credit Risk | Hard | Multicollinearity, ROC-AUC, Gradient Boosting |
| feat_005 | Feature Engineering for Imbalanced Fraud Detection | Hard | SMOTE, F1-score, class imbalance |
| feat_006 ⭐ | **[Real]** Diabetes Dataset — Feature Correlation & Regression Baseline | Medium | Real Efron et al. (2004) data, feature ranking, R² |
| feat_009 | Employee Attrition — Categorical Encoding & Feature Importance | Medium | Label vs one-hot, ordinal encoding, RF importance |
| feat_010 | Retail Sales — Lag & Rolling Window Features for Time Series | Hard | Lag features, rolling mean, autocorrelation |

### Modeling (8 — 7 synthetic · 1 real)

| ID | Title | Difficulty | Key Concepts |
|----|-------|-----------|-------------|
| model_001 | Logistic Regression for Diabetes Prediction | Easy | Coefficients, ROC-AUC, feature ranking |
| model_002 | Random Forest for Wine Quality | Medium | Feature importance, CV tuning, F1 |
| model_003 | Ridge vs Lasso for Student Performance | Medium | Regularization, RMSE, sparsity |
| model_004 | Gradient Boosting for Customer Churn | Hard | Confusion matrix, CV AUC, model comparison |
| model_005 | Multi-Model Regression for Energy Consumption | Hard | RMSE comparison, CV R², feature importance |
| model_006 ⭐ | **[Real]** Wine Recognition — Multi-Class Classification with Feature Analysis | Medium | Real UCI data, RF vs LR, flavanoids |
| model_009 | Wine Quality — Linear Regression vs Random Forest Comparison | Medium | RMSE, R², model comparison, numeric target |
| model_010 | House Prices — Ridge vs Lasso Regularization Comparison | Medium | Regularization, sparsity, coefficient shrinkage |

### Statistical Inference (8 — 7 synthetic · 1 real)

| ID | Title | Difficulty | Key Concepts |
|----|-------|-----------|-------------|
| stat_001 | A/B Test — Conversion Rate Experiment | Easy | z-test, confidence intervals, lift |
| stat_002 | Clinical Trial — Drug Efficacy Test | Medium | t-test, Cohen's d, baseline balance |
| stat_003 | Salary Gap Analysis — Controlling for Confounders | Hard | OLS regression, pay gap, confounding |
| stat_004 | Time Series Decomposition — Sales Trend & Seasonality | Medium | Decomposition, trend, seasonality |
| stat_005 | Statistical Process Control — Manufacturing Defects | Hard | Cp index, drift detection, chi-squared |
| stat_006 ⭐ | **[Real]** Iris Species — One-Way ANOVA for Petal Length Separation | Medium | Real Fisher (1936) data, ANOVA, F-statistic |
| stat_009 | Salary Survey — Mann-Whitney Test for Non-Parametric Gender Comparison | Medium | Mann-Whitney U, non-parametric, null result |
| stat_010 | Employee Attrition — Chi-Squared Test for Overtime & Attrition Independence | Easy | Chi-squared, contingency table, Cramér's V |

### ML Engineering (8 — 7 synthetic · 1 real)

| ID | Title | Difficulty | Key Concepts |
|----|-------|-----------|-------------|
| mod_001 | Data Leakage Detection in Model Selection | Easy | Target leakage, correlation, AUC drop |
| mod_002 | K-Fold Cross-Validation vs Single Hold-Out | Easy | CV variance, small dataset evaluation |
| mod_003 | Probability Calibration for Heart Disease Prediction | Medium | Brier score, Platt scaling, reliability |
| mod_004 | Ensemble Voting vs Individual Models | Medium | VotingClassifier, soft voting, F1 |
| mod_005 | Nested Cross-Validation for Unbiased Tuning | Hard | Selection bias, GridSearchCV, nested CV |
| mod_006 ⭐ | **[Real]** Breast Cancer Wisconsin — K-Fold CV vs Hold-Out on Real Clinical Data | Medium | Real UCI data, CV variance, stratification |
| mod_009 | Fraud Detection — Decision Threshold Optimization for Recall-Weighted F-Score | Medium | Threshold sweep, precision-recall, F-beta |
| mod_010 | Credit Risk — Feature Importance Stability via Bootstrap Resampling | Hard | Bootstrap, stability, confidence intervals |

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

The full scoring specification — every formula, regex, threshold, worked example, and known limitation — is in **[SCORING_SPEC.md](SCORING_SPEC.md)**. Every score in the leaderboard is independently reproducible from that document alone without reading source code.

The statistical validity scorer uses lexical pattern matching. For a precise description of every signal it checks, the exact regexes, a worked example with manual re-scoring, and its known limitations — see [docs/methodology/stat_validity.md](docs/methodology/stat_validity.md).

---

## Project Structure

```
realdataagentbench/
├── core/
│   ├── task.py           # Pydantic schema — validates every YAML field
│   └── registry.py       # Discovers, loads, and filters tasks
├── datasets/
│   └── generators/       # 33 seeded synthetic generators + 6 real-data loaders (UCI/sklearn)
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
│   ├── stat_validity.py  # Lexical statistical rigour signals (category-aware)
│   ├── llm_judge.py      # LLM-as-judge scorer for stat-validity calibration
│   └── composite.py      # Weighted RDAB Score + ScoreCard
└── cli.py                # dab run / list / inspect / score / models
tasks/
├── eda/                  # 7 tasks
├── feature_engineering/  # 8 tasks
├── modeling/             # 8 tasks
├── statistical_inference/ # 8 tasks
└── ml_engineering/       # 8 tasks (leakage, CV, calibration, ensemble, nested CV, threshold, stability)
tests/                    # 150 offline tests — no API calls required
scripts/
├── build_leaderboard.py        # Aggregates outputs/ → docs/results.json (mean ± 95% CI)
├── calibrate_stat_validity.py  # Lexical scorer vs LLM judge agreement (Cohen's κ)
└── dimension_correlations.py   # Scorer-to-scorer Pearson correlation matrix
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
- [x] Phase 7 — 12 models: GPT-5, GPT-4.1, GPT-4.1-mini, GPT-4.1-nano, Grok-3-mini, Gemini 2.5 Flash, Llama 3.3 via Groq; 326 total runs
- [x] Phase 8 — 6 real-data tasks (UCI/sklearn): Breast Cancer, Iris, Diabetes, Wine, ANOVA; SCORING_SPEC.md v1.2; coverage threshold policy; benchmark methodology docs
- [x] Phase 9 — Scorer fixes: category-aware stat-validity (was EDA-only); multi-run CI via `--runs N`; LLM-as-judge scorer for calibration; scorer correlation matrix
- [x] Phase 10 — Full scorer rigor: category-aware interpretation check (Check 3 now category-specific, not EDA-only); expanded vocabulary for modeling/feature-engineering/ML engineering; `--temperature` flag for deterministic multi-run mode; 7 new tests
- [ ] Run calibration script (`calibrate_stat_validity.py`) and publish Cohen's κ agreement between lexical scorer and LLM judge
- [ ] Run ≥3× per task at temperature=0 for defensible CI estimates; report variance across runs
- [ ] 30+ tasks (visualization, NLP, time series categories)
- [ ] arXiv paper

---


## FAQ

**How is stat-validity scored? Isn't that just keyword matching?**

Yes, it is lexical. The scorer applies four binary checks to the agent's final answer, all of which are **category-aware**:

1. **Uncertainty quantification** — Does the answer report a p-value, CI, standard deviation, or other uncertainty signal? Extended vocabulary covers ML uncertainty (bootstrap CI, variance, stability, robustness).
2. **Appropriate method vocabulary** — Does the answer name a method appropriate to the task category? EDA tasks check for correlation/IQR; stat-inference tasks check for t-test/chi-squared/ANOVA; modeling tasks check for CV/AUC/precision; feature-engineering and ML engineering tasks have their own vocab lists.
3. **Analytical interpretation** — Does the answer show understanding beyond bare numbers? This is **category-specific**: modeling tasks are checked for overfitting/generalization signals; feature-engineering tasks for multicollinearity/leakage awareness; ML engineering tasks for selection-bias/calibration reasoning; stat-inference for effect size/practical significance; EDA for confounding/causation awareness.
4. **Absence of p-hacking signals** — No language suggesting the method was chosen to achieve significance.

Score = checks_passed / 4 (0.25 increments). Check 4 almost always passes, so the practical floor is 0.25; the other three require substantive output.

The scorer cannot verify that a reported p-value was computed correctly — it detects the vocabulary, not the reasoning. To quantify this limitation, `scripts/calibrate_stat_validity.py` compares the lexical scorer to an LLM judge (Claude) on a stratified sample of real agent outputs, reporting Pearson correlation and per-criterion Cohen's kappa. For a full list of signals, the exact regexes, and a worked manual re-score, see [docs/methodology/stat_validity.md](docs/methodology/stat_validity.md).

---

**What is the coverage threshold for ranking?**

A model must complete **≥80% of tasks** to be eligible for the ranked leaderboard. Models below this threshold appear in a "partial coverage" section, are not assigned a rank, and are visually flagged. Their averages cannot be fairly compared against full-coverage models because different task sets have different difficulty distributions. Currently all 12 models ran on the original 23 tasks at 100% coverage; new tasks (24–39) will be run as part of the next benchmark cycle. The 80% threshold is enforced dynamically in the leaderboard code. See [SCORING_SPEC.md §10](SCORING_SPEC.md) for the full policy.

---

**What's the difference between RDAB and AgentBench / DA-Code / ScienceAgentBench / HELM?**

See the [RDAB vs Existing Benchmarks](#rdab-vs-existing-benchmarks) table above for a full design-feature comparison.

The key differentiator is that RDAB measures **how** an agent reasons, not just **what** it outputs. A model that reports AUC=0.84 without a confidence interval, or that computes a correlation without noting the confounding structure, scores well on correctness-only benchmarks but poorly on RDAB's statistical validity dimension.

To validate this difference empirically, a future version will run a subset of agents on both RDAB and one existing benchmark to demonstrate score divergence.

---

## Known Limitations

**Lexical stat-validity scorer.** The `stat_validity` scorer is pattern-based. All four checks are category-aware: each category has its own method vocabulary list (Check 2) and its own interpretation signal list (Check 3 — overfitting/generalization for modeling, leakage/stability for feature engineering, selection-bias/calibration for ML engineering, etc.). The scorer detects vocabulary, not reasoning quality: a model that writes "confidence interval" without computing one still passes Check 1. `scripts/calibrate_stat_validity.py` measures agreement between the lexical scorer and an LLM judge (Pearson r and Cohen's κ) to quantify this limitation. See [docs/methodology/stat_validity.md](docs/methodology/stat_validity.md).

**Seeded synthetic datasets.** 33 of 39 tasks use seeded, reproducible dataset generators. This ensures reproducibility but means RDAB does not test robustness to real-world data quality issues — missing values in unexpected columns, mixed dtypes, inconsistent encoding, corrupted records. The 6 real-data tasks (UCI/sklearn) partially address this, but even those use clean, well-known datasets. Performance on real production data may differ.

**String-match correctness scoring.** Ground-truth matching for some tasks checks for the presence of key values or phrases in the final answer. Verbose outputs may satisfy the check when terse correct outputs do not. This is a known limitation of automated scoring; it is most relevant to the EDA tasks.

**Coverage policy.** Models with <80% task coverage are excluded from ranking and flagged separately. Currently all 12 models have run the original 23-task set at 100% coverage; tasks 24–39 will be added in the next benchmark cycle. The policy is enforced dynamically and documented in [SCORING_SPEC.md §10](SCORING_SPEC.md).

**No multi-turn, RAG, or long-context scenarios.** RDAB tests single-session agentic loops on structured tabular data. It does not cover retrieval-augmented generation, multi-session memory, or tasks requiring context beyond a single DataFrame.

---

## External Results & Community Validation

RDAB is only as credible as the number of independent groups that have run it and published results. If you run RDAB on your models, submitting your results strengthens the benchmark for everyone.

**→ [Submit your results](RESULTS_SUBMISSION.md)** — instructions for running the benchmark and opening a PR to add your model to the leaderboard.

Requirements: all 39 tasks at full coverage, unmodified `dab run` harness, ≥1 run per task (≥3 recommended for CI estimates).

---

## How to cite / reproduce

To reproduce the full leaderboard:

```bash
git clone https://github.com/patibandlavenkatamanideep/RealDataAgentBench
cd RealDataAgentBench
pip install -e ".[dev]"
cp .env.example .env          # add your API key(s)
dab run --all --model gpt-4.1 # ~$0.88 for all 39 tasks (single run)
dab run --all --model gpt-4.1 --runs 3 --temperature 0  # 95% CI estimates (~$2.64)
python scripts/build_leaderboard.py
```

All dataset generators are seeded. Running with the same model, `random_state` settings, and `--temperature 0` will reproduce the published scores within scoring tolerance. Single-run scores are point estimates; use `--runs 3` or more for confidence intervals.

To cite:

```bibtex
@software{patibandla2026rdab,
  author    = {Patibandla, Venkata Manideep},
  title     = {{RealDataAgentBench}: An Open Benchmark for Statistical Validity
               in LLM Data Science Agents},
  year      = {2026},
  url       = {https://github.com/patibandlavenkatamanideep/RealDataAgentBench},
  note      = {39 tasks, 4-dimensional scoring, 12 models at full coverage.}
}
```

---

## CostGuard — Practical Companion Tool

> **This is a separate project.** RDAB is a research benchmark — fixed tasks, published methodology, reproducible runs. CostGuard is a practical interactive tool built independently alongside RDAB.

**CostGuard** lets you upload your own CSV and run a live cost-performance analysis against any model — without writing code. Where RDAB evaluates on seeded benchmark tasks with transparent ground truth, CostGuard is interactive: you bring your data, it runs the analysis on your dataset and returns results in real time.

Key distinction: RDAB uses only its own seeded and publicly licensed datasets — it never touches user-uploaded files. CostGuard processes your data in memory and does not store it server-side (see the CostGuard repo for its own privacy policy).

> **[Live app →](https://costguard-production-3afa.up.railway.app/)** &nbsp;·&nbsp; **[GitHub →](https://github.com/patibandlavenkatamanideep/CostGuard)**

---

## License

MIT — see [LICENSE](LICENSE).

---

## Built by

[Venkata Manideep Patibandla](https://github.com/patibandlavenkatamanideep)  
Focused on LLM evaluation, agent systems, and statistically robust AI workflows.
