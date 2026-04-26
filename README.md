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

## TL;DR

- **12 models, 39 tasks, 4-dimensional scoring** — correctness alone misses where models fail in production data workflows
- **GPT-4.1 leads overall at ~15× lower cost than GPT-5** — cost-performance tradeoffs are large enough to change production architecture decisions
- **A free Groq model (Llama 3.3-70b) beats GPT-5 on modeling tasks** — aggregate ranking hides category-level capability gaps
- **Stat-validity is the differentiating dimension:** Claude leads on validity (Sonnet 0.71), GPT leads on correctness — the two dimensions correlate at r = 0.48, confirming they capture orthogonal capabilities

Models that report metrics without uncertainty bounds are dangerous in production data workflows — RDAB measures that gap directly.

---

## Leaderboard — 326 runs · 12 models · 23 tasks (expanding to 39)

**Coverage transparency — what each row means:**

| Tier | Models | Task coverage | Run count | CI status |
|------|--------|:---:|:---:|---|
| Free (expanding) | Gemini 2.5 Flash, Llama 3.3-70b, Grok-3-mini | 39/39 (in progress) | 5 runs target | Full CI planned |
| Tier 1 GPT | gpt-4.1-nano, gpt-4.1-mini, gpt-4o-mini | 39/39 (in progress) | 3 runs target | Full CI planned |
| Tier 2 mid | gpt-4.1, gpt-4o, claude-haiku | 39/39 (in progress) | 3 runs target | Full CI planned |
| **Tier 3 (expensive)** | **claude-sonnet, gpt-5, claude-opus** | **23/39** | **n=1 point estimates** | **No CI — cost-prohibitive at $37–$190 for 3×39 runs** |

**Ranking eligibility requires ≥80% task coverage** — see [SCORING_SPEC.md §10](SCORING_SPEC.md#10-ranking-eligibility--coverage-threshold).

> **Note on Tier 3 models:** Claude Sonnet 4.6, GPT-5, and Claude Opus 4.6 scores shown below are **single-run point estimates on the original 23 tasks only**. No confidence intervals are available for these models — running 3×39 tasks would cost $37, $78, and $190 respectively. Treat their rankings as indicative, not statistically robust. All other models are receiving full multi-run CI coverage across all 39 tasks.

| Rank | Model | Avg RDAB Score | CI | Avg Cost / Task | Stat Validity | Coverage |
|:----:|-------|:--------------:|:--:|:---------------:|:-------------:|:--------:|
| 1 | **gpt-4.1-mini** | **0.854** | n=1† | $0.0127 | 0.641 | 23/39 |
| 2 | gpt-4o | 0.823 | n=1† | $0.0428 | 0.658 | 23/39 |
| 3 | gpt-4.1 | 0.823 | n=1† | $0.0388 | 0.630 | 23/39 |
| 4 | claude-sonnet-4-6 ⚠️ | 0.822 | n=1 | $0.3170 | **0.714** | 23/39 |
| 5 | claude-opus-4-6 ⚠️ | 0.816 | n=1 | $1.6276 | 0.685 | 23/39 |
| 6 | llama-3.3-70b | 0.814 | n=1† | $0.0020 | 0.652 | 23/39 |
| 7 | gpt-4o-mini | 0.790 | n=1† | $0.0169 | 0.696 | 23/39 |
| 8 | gpt-5 ⚠️ | 0.763 | n=1 | $0.6713 | 0.630 | 23/39 |
| 9 | claude-haiku-4-5 | 0.757 | n=1† | $0.0483 | 0.701 | 23/39 |
| 10 | gpt-4.1-nano | 0.659 | n=1† | $0.0126 | 0.630 | 23/39 |
| 11 | grok-3-mini | 0.639 | n=1† | $0.0045 | 0.516 | 23/39 |
| 12 | gemini-2.5-flash | 0.623 | n=1† | $0.0014 | 0.478 | 23/39 |

> † = multi-run CI in progress (expanding to 39 tasks × 3–5 runs)  
> ⚠️ = single-run estimate only; no CI planned due to cost  
> Live leaderboard with CI bounds, per-task breakdowns, and category filters: [patibandlavenkatamanideep.github.io/RealDataAgentBench](https://patibandlavenkatamanideep.github.io/RealDataAgentBench/)

---

## Live leaderboard

![Leaderboard screenshot](docs/screenshots/leaderboard.png)

> **→ [Open live leaderboard](https://patibandlavenkatamanideep.github.io/RealDataAgentBench/)** — filterable by category, sortable by score or cost.

---

## 🔍 Key Findings

From 326 runs across 12 models and 23 tasks — patterns observed in actual benchmark output, not hypothetical.

---

> **💡 Insight 1: Stat-validity isn't a uniform weakness — it's category-dependent and model-dependent**
>
> The gap appears in two dimensions. By category: **EDA = 0.87, stat inference = 0.86, ML engineering = 0.59, modeling = 0.51, feature engineering = 0.45** — models reach for statistical language reactively when cued by the task name, not proactively when warranted. Modeling and feature engineering are the worst: models report AUC and feature importances without uncertainty bounds because nothing in the task name signals that statistics are expected.
>
> By model family: **Claude models lead on stat-validity** (Sonnet 0.71, Haiku 0.70) while trailing GPT models on overall RDAB score — suggesting the dimensions measure genuinely different capabilities. The scorer-correlation analysis confirms this: correctness × stat-validity correlate at r = 0.48; all other dimension pairs are below r = 0.25.
>
> **→ Aggregate leaderboard position masks two orthogonal capability gradients.**

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

## Why RDAB is different

Most data science agent benchmarks ask one question: *"Did the agent get the right answer?"* That is not enough.

| Dimension | What it catches |
|-----------|----------------|
| **Correctness** | Did the agent find the right skewness, correlation sign, missing columns? |
| **Code Quality** | Did it use vectorized ops? Descriptive names? No raw loops? |
| **Efficiency** | Did it waste 10× the token budget to answer a simple question? |
| **Stat Validity** | Did it report uncertainty? Use appropriate tests? Avoid confusing correlation with causation? |

An agent can score **1.0 on correctness and 0.25 on statistical validity on the same task** — and that delta tells you exactly where it fails in production.

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

## 🧠 What this means

Three conclusions that hold across all 326 runs:

- **High correctness does not imply reliable analysis** — a model can score 1.0 on correctness and 0.45 on statistical validity on the same feature-engineering task. Getting the number right is necessary but not sufficient.
- **Model selection should be category-driven, not ranking-driven** — the #1 overall model loses to a free Groq model on modeling tasks. Aggregate leaderboard position is a starting point, not a decision.
- **Cost-performance tradeoffs are large enough to change production architecture** — GPT-4.1 delivers near-identical quality to GPT-5 at 15× lower cost. At scale, that gap determines whether agentic data workflows are economically viable.

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

33 of 39 tasks use seeded synthetic generators. The stat-validity gap (modeling and feature engineering tasks averaging 0.45–0.51 despite correctness ≥ 0.83) is not a synthetic-data artifact — it appears on both synthetic and real-data tasks, and the scoring rubric is identical across both. Known limitations: distributions are idealized vs. real-world data; memorization risk on synthetic tasks (the 6 real-data tasks are not subject to this); ground-truth correctness is defined by the generator, not an external authority.

### Scoring independence

The four scorers (`correctness`, `code_quality`, `efficiency`, `stat_validity`) each run independently on the trace JSON. They do not share state. The composite RDAB Score is a weighted average of their outputs using per-task weights defined in the task YAML.

Ground truth for synthetic tasks is pre-computed at task-creation time and stored in the YAML `ground_truth:` block. Ground truth for real-data tasks is computed from the actual sklearn dataset and is independently verifiable. Neither requires reading RDAB source code.

---

## Tasks

39 tasks across 5 categories: EDA (7), Feature Engineering (8), Modeling (8), Statistical Inference (8), ML Engineering (8). 6 use real UCI/sklearn datasets; 33 use seeded synthetic generators. Difficulty ranges from easy (skewness, log transform) to hard (nested cross-validation, multicollinearity, Simpson's paradox).

<details>
<summary>Click to see all 39 tasks with descriptions</summary>

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

</details>

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

## Known Limitations

**Lexical stat-validity scorer.** The `stat_validity` scorer is pattern-based. All four checks are category-aware: each category has its own method vocabulary list (Check 2) and its own interpretation signal list (Check 3 — overfitting/generalization for modeling, leakage/stability for feature engineering, selection-bias/calibration for ML engineering, etc.). The scorer detects vocabulary, not reasoning quality: a model that writes "confidence interval" without computing one still passes Check 1. `scripts/calibrate_stat_validity.py` measures agreement between the lexical scorer and an LLM judge (Pearson r and Cohen's κ) to quantify this limitation. See [docs/methodology/stat_validity.md](docs/methodology/stat_validity.md).

**Seeded synthetic datasets.** 33 of 39 tasks use seeded, reproducible dataset generators. This ensures reproducibility but means RDAB does not test robustness to real-world data quality issues — missing values in unexpected columns, mixed dtypes, inconsistent encoding, corrupted records. The 6 real-data tasks (UCI/sklearn) partially address this, but even those use clean, well-known datasets. Performance on real production data may differ.

**String-match correctness scoring.** Ground-truth matching for some tasks checks for the presence of key values or phrases in the final answer. Verbose outputs may satisfy the check when terse correct outputs do not. This is a known limitation of automated scoring; it is most relevant to the EDA tasks.

**Coverage policy.** Models with <80% task coverage are excluded from ranking and flagged separately. Currently all 12 models have run the original 23-task set at 100% coverage; tasks 24–39 will be added in the next benchmark cycle. The policy is enforced dynamically and documented in [SCORING_SPEC.md §10](SCORING_SPEC.md).

**No multi-turn, RAG, or long-context scenarios.** RDAB tests single-session agentic loops on structured tabular data. It does not cover retrieval-augmented generation, multi-session memory, or tasks requiring context beyond a single DataFrame.

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

---

## Roadmap

- **Done:** Task schema and harness (168 tests), 39 tasks across 5 categories, 12 models benchmarked with live leaderboard, per-run cost tracking, category-aware scorer, 6 real-data tasks (UCI/sklearn), LLM-as-judge calibration script, multi-run CI support with `--temperature` flag
- **In progress:** Multi-run sweep across all 39 tasks at temperature=0 for CI estimates; calibration κ between lexical scorer and LLM judge; pre-registered uncertainty-uplift experiment
- **Next:** Visualization, NLP, and time-series task categories; arXiv paper

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
tests/                    # 168 offline tests — no API calls required
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
