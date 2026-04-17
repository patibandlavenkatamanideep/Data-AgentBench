# Experiment Design — Uncertainty Prompting Uplift

**Status:** Pre-registered design. Not yet executed.  
**Requires approval before running:** yes — see cost estimate in Section 6.  
**Pre-registration committed:** 2026-04-17

---

## 1. Motivation

RDAB's central finding is that models score ~0.25 on statistical validity while
scoring above 0.83 on correctness for the same tasks. The natural follow-up
question is whether this gap is *addressable* by prompting, or whether it is
structural.

Two competing hypotheses:

- **H-uplift:** Models have the capability to produce statistically rigorous
  output but do not do so by default. A targeted prompt instruction is
  sufficient to close a meaningful fraction of the gap.
- **H-mimicry:** Models respond to uncertainty prompts by adding statistical
  vocabulary ("approximately", "confidence interval", "p-value") without
  meaningful change to the reasoning quality. The stat_validity score
  increases because the scorer is lexical — not because the output is more
  statistically sound.

Both hypotheses predict that `stat_validity` scores will rise under
intervention prompts. They are distinguished by qualitative review: H-mimicry
outputs add the right words but the underlying reasoning is unchanged; H-uplift
outputs add substantive content (actual CI values, bootstrap estimates,
appropriate caveats).

A third possibility:

- **H-null:** Prompt interventions do not reliably increase `stat_validity`.
  Either the models cannot adapt on these tasks, or the instruction conflicts
  with other constraints (e.g., conciseness, tool use format).

---

## 2. Hypothesis (precisely stated)

> Appending an explicit uncertainty-reporting instruction to the system prompt
> will increase mean `stat_validity` score across the 5 selected tasks by more
> than 0.15 (on a 0–1 scale) compared to the baseline prompt, for at least 2
> of the 3 tested models, without reducing mean `correctness` score by more
> than 0.05.

This is the threshold for calling the result **positive**. Smaller gains are
informative (see pre-registered outcomes in Section 8) but do not support
the actionability claim.

---

## 3. Independent variable — prompt variants

The independent variable is the system prompt passed to the model. All other
inputs are held constant: same task, same dataset seed, same `max_steps`, same
tool definitions.

The current baseline prompt is in `realdataagentbench/harness/providers.py`,
line 114, constant `SYSTEM_PROMPT`.

### V0 — Baseline (current production prompt)

```
You are an expert data scientist working on a benchmark task.
You have access to a pandas DataFrame called `df` loaded with the task dataset.

The run_code tool executes Python in a sandboxed namespace. The following are
pre-imported and ready to use WITHOUT any import statements:
  - np        (numpy)
  - pd        (pandas) — `df` is already loaded
  - stats     (scipy.stats)
  - sklearn   (scikit-learn, including sklearn.linear_model, sklearn.ensemble,
               sklearn.preprocessing, sklearn.metrics, sklearn.model_selection)

Do NOT write import statements inside run_code — they will raise an error.
Use np, pd, stats, sklearn directly.

Use the provided tools to analyse the data. After completing your analysis,
write a clear, structured final answer that directly addresses all sub-questions
in the task description. Be precise — include exact numeric values where computed.
```

### V1 — Uncertainty instruction (append to V0)

The following paragraph is appended to the end of V0, replacing no existing text:

```
When reporting any numerical result in your final answer, you MUST also
report its associated uncertainty. Specifically:
  - For classification metrics (accuracy, AUC, F1): report a 95% confidence
    interval or note the test set size and standard error.
  - For regression metrics (RMSE, R²): report the variance across
    cross-validation folds if CV was used, or note single-split uncertainty.
  - For feature importances or coefficients: note whether rankings are likely
    stable or whether the top features are close in magnitude.
  - For any statistical test result: report the p-value, the effect size, and
    the sample size that supports the conclusion.
If you cannot compute a formal uncertainty estimate for a result, explicitly
state that the estimate is from a single train/test split and interpret
accordingly.
```

**Rationale:** Targets Check 1 (uncertainty) and Check 3 (interpretation)
directly with actionable instructions. Does not change the persona. Minimal
token overhead (~110 input tokens).

### V2 — Statistician persona (replace opening + append)

V0's first sentence ("You are an expert data scientist...") is replaced,
and a closing instruction is appended:

```
You are a statistician conducting a rigorous analysis of a data science
pipeline. Your primary responsibility is not just to produce correct numerical
answers but to ensure the analysis is statistically sound: appropriately
uncertain, not over-claiming, aware of violated assumptions, and careful to
avoid confusing correlation with causation.

You have access to a pandas DataFrame called `df` loaded with the task dataset.

[lines 3–13 of V0 unchanged]

Use the provided tools to analyse the data. After completing your analysis,
write a clear, structured final answer that:
  - Directly addresses all sub-questions with exact numeric values
  - Distinguishes statistical significance from practical significance
  - Reports uncertainty bounds (CI, SE, or cross-validation variance) on all
    key metrics
  - Flags any assumptions the analysis depends on
  - Avoids causal language unless the design supports a causal claim
```

**Rationale:** Changes the role identity ("statistician" vs "data scientist"),
which prior prompting research suggests can shift output style more than
explicit instructions alone. Tests whether persona-framing produces real
reasoning change vs. vocabulary-only change.

---

## 4. Dependent variables

Three dependent variables are measured for each run:

| Variable | Source | What it tests |
|---|---|---|
| `stat_validity` score | `StatValidityScorer` on `final_answer` | Primary outcome — does the prompt change the machine score? |
| `correctness` score | `CorrectnessScorer` on `final_answer` | Guard rail — does gained stat validity come at the cost of accuracy? |
| `total_tokens` | `trace.total_input_tokens + total_output_tokens` | Cost signal — does uncertainty language inflate token usage? |

**Why all three:** A result where `stat_validity` rises but `correctness` falls
is a finding in itself — it would suggest the interventions cause models to
hedge at the expense of answering the question. A result where token count
rises sharply would indicate the intervention is expensive to deploy at scale
even if it works.

---

## 5. Task subset

The 5 tasks with the lowest mean `stat_validity` across all full-coverage
models, filtered for tasks where mean `correctness` ≥ 0.60 (to ensure the
task is solvable — low-correctness tasks may be measuring capability failure,
not validity failure):

| Task ID | Category | Difficulty | Mean stat_validity | Mean correctness | Mean input tokens |
|---------|----------|-----------|:-----------------:|:---------------:|:----------------:|
| `feat_002` | feature_engineering | medium | 0.250 | 0.833 | 37,250 |
| `mod_004` | ml_engineering | medium | 0.250 | 0.704 | 19,292 |
| `model_001` | modeling | easy | 0.250 | 0.741 | 18,900 |
| `model_002` | modeling | medium | 0.275 | 0.700 | 50,498 |
| `model_003` | modeling | medium | 0.281 | 0.917 | 28,182 |

All five are non-EDA tasks, which is expected: the stat_validity scorer's
Check 2 (`uses_appropriate_test`) structurally fails on non-EDA tasks due to
the EDA-only pattern list documented in
[docs/methodology/stat_validity.md](stat_validity.md). This means the maximum
achievable score on these tasks under the current scorer is 0.75 (3 of 4 checks
can pass; Check 2 cannot). The experiment will measure movement within that
constrained range.

---

## 6. Model subset and cost estimate

Three models representing the performance tiers in the full-coverage
leaderboard:

| Tier | Model | Provider | Pricing (input/output per 1M tokens) |
|------|-------|----------|--------------------------------------|
| Frontier | `gpt-5` | OpenAI | $15.00 / $60.00 |
| Mid-tier | `gpt-4.1` | OpenAI | $2.00 / $8.00 |
| Small | `llama-3.3-70b-versatile` | Groq | $0.59 / $0.79 |

**Total runs:** 5 tasks × 3 variants × 3 models = **45 runs**

**Cost estimate** (using mean observed tokens per task + ~150 token overhead
for instruction variants, ~500 extra output tokens for uncertainty language):

| Model | Runs | Est. mean tokens (in/out) | Est. cost |
|-------|------|--------------------------|-----------|
| `gpt-5` | 15 | 30,900 in / 4,250 out | **~$10.90** |
| `gpt-4.1` | 15 | 30,900 in / 4,250 out | **~$1.45** |
| `llama-3.3-70b` | 15 | 30,900 in / 4,250 out | **~$0.32** |
| **Total** | **45** | | **~$12.67** |

GPT-5 accounts for 86% of cost. If budget is a constraint, running GPT-5
on only V0 and V1 (not V2) reduces the total to ~$8.33 while still testing
the primary hypothesis on the frontier model. The Llama runs cost under $0.35
regardless.

---

## 7. Analysis plan

### 7a. Primary comparison

For each (model, task) pair, compute the delta:

```
Δstat_validity(V1 vs V0) = stat_validity(V1) − stat_validity(V0)
Δstat_validity(V2 vs V0) = stat_validity(V2) − stat_validity(V0)
```

Aggregate to per-model means and per-task means. The scorer produces values
in {0.25, 0.50, 0.75, 1.00} — with only 45 runs, no significance test is
appropriate. Report descriptive statistics only: mean delta, range, and
proportion of (model, task) pairs where the score improved.

### 7b. Correctness guard

For any (model, variant) combination where mean `Δstat_validity > 0.10`,
report `Δcorrectness`. If `Δcorrectness < −0.05`, flag as a trade-off. A
finding where correctness drops while stat_validity rises is a result, not
a failure — it informs how interventions should be designed for production.

### 7c. Token cost analysis

Report mean `Δtotal_tokens` per variant. If instruction variants cost
significantly more tokens (>30% increase), note the production implication:
uncertainty language may be expensive to elicit at scale.

### 7d. Qualitative review of 3–5 outputs

The critical question the automated score cannot answer: *is the uplift real
reasoning or lexical mimicry?*

For each model, select the output with the largest `Δstat_validity(V1 vs V0)`.
Review manually against three criteria:

1. **Lexical mimicry indicator:** Did the output add uncertainty-sounding
   words (`approximately`, `range`, `around`) without computing actual
   uncertainty estimates? If yes, the gain is likely lexical.
2. **Substantive gain indicator:** Did the output add computed CI values,
   cross-validation variance, or explicit caveats about single-split
   uncertainty? If yes, the gain is likely substantive.
3. **Regression indicator:** Did the output drop or truncate factual content
   in exchange for uncertainty language? If yes, there is a trade-off.

This qualitative step is the experiment's most important output — it determines
whether the stat_validity improvement is credible evidence for H-uplift or
evidence for H-mimicry.

---

## 8. Pre-registered outcomes

These interpretations are committed before running the experiment. If the
results are ambiguous, refer to the definition that most closely matches the
observed data.

### Result A — Clear uplift

*Criterion:* Mean `Δstat_validity` > 0.15 for at least one variant across at
least 2 models, with `Δcorrectness` > −0.05, and qualitative review confirms
at least 50% of improved outputs show substantive (not merely lexical) gains.

*Conclusion:* Uncertainty prompting closes a meaningful fraction of the
stat-validity gap. The gap is not purely structural — models have latent
capability that prompting can surface. Recommended follow-on: test whether
V1-style instructions improve real-world analysis quality in production
settings. The 0.15 threshold is conservative given the scorer's binary checks;
a gain from 0.25 to 0.50 on two of four checks would qualify.

### Result B — Lexical mimicry

*Criterion:* Mean `Δstat_validity` > 0.15 for at least one variant, but
qualitative review shows that ≥70% of improved outputs are lexically triggered
(words added, no substantive reasoning change), OR `Δcorrectness` drops by
more than 0.05.

*Conclusion:* The stat_validity scorer is gameable by surface-level vocabulary
injection. Models learn to say "approximately" and "confidence interval" without
computing them. This is a finding about the scorer's limitations, not about
model capability. Recommended follow-on: design a revised scorer that requires
actual numerical uncertainty estimates, not just vocabulary.

### Result C — Null result

*Criterion:* Mean `Δstat_validity` < 0.10 for all variants and all models.

*Conclusion:* Uncertainty prompting is not effective for these non-EDA task
types under the current scorer. The gap between correctness and stat_validity
is structural — it reflects the scorer's inability to award Check 2 on
non-EDA tasks, not a model capability gap. The intervention to close the gap
is fixing the scorer (adding per-category test patterns), not prompting.
Recommended follow-on: implement the per-category `_check_appropriate_test`
fix documented in the methodology doc, re-score the 227 existing runs, and
re-examine whether a gap persists.

### Result D — Model-tier interaction

*Criterion:* Uplift is observed for the frontier model (GPT-5) but not for the
mid-tier or small models, or vice versa.

*Conclusion:* The ability to follow uncertainty prompts is capability-dependent.
Smaller models may not have sufficient instruction-following fidelity to act on
statistical instructions, even when they can produce correct numerical answers.
This would have practical implications for teams choosing models for statistical
analysis workflows.

---

## 9. Implementation notes (do not run without approval)

The experiment requires modifying `SYSTEM_PROMPT` in `providers.py` to accept
a variant parameter, or creating a thin wrapper that overrides it per-run.
The cleanest implementation is a new CLI flag `--prompt-variant {v0,v1,v2}`
that injects the appropriate system prompt before the agentic loop begins.

Output files should encode the variant in the filename, e.g.:
`feat_002_gpt5_v1_20260417T....json`

The `build_leaderboard.py` aggregator should filter out experiment runs from
the main leaderboard (they use non-standard prompts and should not affect the
benchmark rankings).

**Do not run until:** budget is approved, prompt wording is reviewed, and the
CLI flag implementation is signed off.

---

## 10. Why this experiment matters

The 0.25 stat-validity finding is RDAB's headline result. It appears across all
models and all non-EDA tasks. But before claiming it represents a real model
capability gap, two alternative explanations must be ruled out:

1. **Scorer artifact:** The finding is entirely explained by Check 2's EDA-only
   pattern list. Correcting the scorer would make the gap disappear.
2. **Prompting gap:** The finding is real but addressable — models can do better
   and a short prompt instruction would close most of the gap.

This experiment tests explanation 2. If V1/V2 prompts produce large `stat_validity`
gains without correctness loss, the finding is addressable by prompting. If
prompts produce no gains (null result), the finding is either scorer-structural
(explanation 1, fixable by rewriting the scorer) or a genuine hard capability
limitation.

Either outcome is publishable and useful to practitioners.
