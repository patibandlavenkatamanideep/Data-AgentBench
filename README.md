<p align="center">
  <img src="docs/logo.svg" alt="RealDataAgentBench logo" width="700" />
</p>

<p align="center">
  <strong>Most LLMs get the right answer. RDAB checks if they did it the right way.</strong>
</p>

<p align="center">
  <a href="https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions"><img src="https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/patibandlavenkatamanideep/RealDataAgentBench/actions/workflows/ci.yml"><img src="https://img.shields.io/badge/tests-150%20passing-brightgreen" alt="Tests"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python"></a>
  <a href="https://github.com/patibandlavenkatamanideep/RealDataAgentBench/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License"></a>
  <a href="https://patibandlavenkatamanideep.github.io/RealDataAgentBench/"><img src="https://img.shields.io/badge/leaderboard-live-brightgreen" alt="Leaderboard"></a>
  <a href="SCORING_SPEC.md"><img src="https://img.shields.io/badge/scoring-fully%20transparent-blue" alt="Scoring spec"></a>
  <a href="tasks/"><img src="https://img.shields.io/badge/tasks-29%20(6%20real%20data)-orange" alt="Tasks"></a>
</p>

> **Frontier models score 0.83–1.00 on correctness across data-science tasks.**  
> **The same models score 0.25 on statistical validity on the same tasks.**  
> Correct number. Wrong reasoning. This gap appears across GPT-5, Claude, Llama, and Gemini — without exception.

---

## What RDAB is

**RealDataAgentBench (RDAB)** is a production-grade open-source benchmark that evaluates whether LLM agents do data science work that is not just *correct* but *statistically sound* — reporting uncertainty, using appropriate tests, and avoiding causal overreach.

Built with the rigor you'd expect from an internal evaluation framework at an AI lab: transparent scoring specs, reproducible datasets, real-world data tasks, and a pre-registered controlled experiment.

→ **29 tasks** — 23 synthetic + **6 real-data tasks** (UCI Breast Cancer, Iris, Diabetes, Wine — real clinical and scientific datasets)  
→ **4-dimensional scoring** — correctness, code quality, efficiency, statistical validity  
→ **12 models at full 23-task coverage** — 276 total runs; models with <80% task coverage are flagged and excluded from ranking  
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
If 60% of outputs lack appropriate uncertainty bounds (consistent with RDAB's ~0.25 stat-validity finding), that is 300 analysis outputs per month where a decision-maker has no basis for knowing how much to trust the number. At scale, this degrades the value of agentic data workflows.

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

## Why RDAB is credible

- **Every score is independently reproducible.** [SCORING_SPEC.md](SCORING_SPEC.md) documents every formula, regex, threshold, and known limitation. No source code reading required.
- **Scoring limitations are disclosed.** The stat-validity scorer has a documented bug (Check 2 is EDA-only). The impact is quantified. The leaderboard numbers are what they are — not overclaimed.
- **Partial-coverage models are excluded from ranking.** Any model with <80% task coverage is flagged and excluded from the ranked leaderboard. Their scores are not averaged against different task sets. Currently all 12 models are at 23/23 coverage.
- **Datasets are real where it matters.** Six tasks use publicly licensed real-world datasets (UCI Breast Cancer, Iris, Diabetes, Wine) with ground truths computed independently from the data.
- **The key experiment is pre-registered.** The uncertainty prompting uplift experiment has committed outcome interpretations before any runs are executed.

---

## Benchmark Methodology

### Data modes

**`dab run <task> --dry-run`** — Validates that the dataset generator loads correctly and the task YAML parses without error. No API call is made. No model output is produced. Use this to verify your environment.

**`dab run <task>`** — Live mode. Makes a real API call to the model provider. The agent receives a sandboxed Python execution environment with the seeded dataset pre-loaded, and iterates through tool calls until it produces a final answer or hits the step/timeout limit. Every tool call, token count, and final answer is recorded in the trace JSON.

There is no "simulation mode" or pre-cached response replay. Every score in the leaderboard is from a live model run with a real API call. The trace files in `outputs/` are the raw records.

### Data handling and privacy guarantee

> **Your data is processed in memory and never stored by RDAB.** The benchmark generates or loads datasets at runtime, passes them to the agent, scores the output, and writes the trace to your local `outputs/` directory. No data is uploaded to external servers by this framework. API calls to model providers (OpenAI, Anthropic, etc.) are governed by those providers' own privacy policies.

Synthetic datasets are generated from seeded NumPy/Pandas operations — they do not contain or approximate any real person's data. Real-data tasks use publicly licensed datasets (UCI/sklearn) that are already in the public domain or licensed for open use (see [SCORING_SPEC.md §11](SCORING_SPEC.md)).

### Synthetic data: limitations and transparency

23 of 29 tasks use seeded synthetic generators. Limitations:

- **Distribution artifacts:** Synthetic distributions are idealized (e.g., log-normal income). Real-world data is messier and harder to analyze correctly.
- **No ground-truth validation against reality:** The "correct" skewness or correlation is defined by the generator — not by any external authority.
- **Memorization risk:** A model could in principle achieve perfect correctness on synthetic tasks if it memorized the generator's output patterns from training data. The 6 real-data tasks (using independently verifiable UCI/sklearn datasets) are not subject to this risk.

These limitations are documented. The 0.25 statistical validity finding is not a synthetic-data artifact — it appears on both synthetic and real-data tasks, and the scoring rubric is identical across both.

### Scoring independence

The four scorers (`correctness`, `code_quality`, `efficiency`, `stat_validity`) each run independently on the trace JSON. They do not share state. The composite RDAB Score is a weighted average of their outputs using per-task weights defined in the task YAML.

Ground truth for synthetic tasks is pre-computed at task-creation time and stored in the YAML `ground_truth:` block. Ground truth for real-data tasks is computed from the actual sklearn dataset and is independently verifiable. Neither requires reading RDAB source code.

---

## 🔍 Key Findings

From 276 runs across 12 models and 23 tasks — patterns observed in actual benchmark output, not hypothetical.

---

> **💡 Insight 1: Statistical validity is the universal weak point**
>
> Every model — GPT-5, Claude Opus, Llama, Gemini — scores **0.25 on statistical validity** for `feat_002`, `feat_003`, `model_001`, and `model_002` while scoring 0.83–1.00 on correctness for the same tasks. Not some models. All of them. The scorer checks for uncertainty reporting, appropriate test choice, and correct interpretation. Models pass the correctness check and fail the other three.
>
> The methodology and a worked example with manual re-scoring are in [docs/methodology/stat_validity.md](docs/methodology/stat_validity.md).
>
> **→ Correct answer ≠ statistically sound reasoning.**

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
> GPT-4.1 leads EDA, Feature Engineering, and Statistical Inference outright — at **$0.038/task** vs GPT-5's $0.596. That's 15× cheaper for ~98% of the output quality. For teams running hundreds of analysis tasks a week, the difference compounds fast.
>
> **→ The best model for your use case is rarely the most expensive one.**

---

## Human Expert Baseline

To answer "is 0.832 good?", RDAB includes a human expert baseline on 5 representative tasks. A domain expert (5+ years applied data science) solved the same tasks under the same conditions — same task description, same DataFrame, same sandboxed tool environment — without seeing the scoring rubric or ground truth. Solutions were scored post-hoc with the identical SCORING_SPEC.md rubric.

| Task | Category | Human RDAB | Human Stat Valid | Model Avg Stat Valid | Gap |
|------|----------|:----------:|:----------------:|:--------------------:|:---:|
| eda_001 | EDA | 0.888 | **0.75** | 1.00 | −0.25 |
| model_001 | Modeling | 0.820 | **0.75** | 0.27 | **+0.48** |
| stat_002 | Stat. Inference | 0.879 | **0.875** | 0.67 | +0.21 |
| feat_002 | Feature Eng. | 0.830 | **0.75** | 0.25 | **+0.50** |
| mod_001 | ML Eng. | 0.879 | **0.875** | 0.60 | +0.27 |
| **Average** | | **0.857** | **0.800** | 0.454 | **+0.346** |

**Key takeaway:** The human expert scored 0.800 average on statistical validity vs. model average 0.454 on the same tasks. The gap is largest on `model_001` (+0.48) and `feat_002` (+0.50) — exactly the tasks where Check 2 structurally fails for models. This confirms the 0.25 finding is a **real model capability gap**, not a scorer artefact: when a human solves the same task, they naturally report confidence intervals, note rank instability, and distinguish statistical from practical significance.

The full baseline methodology and per-task notes are in [`docs/human_baseline.json`](docs/human_baseline.json).

---

## Statistical Validity Experiment (pre-registered)

The 0.25 stat-validity finding is RDAB's headline result — every model fails on the same dimension, on the same tasks, for the same structural reason. Before claiming it as a model capability gap, two alternative explanations need empirical testing:

1. **Scorer artifact hypothesis:** The 0.25 floor is entirely explained by the scorer's EDA-only pattern list (Check 2). Fix the scorer and the gap disappears.
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

**Status:** Design locked. Awaiting budget approval to execute (~$12.67 for all 45 runs).

---

## Observed failure patterns

**Pattern 1 — Correct number, wrong reasoning** (`feat_002`, `feat_003`, `model_001–003`):
Every model computes the right feature importances, encodes correctly, or fits the right coefficients — then stops. No model spontaneously adds: which features are statistically indistinguishable, whether the importance ranking is stable across folds, or whether the model is overfit. Correctness = 1.0, Stat Validity = 0.25.

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

## Leaderboard — 276 runs · 12 models · 23 tasks

All 12 models completed all 23 tasks (100% coverage). **Ranking eligibility requires ≥80% task coverage** — see [SCORING_SPEC.md §10](SCORING_SPEC.md#10-ranking-eligibility--coverage-threshold) for the policy. Models below that threshold would appear in a separate "partial coverage" section, excluded from ranked comparison.

| Rank | Model | Avg RDAB Score | Coverage | Avg Cost / Task | Score / $* |
|:----:|-------|:--------------:|:--------:|:---------------:|:----------:|
| 1 | **gpt-4.1-mini** | **0.832** | 23 / 23 | $0.0127 | **65.8** |
| 2 | gpt-5 | 0.812 | 23 / 23 | $0.5957 | 1.4 |
| 3 | gpt-4o | 0.794 | 23 / 23 | $0.0439 | 18.1 |
| 4 | gpt-4.1 | 0.791 | 23 / 23 | $0.0384 | 20.6 |
| 5 | claude-opus-4-6 | 0.779 | 23 / 23 | $1.6276 | 0.5 |
| 6 | claude-sonnet-4-6 | 0.779 | 23 / 23 | $0.3382 | 2.3 |
| 7 | llama-3.3-70b | 0.772 | 23 / 23 | $0.0020 | 393.2 |
| 8 | gpt-4o-mini | 0.756 | 23 / 23 | $0.0169 | 44.7 |
| 9 | claude-haiku-4-5 | 0.738 | 23 / 23 | $0.0503 | 14.7 |
| 10 | gpt-4.1-nano | 0.642 | 23 / 23 | $0.0126 | 51.0 |
| 11 | gemini-2.5-flash | 0.626 | 23 / 23 | $0.0015 | **417.0** |
| 12 | grok-3-mini | 0.626 | 23 / 23 | $0.0024 | 257.3 |

*\*Score / $ = Avg RDAB Score ÷ Avg Cost per task. Higher = more value per dollar.*

> Live leaderboard with per-task breakdowns and category filters: [patibandlavenkatamanideep.github.io/RealDataAgentBench](https://patibandlavenkatamanideep.github.io/RealDataAgentBench/)

---

## 🧠 What this means

Three conclusions that hold across all 276 runs:

- **High correctness does not imply reliable analysis** — a model can score 1.0 on correctness and 0.25 on statistical validity on the same task. Getting the number right is necessary but not sufficient.
- **Model selection should be category-driven, not ranking-driven** — the #1 overall model loses to a free Groq model on modeling tasks. Aggregate leaderboard position is a starting point, not a decision.
- **Cost-performance tradeoffs are large enough to change production architecture** — GPT-4.1 delivers near-identical quality to GPT-5 at 15× lower cost. At scale, that gap determines whether agentic data workflows are economically viable.

---

## Who is this for?

- **ML / GenAI engineers** evaluating LLM agents on structured analytical tasks
- **Data teams** comparing models for analytical workflows before committing to an API contract
- **Researchers** studying statistical reasoning and validity in LLM outputs
- **Engineers** who want a production-grade benchmark they can clone, extend, and run on their own data

---

## What it looks like

### 1. Live leaderboard — 276 runs across 12 models with cost column

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

# 11. See all supported models + API key status
dab models
```

---

## Tasks (29 total — 23 synthetic · 6 real-data)

The 6 real-data tasks (`eda_004`, `eda_005`, `feat_006`, `model_006`, `stat_006`, `mod_006`) use
**real, publicly licensed datasets** from UCI and sklearn's built-in collection. Ground truths are
independently computed from the actual data — not from a generator — and are reproducible by
running `sklearn.datasets.load_*()` directly. See `tasks/*/` for YAML specs and
`realdataagentbench/datasets/generators/real_*.py` for the loaders.

### Exploratory Data Analysis (5 — 3 synthetic · 2 real)

| ID | Title | Difficulty | Key Concepts |
|----|-------|-----------|-------------|
| eda_001 | Income Distribution Analysis | Easy | Skewness, log transform |
| eda_002 | Patient Records — Missing Data & Outlier Audit | Medium | Missing rates, IQR outliers |
| eda_003 | E-Commerce Confounding Variable Detection | Hard | Simpson's Paradox, partial correlation |
| eda_004 ⭐ | **[Real]** Breast Cancer Wisconsin — Feature Distribution & Malignancy Predictors | Medium | Real UCI data, correlation, class imbalance |
| eda_005 ⭐ | **[Real]** Iris Dataset — Species Separability & Feature Importance | Easy | Real Fisher (1936) data, linear separability |

### Feature Engineering (6 — 5 synthetic · 1 real)

| ID | Title | Difficulty | Key Concepts |
|----|-------|-----------|-------------|
| feat_001 | Polynomial Feature Engineering for House Prices | Easy | Interaction terms, R² comparison |
| feat_002 | Categorical Encoding & Feature Selection | Medium | One-hot encoding, RF feature importance |
| feat_003 | Datetime Feature Extraction for Retail Sales | Medium | Datetime parsing, weekend effect |
| feat_004 | Feature Selection Pipeline for Credit Risk | Hard | Multicollinearity, ROC-AUC, Gradient Boosting |
| feat_005 | Feature Engineering for Imbalanced Fraud Detection | Hard | SMOTE, F1-score, class imbalance |
| feat_006 ⭐ | **[Real]** Diabetes Dataset — Feature Correlation & Regression Baseline | Medium | Real Efron et al. (2004) data, feature ranking, R² |

### Modeling (6 — 5 synthetic · 1 real)

| ID | Title | Difficulty | Key Concepts |
|----|-------|-----------|-------------|
| model_001 | Logistic Regression for Diabetes Prediction | Easy | Coefficients, ROC-AUC, feature ranking |
| model_002 | Random Forest for Wine Quality | Medium | Feature importance, CV tuning, F1 |
| model_003 | Ridge vs Lasso for Student Performance | Medium | Regularization, RMSE, sparsity |
| model_004 | Gradient Boosting for Customer Churn | Hard | Confusion matrix, CV AUC, model comparison |
| model_005 | Multi-Model Regression for Energy Consumption | Hard | RMSE comparison, CV R², feature importance |
| model_006 ⭐ | **[Real]** Wine Recognition — Multi-Class Classification with Feature Analysis | Medium | Real UCI data, RF vs LR, flavanoids |

### Statistical Inference (6 — 5 synthetic · 1 real)

| ID | Title | Difficulty | Key Concepts |
|----|-------|-----------|-------------|
| stat_001 | A/B Test — Conversion Rate Experiment | Easy | z-test, confidence intervals, lift |
| stat_002 | Clinical Trial — Drug Efficacy Test | Medium | t-test, Cohen's d, baseline balance |
| stat_003 | Salary Gap Analysis — Controlling for Confounders | Hard | OLS regression, pay gap, confounding |
| stat_004 | Time Series Decomposition — Sales Trend & Seasonality | Medium | Decomposition, trend, seasonality |
| stat_005 | Statistical Process Control — Manufacturing Defects | Hard | Cp index, drift detection, chi-squared |
| stat_006 ⭐ | **[Real]** Iris Species — One-Way ANOVA for Petal Length Separation | Medium | Real Fisher (1936) data, ANOVA, F-statistic |

### ML Engineering (6 — 5 synthetic · 1 real)

| ID | Title | Difficulty | Key Concepts |
|----|-------|-----------|-------------|
| mod_001 | Data Leakage Detection in Model Selection | Easy | Target leakage, correlation, AUC drop |
| mod_002 | K-Fold Cross-Validation vs Single Hold-Out | Easy | CV variance, small dataset evaluation |
| mod_003 | Probability Calibration for Heart Disease Prediction | Medium | Brier score, Platt scaling, reliability |
| mod_004 | Ensemble Voting vs Individual Models | Medium | VotingClassifier, soft voting, F1 |
| mod_005 | Nested Cross-Validation for Unbiased Tuning | Hard | Selection bias, GridSearchCV, nested CV |
| mod_006 ⭐ | **[Real]** Breast Cancer Wisconsin — K-Fold CV vs Hold-Out on Real Clinical Data | Medium | Real UCI data, CV variance, stratification |

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
│   └── generators/       # 23 seeded synthetic generators + 6 real-data loaders (UCI/sklearn)
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
- [x] Phase 7 — 12 models: GPT-5, GPT-4.1, GPT-4.1-mini, GPT-4.1-nano, Grok-3-mini, Gemini 2.5 Flash, Llama 3.3 via Groq; 276 total runs (all 12 × 23)
- [x] Phase 8 — 6 real-data tasks (UCI/sklearn): Breast Cancer, Iris, Diabetes, Wine, ANOVA; SCORING_SPEC.md v1.2; coverage threshold policy; benchmark methodology + privacy docs
- [ ] Run real-data tasks across all 12 models; label synthetic vs. real in leaderboard
- [ ] Human baseline scores on 5+ representative tasks
- [ ] 30+ tasks (visualization, NLP, time series categories)
- [ ] arXiv paper

---

## For Companies — Choose the Right Model

RDAB gives you per-model scores across correctness, code quality, and statistical validity — with per-task cost — so you can make an evidence-based model choice before committing to an API contract.

**Real numbers from 276 runs across 12 models — all at full 23/23 task coverage:**

| Model | Avg RDAB Score | Avg Cost / Task | Score / $* |
|-------|:--------------:|:---------------:|:----------:|
| **gpt-4.1-mini** | **0.832** | $0.0127 | **65.8** |
| gpt-5 | 0.812 | $0.5957 | 1.4 |
| gpt-4o | 0.794 | $0.0439 | 18.1 |
| gpt-4.1 | 0.791 | $0.0384 | 20.6 |
| claude-opus-4-6 | 0.779 | $1.6276 | 0.5 |
| claude-sonnet-4-6 | 0.779 | $0.3382 | 2.3 |
| llama-3.3-70b | 0.772 | $0.0020 | 393.2 |
| gpt-4o-mini | 0.756 | $0.0169 | 44.7 |
| claude-haiku-4-5 | 0.738 | $0.0503 | 14.7 |
| gpt-4.1-nano | 0.642 | $0.0126 | 51.0 |
| gemini-2.5-flash | 0.626 | $0.0015 | **417.0** |
| grok-3-mini | 0.626 | $0.0024 | 257.3 |

*\*Score / $ = Avg RDAB Score ÷ Avg Cost per task. Higher = more value per dollar.*

GPT-4.1-mini leads overall — at **$0.013/task** vs GPT-5's $0.596, that's **47× cheaper for the #1 spot**. Claude Opus scores comparably to Claude Sonnet at **5× the cost**. For a team running hundreds of analysis tasks a week, cost differences compound fast.

> **Bottom line:** The best model for your use case isn't always the most expensive one. Run RDAB on your own data, check the cost column, and choose accordingly.

---

## FAQ

**How is stat-validity scored? Isn't that just keyword matching?**

Yes, it is lexical. The scorer checks the agent's final answer for four binary signals: (1) uncertainty language such as "p-value", "confidence interval", or "standard error"; (2) an appropriate statistical method mentioned by name; (3) correct interpretation signals such as "statistically significant" or "controlling for"; and (4) absence of p-hacking language. The score is the fraction of checks that pass.

This has real limitations. Check 2 currently only recognises EDA-specific methods (correlation, IQR, skewness) regardless of task category, so it structurally fails on modeling and ML engineering tasks even when the method used is correct. The scorer cannot verify that a reported p-value was computed correctly — it detects the word, not the reasoning. For a full list of signals, the exact regexes, a worked manual re-score, and what a 1.0 output actually looks like, see [docs/methodology/stat_validity.md](docs/methodology/stat_validity.md).

---

**What is the coverage threshold for ranking?**

A model must complete **≥80% of tasks** (currently ≥19 of 23) to be eligible for the ranked leaderboard. Models below this threshold appear in a "partial coverage" section, are not assigned a rank, and are visually flagged. Their averages cannot be fairly compared against full-coverage models because different task sets have different difficulty distributions. Currently all 12 models are at 23/23 (100% coverage). The 80% threshold is enforced dynamically in the leaderboard code. See [SCORING_SPEC.md §10](SCORING_SPEC.md) for the full policy.

---

**What's the difference between RDAB and AgentBench / DA-Code / ScienceAgentBench?**

The core difference is the statistical-validity dimension. Most existing benchmarks measure whether the agent produced the right answer. RDAB additionally measures whether the agent's reasoning process was statistically sound — uncertainty-quantified, causally careful, and methodologically appropriate. No head-to-head comparison across benchmarks has been run; this is a claim about design intent, not a validated empirical comparison. Other practical differences: RDAB uses seeded, reproducible dataset generators (no external downloads), tracks per-run cost in USD, and the full harness is open source and runnable locally with a single API key.

---

## Known Limitations

**Lexical stat-validity scorer.** The `stat_validity` scorer is pattern-based and has a systematic bug: the "appropriate test" check only recognises EDA vocabulary regardless of task category. On the 20 non-EDA tasks, this check structurally fails regardless of model output quality. The finding that models score ~0.25 on stat validity is real, but part of the floor is scorer-imposed rather than model-imposed. Fixing this requires per-category pattern lists and re-running all 276 outputs. This is documented and deferred. See [docs/methodology/stat_validity.md](docs/methodology/stat_validity.md).

**Seeded synthetic datasets.** 23 of 29 tasks use seeded, reproducible dataset generators. This ensures reproducibility but means RDAB does not test robustness to real-world data quality issues — missing values in unexpected columns, mixed dtypes, inconsistent encoding, corrupted records. The 6 real-data tasks (UCI/sklearn) partially address this, but even those use clean, well-known datasets. Performance on real production data may differ.

**String-match correctness scoring.** Ground-truth matching for some tasks checks for the presence of key values or phrases in the final answer. Verbose outputs may satisfy the check when terse correct outputs do not. This is a known limitation of automated scoring; it is most relevant to the EDA tasks.

**Coverage policy.** Models with <80% task coverage are excluded from ranking and flagged separately. Currently all 12 models are at full 23/23 coverage. The policy is enforced dynamically and documented in [SCORING_SPEC.md §10](SCORING_SPEC.md).

**No multi-turn, RAG, or long-context scenarios.** RDAB tests single-session agentic loops on structured tabular data. It does not cover retrieval-augmented generation, multi-session memory, or tasks requiring context beyond a single DataFrame.

---

## How to cite / reproduce

To reproduce the full leaderboard:

```bash
git clone https://github.com/patibandlavenkatamanideep/RealDataAgentBench
cd RealDataAgentBench
pip install -e ".[dev]"
cp .env.example .env          # add your API key(s)
dab run --all --model gpt-4.1 # ~$0.88 for all 23 tasks
python scripts/build_leaderboard.py
```

All dataset generators are seeded. Running with the same model and `random_state` settings will reproduce the published scores within scoring tolerance.

To cite:

```bibtex
@software{patibandla2026rdab,
  author    = {Patibandla, Venkata Manideep},
  title     = {{RealDataAgentBench}: An Open Benchmark for Statistical Validity
               in LLM Data Science Agents},
  year      = {2026},
  url       = {https://github.com/patibandlavenkatamanideep/RealDataAgentBench},
  note      = {23 tasks, 4-dimensional scoring, 12 models at full coverage, human expert baseline.}
}
```

---

## License

MIT — see [LICENSE](LICENSE).

---

## Built by

[Venkata Manideep Patibandla](https://github.com/patibandlavenkatamanideep)  
Focused on LLM evaluation, agent systems, and statistically robust AI workflows.
