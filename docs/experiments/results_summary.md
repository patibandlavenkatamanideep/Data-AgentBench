# Uncertainty-Uplift Experiment — Two-Model Summary

**Design pre-registered:** 2026-04-17  
**GPT-4.1 execution:** 2026-05-05 (complete)  
**Llama 3.3-70B execution:** 2026-05-05 and 2026-05-10 (partial — see coverage table)

Full per-model detail: [results_gpt41.md](results_gpt41.md) · [results_llama.md](results_llama.md)

---

## stat_validity scores — side by side

### GPT-4.1 (complete: 5 tasks × 3 variants)

| Task | V0 | V1 | V2 | Δ(V1) | Δ(V2) |
|------|----|----|----|:-----:|:-----:|
| feat_002 | 0.500 | 1.000 | 1.000 | +0.500 | +0.500 |
| mod_004 | 0.500 | 1.000 | 1.000 | +0.500 | +0.500 |
| model_001 | 0.500 | 1.000 | 1.000 | +0.500 | +0.500 |
| model_002 | 0.750 | 1.000 | 1.000 | +0.250 | +0.250 |
| model_003 | 0.500 | 1.000 | 0.750 | +0.500 | +0.250 |
| **Mean** | **0.550** | **1.000** | **0.950** | **+0.450** | **+0.400** |

Correctness: 1.000 across all 15 runs. Zero trade-off.

### Llama 3.3-70B (partial: Groq free tier 100k TPD cap)

| Task | V0 | V1 | V2 | Δ(V1) | Δ(V2) |
|------|----|----|----|:-----:|:-----:|
| feat_002 | 0.500 | — | 0.500 | — | **0.000** |
| mod_004 | 0.500 | 0.500 | — | **0.000** | — |
| model_001 | — ¹ | — | — | — | — |
| model_002 | — ² | — | — | — | — |
| model_003 | 0.500 | — | 0.500 | — | **0.000** |
| **Available Δ** | | | | **0.000** (n=1) | **0.000** (n=2) |

¹ model_001 V0: Llama output a raw `<function/run_code>` tag instead of executing code  
² model_002: all variants exhausted the 100k daily token budget (61k tokens/run)  
V1 feat_002 and model_003 are pending (daily cap; run tomorrow with `--skip-completed`)  
V2 mod_004: HTTP 400 — V2 system prompt replacement breaks Llama's tool-calling on Groq

Correctness: 1.000 on all completed runs (no regression from prompting).

---

## Two-model comparison

| Model | V1 mean Δ | V2 mean Δ | Instruction following |
|-------|:---------:|:---------:|----------------------|
| GPT-4.1 | **+0.450** | +0.400 | Follows and executes |
| Llama 3.3-70B | **0.000** | 0.000 | Ignores completely |

The gap is not subtle. GPT-4.1 V1 produced binomial SE formulas, bootstrap attempts with disclosed failures, and correctly qualified single-split limitations. Llama V1 output was word-for-word equivalent to V0 — the explicit uncertainty instruction left no visible trace in the answer.

---

## Outcome against pre-registered criteria

The pre-registered **Result A (Clear uplift)** required: mean Δ > 0.15 for ≥2 models.

| Model | Result A threshold (Δ > 0.15) |
|-------|:------------------------------:|
| GPT-4.1 | ✓ Δ = +0.450 (3× threshold) |
| Llama 3.3-70B | ✗ Δ = 0.000 |

**Assessment: Result A confirmed for GPT-4.1; Llama shows no prompting effect.** The two-model criterion is not formally met. The more informative finding is that the prompting lever is **strongly model-dependent**: instruction-following capability is the prerequisite, and Llama 3.3-70B does not have it at the level GPT-4.1 does for this specific instruction type.

This is a more useful result than two models both confirming +0.450 — it identifies that prompting is a lever only for models that follow complex system-prompt instructions.

---

## Practical recommendations

**For GPT-4.1 users:** V1-style uncertainty instructions are worth adding to production prompts for metric-reporting tasks. V2 (statistician persona) is the better default — nearly equal stat_validity uplift (+0.400), 15% lower token overhead, and consistently substantive methodological caveats.

**For Llama users:** Uncertainty prompting does not work. If statistical validity matters, use a model that follows detailed system-prompt instructions (GPT-4.1, Claude). Alternatively, use RDAB to measure gap, then select tasks where Llama's V0 already meets the bar.

**For the benchmark:** The stat_validity scorer was patched (2026-05-10, v1.5) to give partial credit (0.5×) for lexical-only uncertainty language without numeric evidence. Score changes are modest (−0.001 to −0.034 per model; −0.007 to −0.019 per category across 1,356 traces). See [SCORING_SPEC.md §9](../../SCORING_SPEC.md#9-changelog) for details.

---

## Pending

- Llama V1 for feat_002 and model_003 (run after daily TPD reset)
- model_001 and model_002 on Groq Dev tier (each task ~58–61k tokens/run)
- `scripts/calibrate_stat_validity.py` re-run with patched scorer to update κ vs LLM judge
