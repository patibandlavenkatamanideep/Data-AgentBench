# SCORING_SPEC — RealDataAgentBench Scoring Specification

**Version:** 1.2 (April 2026)
**Status:** Current — applies to all 227 runs in the v0.1.0 leaderboard, and all runs thereafter.
**Source of truth:** `realdataagentbench/scoring/`

---

## What This Document Is

RealDataAgentBench evaluates AI agents on real data science tasks. This document explains, in plain English, exactly how every score in the leaderboard is computed — including the formulas, the thresholds, and the known weaknesses of the current approach. The goal is transparency: any researcher, recruiter, or contributor should be able to read this document and independently verify any score without ever touching the source code.

---

## Overview: The Four Dimensions

Each agent run is scored on four independent dimensions that together reflect what it means to do data science well. **Correctness** asks whether the agent found the right answer. **Code Quality** asks whether the agent's code follows sound data science practices — using vectorized operations, avoiding raw loops, naming things clearly. **Efficiency** asks whether the agent reached its answer without excessive token usage or unnecessary steps. **Statistical Validity** asks whether the agent reasoned about its findings rigorously — reporting uncertainty, naming the right statistical methods, and interpreting results carefully.

These four dimensions are combined into a single **RDAB Score** using per-task weights that reflect which dimension matters most for that task type:

```
RDAB Score = (correctness × w_c) + (code_quality × w_q) + (efficiency × w_e) + (stat_validity × w_s)
```

Weights always sum to 1.00 for every task and are defined in the task's YAML file.

---

## 1. Correctness

**Range:** 0.0–1.0
**What it measures:** Does the agent's final written answer contain the correct conclusions for this task?

### Intent

This dimension checks whether the agent's final response contains the expected facts, values, and directions — as defined by each task's `ground_truth` YAML block. It is intentionally broad: an answer that says "the income distribution is right-skewed with a skewness of approximately 3.9" passes even if phrased differently from the reference answer. Ground truth entries can specify synonyms (aliases) and numeric tolerances so that paraphrase and rounding do not penalize a correct answer.

### How it works

The scorer iterates over every key in the task's `ground_truth` block. For each key, it runs one of these checks:

| Value type | How it's checked |
|---|---|
| String | Does the primary value or any alias appear anywhere in the lowercased answer? |
| List of strings | Does **every** string in the list appear in the answer? |
| Boolean (`True`) | Does any alias for this key appear in the answer? |
| Numeric with tolerance | Does any number in the answer fall within the stated tolerance of the target value? |

The final correctness score is the fraction of checks that pass.

**Numeric tolerance example:** If the ground truth specifies `skewness_value_approx: 3.82` with a `skewness_tolerance: 0.5`, then any numeric value between 3.32 and 4.32 found anywhere in the answer will pass. Numbers are extracted with the pattern `[-+]?\d+\.?\d*`.

**Alias example:**
```yaml
ground_truth:
  skewness_direction: "right"
  skewness_direction_aliases:
    - "right-skewed"
    - "positively skewed"
    - "positive skew"
```
The answer passes if it contains "right", "right-skewed", "positively skewed", or "positive skew" — any one of them is sufficient.

### Pass vs. fail examples

**Passes (score: 1.0):**
> "The income distribution is strongly right-skewed (skewness ≈ 3.85). A log transformation is recommended before modeling."

This passes because "right-skewed" matches the alias list and 3.85 falls within the 0.5 tolerance of 3.82.

**Fails (score: 0.0):**
> "I analyzed the dataset and computed several statistics. The data has interesting properties worth exploring."

No numeric value near 3.82 appears, and no skewness direction word is present.

### Honest limitations

- **Verbose outputs can pass by accident.** An agent that dumps a large table of numbers may incidentally include a value near the target. This is most relevant to EDA tasks with numeric ground truth.
- **Substring matching is not semantic understanding.** An answer that says "right-skewed income distribution — no transformation needed" still passes the direction check, even though the recommendation contradicts the correct action.
- **No contradiction detection.** The scorer cannot identify cases where a model gives a correct fact in one sentence and a conflicting fact in another.

---

## 2. Code Quality

**Range:** 0.0–1.0
**What it measures:** Does the agent's code follow sound data science coding practices?

### Intent

Good data science code should use vectorized libraries (pandas, numpy) rather than slow Python loops, use descriptive variable names, avoid unexplained magic numbers, and produce visible output. This dimension penalizes lazy or opaque code — not because style is cosmetic, but because code quality correlates with reliability and maintainability. Each block of code the agent runs is scored on five binary checks; the final score is the average across all code blocks.

If an agent writes no code at all, it receives a neutral score of 0.5.

### The five checks

#### Check 1: Uses vectorized operations

**Intent:** Rewards agents that use pandas/numpy operations rather than reimplementing statistics manually.

Passes if the code contains any of: `df["..."]`, `.mean()`, `.std()`, `.sum()`, `.corr(`, `.groupby(`, `np.`, `stats.`

**Passes:** `skewness = df["income"].skew()`
**Fails:** `total = 0; for val in values: total += val; mean = total / len(values)`

#### Check 2: Avoids raw index loops

**Intent:** Penalizes row-by-row iteration when a vectorized alternative exists. Only `range()`-based loops are flagged — iterating over columns (`for col in df.columns`) is acceptable.

Passes if the code does **not** contain `for i in range(n)` or `while True`.

**Passes:** `for col in df.select_dtypes("number").columns:`
**Fails:** `for i in range(len(df)): result[i] = df.iloc[i]["income"] * 2`

#### Check 3: Descriptive variable names

**Intent:** Single-letter variable names (other than conventional exceptions) make code harder to review and debug.

Passes if there are zero single-letter variable assignments outside of `i`, `n`, `df`, and `x`.

**Passes:** `income_mean = df["income"].mean()`
**Fails:** `a = df["income"].mean(); b = df["age"].std()`

#### Check 4: No magic numbers

**Intent:** Bare numeric literals that appear without explanation are a code smell. Named constants communicate intent.

Passes if there are ≤2 bare numeric literals ≥2 digits that are not 0, 1, 2, or 100. The threshold of ≤2 is deliberately permissive to allow a seed value and one domain constant.

**Passes:** `TRAIN_SPLIT = 0.8; X_train, X_test = train_test_split(X, test_size=1-TRAIN_SPLIT, random_state=42)`
**Fails:** `X_train = X[:1200]; X_test = X[1200:1500]; val = X[1500:1800]`

#### Check 5: Produces visible output

**Intent:** Ensures the agent's code prints results rather than computing silently. Silent code cannot be verified by inspection of the run trace.

Passes if `print(` appears anywhere in the code block.

**Passes:** `print(f"Skewness: {df['income'].skew():.4f}")`
**Fails:** `result = df["income"].describe()` *(no print)*

### Score formula

```
score per snippet = (checks passed) / 5
final code_quality = mean(scores across all run_code snippets)
```

### Honest limitations

- **This evaluates form, not correctness.** A well-styled snippet can score 1.0 while computing the wrong statistic.
- **Check 3 only flags assignments.** A single-letter variable used purely in indexing (`df[a]`) may not be caught.
- **Multi-snippet averaging can mask quality degradation.** A model that writes clean code early but messy code in later tool calls will average them together.

---

## 3. Efficiency

**Range:** 0.0–1.0
**What it measures:** Did the agent solve the task without excessive token usage or unnecessary steps?

### Intent

An agent that uses 10× the tokens of another to reach the same answer is less efficient — it is more expensive to run, slower, and suggests the agent is reasoning in circles or producing excessive filler. This dimension rewards agents that stay within a reasonable token budget for their task difficulty, and applies a softer penalty for using too many steps. Runs that terminate in an error are penalized by 50%.

### Token budgets

Budgets were calibrated from observed Claude Sonnet 4.6 runs:

| Difficulty | Token budget |
|---|:---:|
| Easy | 20,000 |
| Medium | 50,000 |
| Hard | 30,000 |

Hard tasks have a lower budget than medium by design: hard tasks have focused, well-scoped subtasks that should not require extensive exploration. A hard task that consumes medium-task token levels is being inefficient.

### Formula

```
token_ratio = total_tokens / budget
step_ratio  = steps_used  / max_steps

token_score = max(0.0, 1.0 - max(0.0, token_ratio - 1.0))
# At budget → 1.0. Double the budget → 0.0. Triple → 0.0.

step_score  = max(0.0, 1.0 - max(0.0, step_ratio - 1.0) × 0.5)
# Step overrun is penalized more gently than token overrun.

raw_efficiency = token_score × 0.6 + step_score × 0.4

if run terminated in error:
    final_efficiency = raw_efficiency × 0.5
else:
    final_efficiency = raw_efficiency
```

### Worked examples

| Scenario | Tokens | Steps | Max steps | Difficulty | Error | Score |
|---|---:|---:|---:|---|---|:---:|
| Clean run, under budget | 15,000 | 5 | 20 | Easy | No | **1.000** |
| Exactly at budget and step limit | 20,000 | 20 | 20 | Easy | No | **1.000** |
| 2× over token budget | 40,000 | 20 | 20 | Easy | No | **0.400** |
| Claude Haiku on feat_005 (extreme overrun) | 608,861 | 28 | 20 | Hard | No | **0.130** |
| Errored, under budget | 10,000 | 3 | 20 | Easy | Yes | **0.500** |

### Honest limitations

- **Budgets are not model-agnostic.** Calibration used Claude Sonnet 4.6. Models like GPT-4.1-mini or Llama 3.3-70b naturally use fewer tokens per response, giving them a structural efficiency advantage unrelated to task quality. This is a known bias we plan to address with per-model budget calibration.
- **Hard tasks penalize thoroughness more than medium tasks.** This is intentional but means a model that is appropriately methodical on a hard task may be penalized more than one that cuts corners.

---

## 4. Statistical Validity

**Range:** 0.25, 0.50, 0.75, or 1.00 (four binary checks, each worth 0.25)
**What it measures:** Does the agent's final answer reflect rigorous statistical reasoning?

### Intent

A data scientist should not just compute a number — they should report uncertainty, name the method they used, interpret results carefully, and avoid fishing for significance. This dimension checks for four qualities in the final answer text: does the agent acknowledge uncertainty? Does it name an appropriate statistical method? Does it reason about what the result means? Does it show no signs of p-hacking?

These checks are deliberately broad to be model-agnostic: they look for vocabulary signals in plain text, not for any specific format.

### Check 1: Reports uncertainty

Passes if the answer contains any of these phrases (case-insensitive):

`p-value`, `confidence interval`, `CI`, `std`, `standard deviation`, `standard error`, `p = 0.0...`, `r = [number]`, `approximately`, `around`, `range`

**Passes:** "The mean income is approximately $52,000 with a standard deviation of $18,400."
**Fails:** "The mean income is $52,341."

> Note: Weak hedges like "approximately" and "around" satisfy this check without formal uncertainty quantification. This is a known tradeoff between recall and precision.

### Check 2: Names an appropriate statistical method

Passes if the answer contains any of: `pearson`, `spearman`, `correlation`, `IQR`, `z-score`, `skewness`, `kurtosis`, `histogram`, `box plot`, `log transform`, `normalization`, `normalise`

**Passes (EDA):** "The Pearson correlation between income and age is 0.43."
**Fails (non-EDA, known bug):** "The logistic regression achieved 87% accuracy on the held-out set." *(logistic regression not in list)*

> **Known limitation:** This vocabulary list covers EDA methods only. On non-EDA tasks (modeling, feature engineering, ML engineering, statistical inference), this check will almost always fail regardless of how appropriate the agent's method is. A model that correctly runs a t-test, chi-squared test, or cross-validation cannot pass this check because those terms are not in the list. This is the primary reason non-EDA tasks have a structural score ceiling of 0.75 on this dimension. See the limitations section for full impact.

### Check 3: Interprets results correctly

Passes if the answer contains any of: `correlation does not imply causation`, `controlling for`, `adjusting for`, `partial correlation`, `confounder`/`confounding`, `Simpson`, `spurious`, `statistically significant`, `not significant`, `skew`/`skewed`, `distribution`

**Passes:** "While income and health outcomes are correlated, this does not imply causation — confounding variables like access to healthcare are likely present."
**Fails:** "Income and health are related (r = 0.52)." *(result stated without interpretation)*

> Note: Common words like "distribution" and "skew" appear in many EDA responses, so this check passes frequently on EDA tasks. It passes less often on modeling and ML tasks unless the agent explicitly discusses statistical assumptions.

### Check 4: No p-hacking signals

Passes if the answer does **not** contain: `tried...different...method`, `until...significant`, `p...just...below...0.05`

**These patterns have never fired in 227 runs.** This check currently passes unconditionally and contributes +0.25 to every score. It is an aspirational check — designed for a class of outputs that does not yet appear in the benchmark — but it is currently uninformative as a discriminating signal.

### Effective score ranges by task category

Due to the EDA-only vocabulary limitation in Check 2:

| Category | Check 2 can pass? | Typical score range |
|---|---|:---:|
| EDA (3 tasks) | Yes | 0.50–0.75 |
| Feature Engineering (5 tasks) | **No** | **0.25** |
| Modeling (5 tasks) | **No** | **0.25** |
| Statistical Inference (5 tasks) | **No** | **0.25** |
| ML Engineering (5 tasks) | **No** | **0.25** |

The 0.25 floor on non-EDA tasks reflects: Check 4 always passes (+0.25), Check 2 structurally fails (0), and Checks 1 and 3 rarely pass on non-EDA outputs. Most non-EDA outputs score exactly 0.25.

### Honest limitations

These are limitations we have documented and plan to improve:

- **L1 (Critical): Check 2 only covers EDA vocabulary.** Non-EDA tasks cannot achieve more than 0.75 on this dimension. A future version will extend the vocabulary list to cover modeling, inference, and ML engineering methods.
- **L2: Check 1 accepts weak hedges.** Words like "approximately" satisfy the uncertainty check without requiring formal statistical reporting. A future version will require stronger signals for full credit.
- **L3: All checks are vocabulary-driven.** No check understands what the agent is saying — only whether specific words appear. A semantically correct answer phrased unusually may fail; a superficially correct answer may pass.
- **L4: Check 4 is currently uninformative.** It has never fired. Its purpose is correct but its current patterns are too narrow to discriminate.

---

## 5. Composite RDAB Score

**Range:** 0.0–1.0

```
RDAB Score = (correctness × w_c) + (code_quality × w_q) + (efficiency × w_e) + (stat_validity × w_s)
```

Weights are defined per-task in the YAML `scoring:` block and always sum to 1.00.

### Weight profiles by task category

| Category | Correctness | Code Quality | Efficiency | Stat. Validity |
|---|:---:|:---:|:---:|:---:|
| EDA | 0.50 | 0.20 | 0.15 | 0.15 |
| Feature Engineering | 0.45 | 0.20 | 0.15 | 0.20 |
| Modeling | 0.40 | 0.15 | 0.15 | 0.30 |
| Statistical Inference | 0.40 | 0.15 | 0.15 | 0.30 |
| ML Engineering | 0.45 | 0.20 | 0.15 | 0.20 |

These are representative values. Individual tasks may deviate slightly (e.g., `eda_003` with Simpson's Paradox has `stat_validity_weight: 0.25`). The exact weights for each task are in its YAML file.

---

## 6. Ranking Eligibility

To appear in the **ranked leaderboard**, a model must have completed at least **80% of the current task set** (currently ≥19 of 23 tasks).

**Why this threshold exists:** A model that ran only easy tasks would have a structurally inflated score compared to a model that ran all difficulties. The 80% threshold ensures that ranked comparisons are meaningful.

**Partial coverage models** (below 80%) appear in a separate section with a dashed border, reduced opacity, a "partial" tag, and a `†` footnote. They are not assigned a rank number and do not appear in the main model cards ranking.

---

## 7. Real Data vs. Synthetic Task Classification

Every task in RDAB is classified as either `synthetic` or `real_data` in the task YAML under `dataset.data_source`.

### Synthetic tasks (17 tasks)

Data is generated by seeded Python scripts with fixed parameters. Running the same generator twice produces byte-identical output. Ground truth is computed analytically from the generator's output and recorded in the YAML at task-creation time.

> **Limitation:** Synthetic data may be easier or harder than equivalent real-world data. Models that have encountered similar synthetic distributions in training may receive inflated scores.

### Real-data tasks (6 tasks)

Data is loaded from publicly licensed external sources — the UCI Machine Learning Repository or scikit-learn's built-in datasets.

| Task | Dataset | Source | License |
|---|---|---|---|
| `eda_004` | Breast Cancer Wisconsin | UCI / sklearn | CC BY 4.0 |
| `eda_005` | Iris | UCI / sklearn | Public domain |
| `feat_006` | Diabetes | sklearn | BSD-3 |
| `model_006` | Wine Recognition | UCI / sklearn | CC BY 4.0 |
| `stat_006` | Iris (ANOVA task) | UCI / sklearn | Public domain |
| `mod_006` | Breast Cancer Wisconsin (CV task) | UCI / sklearn | CC BY 4.0 |

Ground truth for real-data tasks is independently verifiable: any reviewer can load the same dataset from sklearn and apply the same operations to confirm the expected output. These tasks cannot be overfitted to a synthetic distribution the benchmark author controls.

---

## 8. How to Independently Verify a Score

Any reviewer can verify a leaderboard score by following these steps. No benchmark source code is required.

**Step 1 — Locate the run trace.**
Find the JSON trace file for the model and task you want to verify. The trace contains `final_answer`, all tool calls, `total_input_tokens`, `total_output_tokens`, `num_steps`, and `error`.

**Step 2 — Verify statistical validity (Section 4).**
Apply the regex patterns from Checks 1–4 against `final_answer` (case-insensitive). Each check is binary. `stat_validity = (check1 + check2 + check3 + check4) / 4`.

**Step 3 — Verify code quality (Section 2).**
Extract all `tool_input` values from steps where `tool_name == "run_code"`. Apply the five binary checks from Section 2 to each snippet. Average the per-snippet scores. If no code snippets exist, code_quality = 0.5.

**Step 4 — Verify efficiency (Section 3).**
Sum `total_input_tokens + total_output_tokens`. Look up the budget for the task's difficulty from Section 3. Apply the token_score and step_score formulas. Apply the 50% error multiplier if `trace.error` is non-null.

**Step 5 — Verify correctness (Section 1).**
Open the task's YAML file and read the `ground_truth` block. For each key, apply the matching rule from the table in Section 1. `correctness = checks_passed / total_checks`.

**Step 6 — Compute the RDAB Score.**
Look up the task's weight profile from Section 5 (or the exact weights in its YAML). Compute:
```
RDAB Score = (correctness × w_c) + (code_quality × w_q) + (efficiency × w_e) + (stat_validity × w_s)
```

**Step 7 — Compare to the leaderboard.**
Round to 4 decimal places. If your result differs from the displayed score by more than 0.001 (to account for floating-point differences), open a GitHub issue with the task ID, model name, and the discrepancy you found.

---

## 9. Summary of Known Limitations

We document these limitations openly because we believe transparency about a benchmark's weaknesses is more useful than silence about them. All of these are candidates for improvement in future versions.

| ID | Dimension | Description | Priority |
|---|---|---|---|
| L1 | Stat Validity | Check 2 is EDA-only; non-EDA tasks cannot pass it — this is the primary driver of the 0.25 floor | High — planned fix |
| L2 | Stat Validity | Check 1 accepts weak hedges ("approximately", "around") without formal uncertainty | Medium |
| L3 | Stat Validity | All checks are vocabulary-based, not semantically aware | Medium |
| L4 | Stat Validity | Check 4 (p-hacking) has never fired in 227 runs — uninformative | Low |
| L5 | Correctness | Verbose outputs can pass numeric checks by inclusion | Medium |
| L6 | Correctness | No contradiction detection — conflicting sentences are not caught | Medium |
| L7 | Code Quality | Evaluates code form, not whether the code is correct | By design |
| L8 | Code Quality | Multi-snippet averaging may mask quality degradation in later tool calls | Low |
| L9 | Efficiency | Token budgets calibrated on Claude Sonnet 4.6, not model-agnostic | High — planned fix |

---

## 10. Changelog

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-04-01 | Initial spec covering all 4 dimensions; reflects all 227 v0.1.0 runs |
| 1.1 | 2026-04-17 | Added L9 (efficiency calibration bias), Section 5.5 score floor table, Section 9 checklist |
| 1.2 | 2026-04-18 | Added coverage threshold (Section 6), real vs. synthetic data classification (Section 7), plain-English intent blocks, pass/fail examples, and verification checklist |

---

> **All scores in the leaderboard were computed using this specification.** The scoring logic in `realdataagentbench/scoring/` implements exactly the formulas, regex patterns, and thresholds described here. Any discrepancy between a score you compute by following this document and the score shown in the leaderboard should be reported as a [GitHub issue](https://github.com/Venkatamanideep09/RealDataAgentBench/issues) with the task ID, model name, and observed discrepancy.
