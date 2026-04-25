# SCORING_SPEC — RealDataAgentBench Scoring Specification

**Version:** 1.3 (April 2026) · **Status:** Current — applies to all 227 runs in the v0.1.0 leaderboard
**Source:** `realdataagentbench/scoring/` · **Scope:** Every formula, threshold, and known limitation is stated here explicitly so any reviewer can reproduce any score without reading source code.

---

## What the Four Dimensions Measure — and Why They Matter

Doing data science well means more than getting the right number. It means writing code that a colleague could read and trust, reaching the answer without burning excessive compute, and reasoning about results with the intellectual honesty a statistician would expect. RealDataAgentBench captures these four demands in four independent dimensions: **Correctness** (did the agent find the right answer?), **Code Quality** (is the code readable, vectorized, and transparent?), **Efficiency** (was the answer reached without excessive tokens or steps?), and **Statistical Validity** (did the agent report uncertainty, name the right method, and interpret findings rigorously?). Together they reward agents that behave like careful, professional data scientists — not just agents that happen to produce the right final number.

```
RDAB Score = (correctness × w_c) + (code_quality × w_q) + (efficiency × w_e) + (stat_validity × w_s)
```
Weights sum to 1.00 per task and are defined in each task's YAML. Typical profiles are shown in §5.

---

## 1. Correctness · Range 0.0–1.0

**Intent:** Check whether the agent's final written answer contains the expected facts, values, and directions. The scorer is intentionally permissive about phrasing: aliases and numeric tolerances ensure that correct answers phrased differently from the reference still receive full credit.

**How it works:** Each task defines a `ground_truth` block. The scorer applies one rule per key:

| Ground truth type | Rule |
|---|---|
| String (+ aliases) | Does the value *or* any alias appear anywhere in the lowercased answer? |
| List of strings | Does *every* string in the list appear in the answer? |
| Numeric (+ tolerance) | Does any number in the answer fall within ±tolerance of the target? Default tolerance = 15% of target. |

Score = fraction of checks that pass.

**Alias example:** Ground truth `skewness_direction: "right"` with aliases `["right-skewed", "positively skewed", "positive skew"]` — any one of those four strings passes the check.

**Numeric example:** Target `skewness_value_approx: 3.82`, tolerance `0.5` → any value in [3.32, 4.32] found in the answer passes.

| | Example output | Score |
|---|---|:---:|
| ✅ Pass | *"The income distribution is strongly right-skewed (skewness ≈ 3.85). A log transformation is recommended."* | 1.0 |
| ❌ Fail | *"I analyzed the dataset and found several interesting statistical properties worth exploring."* | 0.0 |

**Honest limitations:**
- Verbose outputs (e.g., a full numeric dump) can satisfy numeric checks by accident.
- Substring matching is not semantic: an answer saying "right-skewed — no transformation needed" still passes the direction check despite the wrong recommendation.
- No contradiction detection — correct facts alongside conflicting facts both count as passing.

---

## 2. Code Quality · Range 0.0–1.0

**Intent:** Good data science code uses vectorized libraries, avoids row-by-row loops, names variables clearly, avoids unexplained constants, and produces visible output. These aren't aesthetic preferences — they correlate with correctness, reproducibility, and maintainability. Each `run_code` block is scored on five binary checks; the final score is the mean across all blocks. No code → 0.5 (neutral).

| Check | What it rewards | ✅ Passes | ❌ Fails |
|---|---|---|---|
| **Vectorized ops** | Uses pandas/numpy rather than manual loops | `df["income"].skew()` | `for val in values: total += val` |
| **No raw loops** | No `for i in range(n)` or `while True` | `for col in df.columns:` | `for i in range(len(df)):` |
| **Descriptive names** | Zero single-letter assignments (except `i`, `n`, `df`, `x`) | `income_mean = df["income"].mean()` | `a = df["income"].mean()` |
| **No magic numbers** | ≤2 bare multi-digit literals (threshold is permissive — allows a seed + one constant) | `random_state=42` | `X[:1200]; X[1200:1500]; X[1500:1800]` |
| **Visible output** | `print(` appears in the code block | `print(f"Skewness: {val:.4f}")` | `result = df.describe()` *(silent)* |

Score per snippet = checks passed / 5. Final = mean across snippets.

**Honest limitations:**
- Evaluates code *form*, not code *correctness* — a well-styled snippet can score 1.0 while computing the wrong statistic.
- Multi-snippet averaging may mask quality degradation in later tool calls.

---

## 3. Efficiency · Range 0.0–1.0

**Intent:** An agent that uses 10× the tokens of another to reach the same answer is less efficient and more expensive. This dimension rewards staying within a calibrated token budget and penalizes excessive steps. Error runs are penalized 50%.

**Token budgets** (calibrated on Claude Sonnet 4.6 runs):

| Difficulty | Budget | Why |
|---|:---:|---|
| Easy | 20,000 | Straightforward single-operation tasks |
| Medium | 50,000 | Multi-step analysis with exploration |
| Hard | 30,000 | Focused subtasks — thoroughness ≠ verbosity |

**Formula:**
```
token_score = max(0, 1 − max(0, tokens/budget − 1))   # linear penalty above budget; 2× = 0.0
step_score  = max(0, 1 − max(0, steps/max_steps − 1) × 0.5)   # softer step penalty
efficiency  = token_score × 0.6 + step_score × 0.4
if error: efficiency × 0.5
```

**Worked examples:**

| Scenario | Score |
|---|:---:|
| Clean run, well under budget | **1.000** |
| Exactly at token budget and step limit | **1.000** |
| 2× over token budget, no error | **0.400** |
| Claude Haiku feat_005: 608,861 tokens, 28/20 steps | **0.130** |
| Error run, under budget | **0.500** |

**Honest limitations:**
- Budgets were calibrated on Claude Sonnet 4.6. GPT-4.1-mini and Llama 3.3-70b produce shorter responses structurally, giving them an efficiency advantage unrelated to task quality. **Per-model budget calibration is planned.**
- Hard tasks have a smaller budget than medium by design, which means methodical reasoning on hard tasks is penalized more heavily.

---

## 4. Statistical Validity · Range 0.25 / 0.50 / 0.75 / 1.00

**Intent:** A rigorous data scientist reports uncertainty, names the appropriate method, interprets results in context, and avoids p-hacking. This dimension checks for those four qualities using vocabulary signals in the final answer. All four checks are **category-aware** — each task category has its own vocabulary lists for Checks 2 and 3.

Score = checks passed / 4 (increments of 0.25). Minimum achievable score ≈ 0.25 (Check 4 almost always passes by default).

### Check 1 — Uncertainty Quantification

Does the answer quantify uncertainty using any of: *p-value, confidence interval, std, standard deviation, standard error, approximately, range, bootstrap, variance, stability, robustness, reliability, prediction interval, error bar, margin of error*.

| ✅ Passes | ❌ Fails |
|---|---|
| *"mean ≈ $52k with std $18.4k"* | *"mean is $52,341"* |
| *"AUC = 0.84 (bootstrap 95% CI: 0.79–0.89)"* | *"AUC is 0.84"* |

### Check 2 — Appropriate Method Vocabulary (category-specific)

Does the answer name a method appropriate to the task category?

| Category | Example patterns that pass |
|---|---|
| `eda` | *pearson, spearman, correlation, IQR, z-score, skewness, kurtosis, log transform, normalization* |
| `statistical_inference` | *t-test, z-test, chi-squared, Mann-Whitney, ANOVA, null hypothesis, degrees of freedom, two-proportion* |
| `modeling` | *cross-validation, ROC-AUC, precision, recall, F1-score, confusion matrix, regularization, RMSE, learning curve* |
| `feature_engineering` | *one-hot encoding, label encoding, imputation, feature selection, interaction term, SMOTE, target encoding, rolling* |
| `ml_engineering` | *nested CV, data leakage, calibration, ensemble, hyperparameter, pipeline, stratification, Brier score, bootstrap* |
| *(unknown)* | Always fails — no fallback to EDA vocabulary |

### Check 3 — Analytical Interpretation (category-specific)

Does the answer show analytical understanding beyond reporting a bare number? Each category has its own interpretation signals — this prevents EDA-specific language from being the only way to pass.

| Category | Example signals that pass |
|---|---|
| `eda` | *correlation does not imply causation, controlling for, confounding, Simpson's paradox, spurious, statistically significant* |
| `statistical_inference` | *statistically significant, reject null, effect size, practical significance, Type I error, normality assumption* |
| `modeling` | *overfitting, generalization, bias-variance, selection bias, class imbalance, threshold, interpret, stability* |
| `feature_engineering` | *multicollinearity, leakage, stability, ordinal relationship, dimensionality, sparsity* |
| `ml_engineering` | *selection bias, optimistic bias, leakage, calibration, reliability, stratification, class imbalance* |
| *(unknown)* | Falls back to EDA interpretation list |

### Check 4 — Absence of P-Hacking Signals

Does the answer avoid phrases suggesting the method was chosen to achieve significance? Patterns: *tried different methods until significant, p just below 0.05*.

This check has not fired in over 300 benchmark runs — it is aspirational but retained as a guard against future failure modes.

---

**Worked example — `stat_001` (A/B test, category: `statistical_inference`):**

Answer: *"The two-proportion z-test gives p = 0.0001 (z = 3.89). We reject the null hypothesis. Effect size is small (lift = 2.1 percentage points). The result is statistically significant but check practical significance given the cost of the intervention."*

- Check 1 ✓ — "p = 0.0001" matches uncertainty patterns
- Check 2 ✓ — "z-test" matches statistical_inference method vocab
- Check 3 ✓ — "reject the null", "statistically significant", "practical significance" match interp patterns
- Check 4 ✓ — no p-hacking signals
- **Score = 1.00**

**Worked example — `feat_002` (feature selection, category: `feature_engineering`):**

Answer: *"Applied one-hot encoding to categorical columns. Random forest feature importance: income = 0.32, age = 0.18, credit = 0.11."*

- Check 1 ✓ — "importance" does not match; but "range" or similar… actually no uncertainty language → ✗
- Check 2 ✓ — "one-hot encoding" matches feature_engineering vocab
- Check 3 ✗ — no leakage/stability/multicollinearity mention
- Check 4 ✓ — no p-hacking signals
- **Score = 0.50**

---

## 5. Composite Score and Weights

```
RDAB Score = (correctness × w_c) + (code_quality × w_q) + (efficiency × w_e) + (stat_validity × w_s)
```

| Category | Correctness | Code Quality | Efficiency | Stat. Validity |
|---|:---:|:---:|:---:|:---:|
| EDA | 0.50 | 0.20 | 0.15 | 0.15 |
| Feature Engineering | 0.45 | 0.20 | 0.15 | 0.20 |
| Modeling | 0.40 | 0.15 | 0.15 | 0.30 |
| Statistical Inference | 0.40 | 0.15 | 0.15 | 0.30 |
| ML Engineering | 0.45 | 0.20 | 0.15 | 0.20 |

Individual tasks may deviate (e.g., `eda_003` uses `stat_validity: 0.25`). Exact weights are in each task's YAML.

**Ranking eligibility:** A model must complete ≥80% of tasks (≥19/23) to appear in the ranked leaderboard. Models below this threshold appear in a separate "partial coverage" section with a `†` footnote and no rank number. This prevents a model that ran only easy tasks from being compared against one that ran all difficulties.

---

## 6. Human Baseline

No human expert baseline currently exists in this benchmark. Recruiting domain experts to solve a representative subset of tasks under the same conditions is planned for a future iteration. Until then, model scores should be interpreted relative to each other, not against a human reference point.

---

## 7. How to Independently Verify Any Score

No source code required. Any reviewer can follow these steps:

1. **Get the trace.** Find the JSON trace for the model + task. It contains `final_answer`, all tool calls, `total_input_tokens`, `total_output_tokens`, `num_steps`, and `error`.

2. **Score statistical validity.** Apply the regex patterns from §4 Checks 1–4 against `final_answer` (case-insensitive). Use the task's category to select the correct Check 2 (method vocab) and Check 3 (interpretation) pattern list. `stat_validity = (c1 + c2 + c3 + c4) / 4`.

3. **Score code quality.** Extract all `tool_input` values where `tool_name == "run_code"`. Apply the 5 binary checks from §2 to each. Average across snippets. (No snippets → 0.5.)

4. **Score efficiency.** Sum input + output tokens. Look up the difficulty budget from §3. Apply the token\_score and step\_score formulas. Apply ×0.5 if `error` is non-null.

5. **Score correctness.** Open the task YAML, read `ground_truth`. For each key, apply the matching rule from the §1 table. `correctness = checks_passed / total_keys`.

6. **Compute RDAB Score.** Use the task's YAML weights (or the category defaults from §5):
   `RDAB Score = correctness × w_c + code_quality × w_q + efficiency × w_e + stat_validity × w_s`

7. **Compare.** Round to 4 decimal places. A discrepancy > 0.001 from the leaderboard value should be filed as a [GitHub issue](https://github.com/Venkatamanideep09/RealDataAgentBench/issues) with the task ID, model name, and observed vs. expected score.

---

## 8. Honest Limitations — What We Know and Plan to Fix

| ID | Dimension | Description | Status |
|---|---|---|---|
| ~~**L1**~~ | ~~Stat Validity~~ | ~~Check 2 vocabulary is EDA-only~~ | ✅ **Fixed in v1.4** — all four checks are now category-aware |
| **L2** | Efficiency | Token budgets calibrated on Claude Sonnet 4.6, not model-agnostic | 🔴 High priority — planned fix |
| **L3** | Stat Validity | Check 1 accepts weak hedges ("approximately", "range") as uncertainty | 🟡 Known, acceptable tradeoff |
| **L4** | Stat Validity | Check 3 detects vocabulary, not reasoning quality — can't verify that "confidence interval" was correctly computed | 🟡 Mitigated by LLM-judge calibration script |
| **L5** | Stat Validity | Check 4 (p-hacking) has never fired — aspirational guard | 🟡 Retained; patterns tightened in future iterations |
| **L6** | Correctness | Verbose numeric outputs can pass checks by accidental inclusion | 🟡 Partially mitigated by task design |
| **L7** | Correctness | No contradiction detection across sentences | 🟠 Known fundamental limit of string scoring |
| **L8** | Code Quality | Evaluates code form, not code correctness | ⚪ By design |
| **L9** | Code Quality | Multi-snippet averaging may mask late-run quality issues | 🟢 Low impact, known |

---

## 9. Changelog

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-04-01 | Initial spec — all 4 dimensions, 227 v0.1.0 runs |
| 1.1 | 2026-04-17 | Added L9 (efficiency calibration bias), score floor table, reproducibility checklist |
| 1.2 | 2026-04-18 | Added coverage threshold, real vs. synthetic classification, pass/fail examples, verification checklist |
| 1.3 | 2026-04-18 | Condensed for print readability; promoted L1 and L2 to high priority |
| **1.4** | **2026-04-25** | **Fixed L1: all four checks now category-aware. Check 3 (interpretation) has per-category signal lists for modeling/feature-engineering/ML engineering/stat-inference. Expanded Check 1 uncertainty vocab (bootstrap, variance, stability, robustness). Added `--temperature` flag for deterministic multi-run mode. 7 new tests.** |

---

> **All scores in the leaderboard were computed using this specification.** The scoring logic in `realdataagentbench/scoring/` implements exactly the formulas, regex patterns, and thresholds described here. Any discrepancy between a score you compute by following this document and the score shown in the leaderboard should be reported as a [GitHub issue](https://github.com/Venkatamanideep09/RealDataAgentBench/issues) with the task ID, model name, and observed discrepancy.
