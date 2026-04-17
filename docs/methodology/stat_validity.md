# Statistical Validity Scorer — Methodology

This document describes exactly how RDAB scores the `stat_validity` dimension.
It is written for a technical reviewer who wants to understand whether the
finding — "models score ~0.25 on statistical validity while scoring 0.83+ on
correctness on the same tasks" — is meaningful or an artifact of a weak scorer.

The short answer: the scorer is lexical and has a known systematic bias against
non-EDA tasks. The finding is real, but the absolute numbers are conservative
estimates. A human reviewer would score most model outputs *higher*, not lower,
than the machine does. The gap would shrink but not disappear.

---

## 1. What the scorer checks

The scorer is implemented in
`realdataagentbench/scoring/stat_validity.py`. It runs four binary checks on
the agent's `final_answer` string. The score is the fraction of checks that
pass: `score = passing_checks / 4`, yielding 0.00, 0.25, 0.50, 0.75, or 1.00.

### Check 1 — Uncertainty reporting (`reports_uncertainty`)

**Passes if** any of the following regexes match (case-insensitive) in the
final answer:

```python
r"\bp[\s-]*value\b"        # "p-value", "p value"
r"\bconfidence interval\b"  # exact phrase
r"\bci\b"                   # standalone "CI"
r"\bstd\b"                  # standalone "std"
r"\bstandard deviation\b"
r"\bstandard error\b"
r"\bp\s*=\s*0\."            # "p = 0.03", "p=0.001"
r"\br\s*=\s*[-+]?\d"        # "r = 0.82", "r = -0.4"
r"\bapproximately\b"
r"\baround\b"
r"\brange\b"
```

**What this actually catches:** Formal statistical language (`p-value`,
`confidence interval`) *and* weak hedging words (`approximately`, `around`,
`range`). An output that says "the values range from 0.3 to 0.7" will pass this
check even though it reports no formal uncertainty. Conversely, an output that
correctly reports `AUC = 0.84` with no surrounding uncertainty language will
fail, even if the estimate is practically useful.

### Check 2 — Appropriate test (`uses_appropriate_test`)

**Passes if** any of the following regexes match (case-insensitive):

```python
r"\bpearson\b"
r"\bspearman\b"
r"\bcorrelation\b"
r"\biqr\b"
r"\bz[\s-]*score\b"        # "z-score", "z score"
r"\bskewness\b"
r"\bkurtosis\b"
r"\bhistogram\b"
r"\bbox[\s-]*plot\b"        # "box-plot", "boxplot"
r"\blog[\s-]transform"      # "log-transform", "log transform"
r"\bnormalization\b"
r"\bnormalise\b"
```

**Known limitation — systematic bias against non-EDA tasks:** This list
contains only EDA-specific methods. The `_check_appropriate_test` method
accepts a `category` parameter but does not use it — the same regex list is
applied to every task regardless of whether the task is EDA, modeling,
feature engineering, or statistical inference. A model that correctly runs a
logistic regression, a t-test, or a chi-squared test will fail this check
because none of those terms appear in the list. See Section 5 for the full
impact analysis.

### Check 3 — Correct interpretation (`interprets_correctly`)

**Passes if** any of the following regexes match (case-insensitive):

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

**What this actually catches:** A mix of causal-reasoning vocabulary
(`correlation does not imply causation`, `confound`, `spurious`) and generic
statistical vocabulary (`statistically significant`, `distribution`, `skew`).
An output that says "the result is statistically significant" passes even
without reporting *what test produced it* or *at what threshold*. An output
that correctly interprets a coefficient ranking without using any of these
phrases will fail.

### Check 4 — No p-hacking signals (`avoids_p_hacking_signals`)

**Passes if none** of the following regexes match:

```python
r"tried.*different.*method"
r"until.*significant"
r"p.*just.*below.*0\.05"
```

**What this actually catches:** Almost nothing. These patterns are so narrow
that they almost never fire on model outputs. In 227 runs, zero outputs
triggered this check. It passes by default on every output, making it
uninformative as a discriminating signal — it contributes 0.25 to every
score unconditionally.

---

## 2. Score computation

```python
checks = [uncertainty, appropriate_test, correct_interp, no_p_hacking]
score = round(sum(checks) / len(checks), 4)
```

All four checks have equal weight. There is no per-task or per-category
weighting inside the stat-validity scorer itself. The per-task weight of
`stat_validity` in the final RDAB score is set in each task's YAML
(`stat_validity_weight`, typically 0.15–0.30).

---

## 3. Worked example — `model_001` (Logistic Regression for Diabetes Prediction)

`model_001` is used because:
- It is a `modeling`-category task (not EDA), so it exposes the Check 2 bias
- All 9 models that ran it score exactly `stat_validity = 0.25`
- Three representative outputs are available: Claude Opus, GPT-5, GPT-4.1-mini

The task asks the agent to: split data 80/20, standardize features, train
logistic regression, report Accuracy and ROC-AUC, identify top 3 features by
coefficient magnitude, and state whether glucose is the top predictor.

### 3a. Machine scoring — three outputs, all score 0.25

#### Claude Opus output (excerpt)

```
Test Performance
  Accuracy:  0.7438 (74.38%)
  ROC-AUC:   0.8412 (84.12%)

Top 3 Most Important Features (by absolute coefficient magnitude)
  1. glucose          1.1675
  2. diabetes_pedigree 0.6542
  3. age              0.5176

Yes. Glucose is the most predictive feature with the largest absolute
coefficient (1.1675), nearly twice as large as diabetes_pedigree (0.6542).
This aligns with medical knowledge that blood glucose level is the strongest
indicator of diabetes.
```

| Check | Result | Why |
|---|---|---|
| Uncertainty | **FAIL** | No p-value, CI, std, SE, or hedging words in output |
| Appropriate test | **FAIL** | Logistic regression is not in the EDA-only pattern list |
| Correct interp | **FAIL** | No "statistically significant", "distribution", or causal language |
| No p-hacking | **PASS** | No hacking signals detected |
| **Score** | **0.25** | 1 of 4 checks pass |

#### GPT-5 output (excerpt)

```
Test performance:
  Accuracy: 0.7438
  ROC-AUC:  0.8412

Top 3 most important features by absolute coefficient magnitude:
  glucose:             1.167548
  diabetes_pedigree:   0.654239
  age:                 0.517580

Is glucose the most predictive feature?
Yes. Glucose has the largest absolute coefficient.
```

| Check | Result | Why |
|---|---|---|
| Uncertainty | **FAIL** | Same as Opus — point estimates only |
| Appropriate test | **FAIL** | Same EDA-only list miss |
| Correct interp | **FAIL** | No triggering phrases |
| No p-hacking | **PASS** | |
| **Score** | **0.25** | 1 of 4 checks pass |

#### GPT-4.1-mini output (excerpt, the overall #1 model on RDAB)

```
Accuracy is 0.7438
ROC-AUC score is 0.8412
Top 3 most important features by absolute coefficient magnitude:
  glucose, diabetes_pedigree, age
Glucose is the most predictive feature, as it has the highest absolute
coefficient magnitude.
```

| Check | Result | Why |
|---|---|---|
| Uncertainty | **FAIL** | Same |
| Appropriate test | **FAIL** | Same |
| Correct interp | **FAIL** | Same |
| No p-hacking | **PASS** | |
| **Score** | **0.25** | 1 of 4 checks pass |

**The uniformity across all three outputs is itself the finding.** The scorer
is not distinguishing between a weak output and a strong one — it is giving
0.25 to every modeling output because two of the three failing checks are
structurally impossible to pass on a modeling task with this scorer.

### 3b. Manual re-score of Claude Opus

The peer-reviewer question: *if a human statistician re-scored the Opus output
manually, would the score change?*

**Check 1 — Uncertainty reporting:**
The Opus output reports Accuracy = 0.7438 and ROC-AUC = 0.8412 as point
estimates with no confidence intervals, no bootstrap variance, and no note
that the estimates are split-dependent. A statistician would want: a 95% CI
on AUC (trivial to compute via DeLong's method), a note on test set size
(160 samples — small enough for the CI to be wide), and acknowledgment that
the coefficient ranking may shift across different random splits.

*Human verdict: FAIL. The machine and the human agree here.*

**Check 2 — Appropriate test:**
Logistic regression is the correct method for binary classification with
continuous predictors. StandardScaler before logistic regression is correct
(prevents regularization from penalizing high-variance features
disproportionately). The 80/20 split with random_state=42 is appropriate for
reproducibility. max_iter=1000 is a reasonable convergence setting.

*Human verdict: PASS. The machine gives FAIL due to the EDA-only pattern
list — this is a scorer bug, not a model failure.*

**Check 3 — Correct interpretation:**
The output correctly identifies glucose as the top feature and provides
domain context ("aligns with medical knowledge"). However, it does not note
that (a) the coefficient magnitudes are on standardized features, meaning
they represent standard-deviation-scaled importance; (b) the ranking could be
unstable across splits given the gap between ranks 2 and 3 is small (0.654
vs 0.518); or (c) a high AUC of 0.84 does not imply the model is calibrated
(no Brier score or calibration curve).

*Human verdict: PARTIAL PASS (~0.5). The interpretation is correct but
incomplete. The machine gives FAIL because no triggering phrase appears.*

**Check 4 — No p-hacking:**
No evidence of data-dredging.

*Human verdict: PASS. Agree with machine.*

| Check | Machine | Human |
|---|---|---|
| Uncertainty | 0 | 0 |
| Appropriate test | 0 | **1** |
| Correct interp | 0 | **0.5** |
| No p-hacking | 1 | 1 |
| **Score** | **0.25** | **~0.625** |

**The machine underestimates by ~0.38.** The gap comes almost entirely from
the `appropriate_test` bug (Check 2), with a smaller contribution from the
binary treatment of correct interpretation (Check 3 treats partial credit as
zero). The direction is consistent: for non-EDA tasks, machine scores are
conservative relative to human judgment.

### 3c. What a 1.0 output on model_001 would look like

An output that scores 1.0 must pass all four checks. Given the current
patterns, it would need to include:

```
Logistic Regression was trained on the diabetes dataset with an 80/20
train/test split (random_state=42) and StandardScaler normalization.

Test performance on the held-out set (n=160):
  Accuracy:  0.744 (95% CI: 0.671–0.817, estimated via bootstrap)
  ROC-AUC:   0.841 (95% CI: 0.779–0.903, DeLong method)

The standard error on the AUC estimate is approximately 0.032, suggesting
the performance range is consistent with a moderately strong classifier.

Feature importance by absolute coefficient (standardized features):
  glucose:              1.168  (distribution of this feature shows right-skew,
                                 correlation with outcome is strongest)
  diabetes_pedigree:    0.654
  age:                  0.518

Glucose is the most predictive feature. The gap between glucose and
diabetes_pedigree (1.168 vs 0.654) is large enough that this ranking is
likely stable across bootstrap resamples. We are not adjusting for potential
confounders here — this is a predictive model, not a causal one, so we
treat the correlation without implying causation.
```

This output passes all four checks:
- `r"\bapproximately\b"`, `r"\brange\b"`, `r"\bstandard error\b"` → Check 1 ✓
- `r"\bcorrelation\b"`, `r"\bnormalization\b"` → Check 2 ✓
- `r"\bcorrelation does not imply causation\b"`, `r"\bdistribution\b"` → Check 3 ✓
- No p-hacking signals → Check 4 ✓

Note that a real statistician would rate this output higher than the Opus
output — it earns 1.0 because it uses the right vocabulary, not solely because
it demonstrates deeper reasoning. That is a limitation of lexical scoring.

---

## 4. Known limitations

**L1 — Check 2 is EDA-only regardless of task category.** The
`_check_appropriate_test` method accepts a `category` argument but ignores it.
All tasks — including modeling, statistical inference, and ML engineering —
are evaluated against the same EDA vocabulary list. For the 20 non-EDA tasks
in the benchmark, Check 2 almost never passes. This creates a structural
ceiling: non-EDA outputs can score at most 0.75, and in practice score 0.25
because Check 3 also usually fails (see L3).

This is not a calibration problem; it is a code bug. The fix would require
expanding `_check_appropriate_test` with per-category pattern lists (e.g.,
`t-test`, `chi-squared`, `logistic`, `cross-validation` for modeling tasks).
This fix has not been applied because **changing the scorer invalidates all
existing runs**. The existing 227 runs would need to be re-scored, changing
the leaderboard numbers. This decision is deferred.

**L2 — Uncertainty check rewards hedging words, not formal uncertainty.**
`approximately`, `around`, and `range` pass Check 1. A model that says
"the accuracy is around 0.74" passes the same check as one that reports a
bootstrapped 95% CI. The check detects the *presence* of uncertainty language,
not its statistical correctness.

**L3 — Check 3 is vocabulary-driven, not semantically sensitive.** An output
that correctly interprets a result using different words (e.g., "we cannot
conclude that A causes B from this observational data") will fail because the
exact phrases are not in the pattern list. An output that incorrectly writes
"this finding is statistically significant" (with no supporting test) will
pass.

**L4 — Check 4 is uninformative.** The p-hacking patterns have never fired
in 227 runs. This check contributes +0.25 to every output unconditionally,
compressing the effective score range to [0.25, 1.0] rather than [0.0, 1.0].
The practical effect is that 0.25 is the floor, not a signal of anything
in particular.

**L5 — Category conflation in Check 3.** The correct-interpretation patterns
mix causal-reasoning signals (`confound`, `spurious`, `correlation does not
imply causation`) with generic vocabulary (`distribution`, `skew`). A task
about Simpson's Paradox (EDA) and a task about logistic regression (modeling)
are scored against the same pattern list. The patterns are informative for EDA
and statistical inference tasks; they are nearly irrelevant for modeling and
ML engineering tasks.

---

## 5. Impact summary on the leaderboard finding

The key RDAB finding — "models score ~0.25 on stat_validity while scoring 0.83+
on correctness" — is real, but its interpretation should be precise:

| What the scorer measures | What it misses |
|---|---|
| Whether the output contains uncertainty language | Whether the uncertainty is correctly quantified |
| Whether EDA-appropriate methods are named | Whether non-EDA methods are appropriate (always fails) |
| Whether causal-reasoning phrases appear | Whether the causal reasoning is actually correct |
| Whether narrow p-hacking phrases appear | All other forms of selective reporting |

The 0.25 scores observed across non-EDA tasks reflect **two** things: (a) models
genuinely do not add uncertainty quantification to their outputs, and (b) the
scorer structurally cannot award Check 2 on non-EDA tasks. A corrected scorer
with per-category test patterns would likely raise most 0.25 scores to 0.50,
narrowing the correctness–validity gap from ~0.58 to ~0.33. That gap would
still be large and still represent a real finding.

The honest claim, given the scorer's limitations, is:

> On non-EDA tasks, models almost never add uncertainty quantification
> (Check 1 fails) and almost never use causal-reasoning language (Check 3
> fails). The `appropriate_test` check (Check 2) is not informative for
> non-EDA tasks due to the EDA-only pattern list. The p-hacking check
> (Check 4) is not informative in any task because it never fires.
> The 0.25 stat-validity scores on modeling tasks are driven primarily by
> the absence of uncertainty language in model outputs — which is real —
> combined with structural scorer limitations that prevent Check 2 from
> passing on non-EDA tasks.
