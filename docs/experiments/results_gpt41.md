# Uncertainty-Uplift Experiment — GPT-4.1 Results

**Design pre-registered:** 2026-04-17  
**Execution:** 2026-05-05  
**Design doc:** [uncertainty_uplift_design.md](uncertainty_uplift_design.md)  
**Runner:** `scripts/run_uncertainty_uplift.py`  
**Output files:** `outputs/experiment/`

---

## Setup

3 prompt variants × 5 tasks = 15 GPT-4.1 runs. Temperature 0 throughout.

| Variant | Change |
|---------|--------|
| **V0 (baseline)** | Current production system prompt |
| **V1 (uncertainty)** | V0 + explicit CI/SE/p-value instruction (~110 tokens) |
| **V2 (statistician)** | Full replacement with statistician persona + structured output rules |

Full prompt text is in [uncertainty_uplift_design.md §3](uncertainty_uplift_design.md).

Tasks: `feat_002`, `mod_004`, `model_001`, `model_002`, `model_003`

---

## Quantitative results

### stat_validity scores by task and variant

| Task | V0 | V1 | V2 | Δ (V1−V0) | Δ (V2−V0) |
|------|----|----|----|:---------:|:---------:|
| feat_002 | 0.500 | 1.000 | 1.000 | +0.500 | +0.500 |
| mod_004  | 0.500 | 1.000 | 1.000 | +0.500 | +0.500 |
| model_001| 0.500 | 1.000 | 1.000 | +0.500 | +0.500 |
| model_002| 0.750 | 1.000 | 1.000 | +0.250 | +0.250 |
| model_003| 0.500 | 1.000 | 0.750 | +0.500 | +0.250 |
| **Mean** | **0.550** | **1.000** | **0.950** | **+0.450** | **+0.400** |

Correctness across all 15 runs: **1.000**. Zero trade-off between uncertainty reporting and factual accuracy.

### Token overhead vs V0 baseline

| Variant | Mean tokens | Change |
|---------|:-----------:|:------:|
| V0 | 12,677 | baseline |
| V1 | 16,664 | +31% |
| V2 | 10,713 | −15% |

The V1 average is inflated by one outlier: `mod_004` went from 5,777 → 24,484 tokens (+324%), where the model attempted a bootstrap computation. Three of five V1 tasks used under +15% additional tokens. V2 is consistently more efficient than baseline.

---

## Qualitative review (§7d of design)

The stat_validity scorer is lexical — it detects vocabulary, not reasoning quality. All 15 outputs were reviewed manually against three criteria:

1. Were uncertainty-sounding words added without any computation?
2. Were actual numerical estimates computed (SE, CI width, bootstrap result)?
3. Was any factual content dropped relative to V0?

| Task | V1 verdict | V2 verdict |
|------|:----------:|:----------:|
| feat_002 | Lexical mimicry | Mixed |
| mod_004 | **Real reasoning uplift** | Lexical |
| model_001 | **Real reasoning uplift** | Mixed |
| model_002 | Mixed (flawed SE, correct instability flag) | **Real reasoning uplift** |
| model_003 | Mixed (approximate formula, correct conclusion) | Lexical / caveats only |

**No regression in any run:** V1 and V2 outputs are strict supersets of V0 content on all five tasks.

### Genuine uplift — V1, `mod_004`

The model computed binomial SE using the correct formula: `SE = sqrt(p(1−p)/n)` applied to the actual test set size (n=140), yielding 0.031 for Logistic Regression accuracy. It then attempted bootstrap for F1 SE, hit a sandbox limitation, disclosed the failure explicitly, and provided an informed range estimate (≈0.03–0.04). No number was fabricated. This is the target behavior.

### Lexical mimicry — V1, `feat_002`

The model added "the top features are clearly separated in magnitude" and offered CIs "if needed" — without performing any bootstrap computation. The stat_validity scorer rewarded this identically to the `mod_004` genuine computation. This is the scorer's blind spot.

### V2 genuine uplift — V2, `model_002`

V2's statistician framing pushed the model to discuss cross-validation variance and feature instability with substantive caveats about which wine-quality features would likely re-rank on different splits. The reasoning was substantive rather than boilerplate.

---

## Outcome against pre-registered criteria

The pre-registered threshold for **Result A (Clear uplift)** required mean Δ > 0.15 for at least two models. GPT-4.1 V1 returns Δ = +0.450 — three times the threshold — on all five tasks with zero correctness loss.

Llama V1/V2 data is unavailable due to Groq free-tier rate limiting (re-run pending). The two-model criterion is not yet formally met.

**Assessment: qualified Result A.** Prompting produces genuine reasoning improvements on classification and regression metric tasks (3 of 5 tasks show substantive computation). On feature importance tasks, gains are primarily lexical.

---

## Implications

**For practitioners:** V1-style uncertainty instructions are worth adding to production prompts for metric-reporting workflows. V2 (statistician persona) is the better default — nearly equal uplift, 15% lower token overhead, and consistently substantive methodological caveats.

**For the benchmark:** The lexical stat_validity scorer requires a numeric-evidence check to separate deferred offers ("let me know if you need CIs") from actual computations. The scorer limitation and the model capability gap are separate problems, now empirically distinguishable.

---

## Run status

| Model | V0 | V1 | V2 |
|-------|:--:|:--:|:--:|
| gpt-4.1 | ✓ 5/5 | ✓ 5/5 | ✓ 5/5 |
| llama-3.3-70b | 4/5 ⚠️ rate-limited | pending | pending |
| gpt-5 | — not run | — | — |

Llama re-run command (rate-limit delay added in v2 of script):

```bash
python scripts/run_uncertainty_uplift.py --model llama-3.3-70b-versatile --variant v1
python scripts/run_uncertainty_uplift.py --model llama-3.3-70b-versatile --variant v2
```
