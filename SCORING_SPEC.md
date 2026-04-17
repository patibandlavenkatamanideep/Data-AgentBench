# SCORING_SPEC — RealDataAgentBench Scoring Specification

**Version:** 1.1 (April 2026)  
**Status:** Current — applies to all 227 runs in the v0.1.0 leaderboard, and all runs thereafter.  
**Source of truth:** `realdataagentbench/scoring/`

> This document exists so that any reviewer, researcher, or contributor can
> independently reproduce any score in the leaderboard without reading source code.
> Every formula, threshold, regex, and edge case is stated here explicitly.

---

## 1. Overview

Each agent run produces a JSON trace file containing:
- `trace.final_answer` — the agent's written response to the task
- `trace.steps[]` — each tool call with `tool_name`, `tool_input`, and `tool_output`
- `trace.total_input_tokens`, `trace.total_output_tokens`
- `trace.num_steps`
- `trace.error` — non-null if the run terminated in an error

The `CompositeScorer` (`scoring/composite.py`) extracts these fields and passes them to four independent sub-scorers. The final **RDAB Score** is their weighted sum using per-task weights defined in each task's YAML.

```
RDAB Score = correctness  × w_c
           + code_quality × w_q
           + efficiency   × w_e
           + stat_validity × w_s
```

Where `w_c + w_q + w_e + w_s = 1.00` for every task.

---

## 2. Correctness Scorer

**Source:** `scoring/correctness.py`  
**Range:** 0.0–1.0 (float, rounded to 4 decimal places)  
**Input:** `trace.final_answer` (string), `task.ground_truth` (dict from YAML)

### 2.1 Algorithm

The scorer iterates over every key in `ground_truth` (excluding `*_aliases` and `*_tolerance` / `*_approx` suffix keys — those are consumed by their primary key). For each key it runs one check:

| Value type | Check |
|---|---|
| `str` | Does the primary value OR any alias in `{key}_aliases` appear as a substring in `answer.lower()`? |
| `list[str]` | Does **every** string in the list appear in `answer.lower()`? |
| `bool (True)` | Do any aliases in `{key}_aliases` appear in `answer.lower()`? (Only checked when value is `True`) |
| `float/int` with `{key}_approx` | Is there any numeric token in the answer within `tolerance` of `approx`? Default tolerance = 15% of approx if not specified. |
| `float/int` without `{key}_approx` | Skipped — raw numeric keys without `_approx` are metadata only. |

All checks are Boolean. The final score is `sum(checks) / len(checks)`.

### 2.2 Numeric matching

```python
# Any float literal in the answer is extracted with:
pattern = r"[-+]?\d+\.?\d*"

# A match passes if:
abs(candidate_value - target_approx) <= tolerance
```

Example: if `ground_truth["skewness_value_approx"] = 3.82` with `skewness_tolerance = 0.5`,
then any value in [3.32, 4.32] that appears as a number in the answer passes.

### 2.3 Alias expansion

```yaml
# In the task YAML:
ground_truth:
  skewness_direction: "right"
  skewness_direction_aliases:
    - "right-skewed"
    - "positively skewed"
    - "positive skew"
```

The scorer checks: does `"right"` OR `"right-skewed"` OR `"positively skewed"` OR `"positive skew"` appear in `answer.lower()`?

### 2.4 Known limitations

- **Verbose outputs can pass by inclusion.** A model that outputs a large dump of numbers will satisfy numeric checks as a side-effect of verbosity. This is most relevant to EDA tasks where correctness is partially numeric.
- **String checks are substring, not exact.** An answer that contains "right-skewed income distribution" passes the `skewness_direction` check even if it then incorrectly recommends no transformation.
- **No semantic understanding.** The scorer cannot detect contradictions in the final answer.

---

## 3. Code Quality Scorer

**Source:** `scoring/code_quality.py`  
**Range:** 0.0–1.0 (float, rounded to 4 decimal places)  
**Input:** list of code strings extracted from `tool_name == "run_code"` steps in the trace

### 3.1 Algorithm

Each `run_code` call is scored independently. If multiple code snippets exist, the final score is the mean over all snippets. If no code snippets exist, the score is `0.5` (neutral).

Five binary checks are applied per snippet:

#### Check 1 — Vectorized operations (`uses_vectorized_ops`)

**Passes if** any of these regex patterns match the code:

```python
r"df\["           # pandas column access
r"\.mean\(\)"     # pandas/numpy aggregation
r"\.std\(\)"
r"\.sum\(\)"
r"\.corr\("
r"\.groupby\("
r"np\."           # any numpy operation
r"stats\."        # any scipy.stats operation
```

**Intent:** Rewards code that uses pandas/numpy vectorized operations rather than manual Python logic.

#### Check 2 — Avoids raw loops (`avoids_raw_loops`)

**Passes if none** of these patterns match:

```python
r"\bfor\s+\w+\s+in\s+range\("   # for i in range(n) — raw index loop
r"\bwhile\s+True"               # infinite loop pattern
```

**Intent:** Penalizes row-by-row iteration in Python when a vectorized equivalent exists. Note: `for col in df.columns` does NOT trigger this check — only `range()`-based loops.

#### Check 3 — Descriptive variable names (`uses_descriptive_names`)

**Passes if** there are **zero** single-letter variable assignments (excluding `i`, `n`, `df`, and `x`):

```python
single_letter = re.findall(r"\b([a-eg-moq-wyz])\s*=", code)
passes = len(single_letter) == 0
```

**Excluded from flagging:** `i` (loop index), `n` (sample size), `df` (dataframe convention), `x` (axis). All others (e.g., `a = ...`, `b = ...`, `c = ...`) count as non-descriptive.

#### Check 4 — No magic numbers (`no_magic_numbers`)

**Passes if** there are ≤2 bare numeric literals ≥2 digits that are not 0, 1, 2, or 100:

```python
magic = re.findall(
    r"(?<![=\w])\b(?!0\b|1\b|2\b|100\b)\d{2,}\b(?!\s*[=\w])", code
)
passes = len(magic) <= 2
```

**Intent:** Allows common constants (`42` as a seed, `80` in an 80/20 split) but flags repeated bare literals that should be named constants. The threshold of ≤2 is permissive by design.

#### Check 5 — Has print output (`has_print_output`)

**Passes if** `"print("` appears anywhere in the code.

**Intent:** Ensures the agent produces visible output during execution, not just silent computation.

### 3.2 Score formula

```python
checks = [vectorized, no_loops, descriptive, no_magic, has_print]
score = sum(checks) / 5   # per snippet
final_score = mean(scores_per_snippet)
```

### 3.3 Known limitations

- **Evaluates syntax, not correctness.** A snippet can score 1.0 for code quality while computing the wrong answer.
- **Check 3 regex matches assignment context only.** A single-letter variable used only in indexing (`df[a]`) may not be flagged.
- **Multi-snippet averaging.** A model that writes one good snippet and one bad snippet will average them. This can mask systematic quality issues in later tool calls.

---

## 4. Efficiency Scorer

**Source:** `scoring/efficiency.py`  
**Range:** 0.0–1.0 (float, rounded to 4 decimal places)  
**Input:** `total_tokens`, `steps_used`, `max_steps`, `difficulty`, `has_error`

### 4.1 Token budgets

Calibrated from observed Claude Sonnet 4.6 runs (the baseline model used during development):

| Difficulty | Token budget |
|---|:---:|
| `easy` | 20,000 |
| `medium` | 50,000 |
| `hard` | 30,000 |

Note: `hard` has a lower budget than `medium` by design — hard tasks have more structured, focused subtasks that should require fewer exploratory token exchanges.

### 4.2 Formula

```python
token_ratio = total_tokens / budget          # e.g. 1.5 means 50% over budget
step_ratio  = steps_used  / max_steps        # e.g. 0.8 means used 80% of allowed steps

token_score = max(0.0, 1.0 - max(0.0, token_ratio - 1.0))
# Linearly penalizes over-budget: ratio=1.0 → 1.0, ratio=2.0 → 0.0, ratio=3.0+ → 0.0
# Under budget is rewarded at 1.0 (no "bonus" for extreme frugality)

step_score = max(0.0, 1.0 - max(0.0, step_ratio - 1.0) * 0.5)
# Softer penalty for step overrun: ratio=1.5 → 0.75, ratio=3.0 → 0.0

raw = token_score * 0.6 + step_score * 0.4

if has_error:
    raw *= 0.5   # 50% penalty for runs that terminated in error
```

### 4.3 Worked examples

| Scenario | tokens | steps | max_steps | diff | has_error | Score |
|---|---:|---:|---:|---|---|:---:|
| Efficient, under budget | 15,000 | 5 | 20 | easy | No | **1.000** |
| At budget, at step limit | 20,000 | 20 | 20 | easy | No | **1.000** |
| 2× over token budget | 40,000 | 20 | 20 | easy | No | **0.400** |
| Claude Haiku feat_005 | 608,861 | 28 | 20 | hard | No | **0.130** |
| Error, under budget | 10,000 | 3 | 20 | easy | Yes | **0.500** |

### 4.4 Known limitations

- **Budgets are model-agnostic.** The calibration was done on Claude Sonnet runs. GPT-4.1-mini and Llama 3.3-70b use fewer tokens by behavior, giving them a structural advantage on efficiency scores independent of correctness.
- **Hard tasks have a smaller budget than medium.** This is intentional but means models that are thorough on hard tasks are penalized more than on medium tasks.

---

## 5. Statistical Validity Scorer

**Source:** `scoring/stat_validity.py`  
**Range:** {0.25, 0.50, 0.75, 1.00} — four binary checks, each worth 0.25  
**Input:** `trace.final_answer` (string), `task.category` (string — currently unused in logic)

### 5.1 Check 1 — Uncertainty reporting

**Passes if** any regex matches (case-insensitive) in `final_answer`:

```python
r"\bp[\s-]*value\b"         # "p-value", "p value"
r"\bconfidence interval\b"
r"\bci\b"                   # standalone "CI"
r"\bstd\b"                  # standalone "std"
r"\bstandard deviation\b"
r"\bstandard error\b"
r"\bp\s*=\s*0\."            # "p = 0.03", "p=0.001"
r"\br\s*=\s*[-+]?\d"        # "r = 0.82"
r"\bapproximately\b"
r"\baround\b"
r"\brange\b"                # "the values range from..."
```

**Note:** `approximately`, `around`, and `range` are weak hedging words — they will satisfy this check even without formal uncertainty quantification.

### 5.2 Check 2 — Appropriate statistical test

**Passes if** any regex matches (case-insensitive):

```python
r"\bpearson\b"
r"\bspearman\b"
r"\bcorrelation\b"
r"\biqr\b"
r"\bz[\s-]*score\b"
r"\bskewness\b"
r"\bkurtosis\b"
r"\bhistogram\b"
r"\bbox[\s-]*plot\b"
r"\blog[\s-]transform"
r"\bnormalization\b"
r"\bnormalise\b"
```

**Known bug:** This list contains only EDA-specific vocabulary. On the 20 non-EDA tasks (modeling, feature engineering, ML engineering, statistical inference), this check almost never passes regardless of how appropriate the model's method is. A model that correctly runs a logistic regression, t-test, or chi-squared test will fail this check because those terms are not in the list.

**Impact:** For non-EDA tasks, the maximum achievable stat_validity score under the current scorer is 0.75. In practice, Check 3 also often fails on non-EDA tasks, so the effective floor for non-EDA tasks is 0.25. **This is the primary driver of the 0.25 finding.** See Section 5.5 for the full impact breakdown.

### 5.3 Check 3 — Correct interpretation

**Passes if** any regex matches (case-insensitive):

```python
r"\bcorrelation does not imply causation\b"
r"\bcontrolling for\b"
r"\badjusting for\b"
r"\bpartial correlation\b"
r"\bconfound"               # "confounder", "confounding"
r"\bsimpson"                # Simpson's Paradox
r"\bspurious"
r"\bstatistically significant\b"
r"\bnot significant\b"
r"\bskew"                   # "skewed", "skewness"
r"\bdistribution\b"
```

**Note:** `distribution` and `skew` are common vocabulary that appears in many responses. On EDA tasks, this check passes frequently. On modeling and ML engineering tasks, it rarely passes unless the model explicitly discusses statistical assumptions.

### 5.4 Check 4 — No p-hacking signals

**Passes if none** of the following match:

```python
r"tried.*different.*method"
r"until.*significant"
r"p.*just.*below.*0\.05"
```

**Note:** These patterns have never fired in 227 runs. This check passes unconditionally in all observed outputs, contributing +0.25 to every score. It is currently **uninformative as a discriminating signal**.

### 5.5 Score computation and effective floor

```python
checks = [uncertainty, appropriate_test, correct_interp, no_p_hacking]
score = round(sum(checks) / 4, 4)
```

Effective score distribution by category:

| Category | Check 2 structural result | Typical observed score |
|---|---|:---:|
| EDA (3 tasks) | Can pass | 0.50–0.75 |
| Feature Engineering (5 tasks) | **Structurally fails** | **0.25** |
| Modeling (5 tasks) | **Structurally fails** | **0.25** |
| Statistical Inference (5 tasks) | **Structurally fails** | **0.25** |
| ML Engineering (5 tasks) | **Structurally fails** | **0.25** |

The 0.25 floor on non-EDA tasks reflects: Check 4 always passes (+0.25), Check 2 always fails (−), Check 1 and Check 3 rarely pass on non-EDA outputs (−). Most non-EDA outputs score exactly 0.25.

### 5.6 What a 1.0 output requires

For an EDA task, the output must contain all of:
- Any uncertainty signal from Check 1 list (easiest: "approximately", "range")
- Any method signal from Check 2 list ("correlation", "skewness", "histogram")
- Any interpretation signal from Check 3 list ("distribution", "statistically significant")
- No p-hacking phrases from Check 4 list (satisfied by default)

For a non-EDA task, achieving 1.0 is currently impossible (Check 2 cannot pass). Maximum achievable score = 0.75.

---

## 6. Composite RDAB Score

**Source:** `scoring/composite.py`  
**Range:** 0.0–1.0 (float, rounded to 4 decimal places)

```python
RDAB_Score = (
    correctness   × w_correctness
  + code_quality  × w_code_quality
  + efficiency    × w_efficiency
  + stat_validity × w_stat_validity
)
```

Weights are defined per-task in the YAML under the `scoring:` block. Weights always sum to 1.00.

---

## 7. Per-Task Weight Profiles

Weights reflect how much each dimension matters for the task type:

| Category | w_correctness | w_code_quality | w_efficiency | w_stat_validity |
|---|:---:|:---:|:---:|:---:|
| EDA | 0.50 | 0.20 | 0.15 | 0.15 |
| Feature Engineering | 0.45 | 0.20 | 0.15 | 0.20 |
| Modeling | 0.40 | 0.15 | 0.15 | 0.30 |
| Statistical Inference | 0.40 | 0.15 | 0.15 | 0.30 |
| ML Engineering | 0.45 | 0.20 | 0.15 | 0.20 |

These are representative values. Individual tasks may deviate slightly (e.g., `eda_003` with Simpson's Paradox has `stat_validity_weight: 0.25`). The exact weights for each task are in the YAML.

---

## 8. Summary of Scoring Limitations

| ID | Dimension | Description | Status |
|---|---|---|---|
| L1 | Stat Validity | Check 2 is EDA-only; non-EDA tasks cannot pass it | Known, documented, deferred |
| L2 | Stat Validity | Check 1 accepts weak hedging words, not formal uncertainty | Known, acceptable |
| L3 | Stat Validity | Check 3 is vocabulary-driven, not semantically sensitive | Known, acceptable |
| L4 | Stat Validity | Check 4 never fires (uninformative) | Known, documented |
| L5 | Correctness | Substring matching — verbose outputs can pass by inclusion | Known, partially mitigated by task design |
| L6 | Correctness | No contradiction detection | Known, fundamental limitation of string scoring |
| L7 | Code Quality | Evaluates code form, not code correctness | Known, by design |
| L8 | Code Quality | Multi-snippet averaging may mask late-run quality issues | Known |
| L9 | Efficiency | Token budgets calibrated on Claude Sonnet, not model-agnostic | Known, favors token-efficient models |

---

## 9. Independent Reproducibility Checklist

To independently score any model output:

1. Extract `final_answer` from the JSON trace file.
2. Apply the 10 regex patterns in Section 5.1 (case-insensitive). Check 1 passes if any match.
3. Apply the 12 regex patterns in Section 5.2. Check 2 passes if any match.
4. Apply the 11 regex patterns in Section 5.3. Check 3 passes if any match.
5. Apply the 3 regex patterns in Section 5.4. Check 4 passes if none match.
6. `stat_validity = (check1 + check2 + check3 + check4) / 4`
7. Extract all `run_code` tool inputs from the trace. Apply the 5 checks in Section 3.1–3.5.
8. `code_quality = mean(scores_per_snippet)` where each snippet scores `(checks_passed / 5)`
9. Compute `token_ratio = total_tokens / budget[difficulty]` using Section 4.1 budgets.
10. Compute `efficiency` using the formula in Section 4.2.
11. Compare `final_answer` against task YAML `ground_truth` using the rules in Section 2.
12. Compute `RDAB_Score = correctness × w_c + code_quality × w_q + efficiency × w_e + stat_validity × w_s` using the task's YAML weights.

Any reviewer who follows these steps and gets a different score than the leaderboard should open an issue with the task ID, model, and discrepancy.

---

## 10. Changelog

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-04-01 | Initial spec covering all 4 dimensions; reflects all 227 v0.1.0 runs |
| 1.1 | 2026-04-17 | Added L9 (efficiency calibration bias), Section 5.5 table, Section 9 checklist |
