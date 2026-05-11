# Uncertainty-Uplift Experiment — Llama 3.3-70B Results

**Execution attempts:** 2026-05-05 and 2026-05-10  
**Model:** `llama-3.3-70b-versatile` (Groq free tier)  
**Design doc:** [uncertainty_uplift_design.md](uncertainty_uplift_design.md)  
**Runner:** `scripts/run_uncertainty_uplift.py`

---

## Coverage and constraints

Groq free tier limits:
- **30 RPM** (requests per minute) — handled by `--rate-limit-delay 6`
- **100k tokens per day (TPD)** — the binding constraint

`model_002` alone consumed 61,273 tokens on a single V0 run. `model_001` V2 consumed 58,271 tokens (looping behavior). Together they exceed the daily budget. Completed runs:

| Task | V0 | V1 | V2 |
|------|:--:|:--:|:--:|
| feat_002 | ✓ | ✗ TPD | ✓ |
| mod_004 | ✓ | ✓ | ✗ format error |
| model_001 | ✗ malformed | ✗ TPD | ✗ TPD (58k tokens) |
| model_002 | ✗ TPD | ✗ TPD | ✗ TPD |
| model_003 | ✓ | ✗ TPD | ✓ |

**V0 format note:** `model_001` V0 "succeeded" but Llama output a raw `<function/run_code>` tag as its final answer — the agent never actually executed the code. This is a known tool-calling format failure on Groq/Llama.

**V2 mod_004 format error:** Groq returned HTTP 400 ("Failed to call a function") when V2's statistician persona replaced the system prompt. The Groq-specific tool-call suffix appended to V2 was insufficient — Llama's function-calling behavior breaks when the entire system prompt is replaced.

---

## stat_validity scores — successful runs only

| Task | V0 | V1 | V2 | Δ (V1−V0) | Δ (V2−V0) |
|------|----|----|----|:---------:|:---------:|
| feat_002 | 0.500 | — | 0.500 | — | **0.000** |
| mod_004 | 0.500 | 0.500 | — | **0.000** | — |
| model_003 | 0.500 | — | 0.500 | — | **0.000** |
| **Available Δ** | | | | **0.000** (n=1) | **0.000** (n=2) |

**Correctness:** All successful runs returned correct answers (no correctness regression from prompting).

---

## Qualitative analysis

### mod_004 V1 (the one valid V1 run)

The V1 prompt appended explicit instructions to report standard errors, confidence intervals, and test set size alongside every metric. Llama's answer:

> "The results show that the VotingClassifier outperforms all three base classifiers on F1 score. The Random Forest classifier has the highest accuracy among the base classifiers."

The uncertainty instruction was completely ignored. No standard errors, no CIs, no test-set-size qualifiers. The model reported the same bare comparison it would have given under V0. This is not partial compliance — the uncertainty instruction had zero visible effect on the output.

### V2 behavioral shift

V2's statistician persona caused Llama to describe what the code WOULD do rather than executing it:

> "The provided code is designed to perform a series of tasks... However, due to the nature of the task and the constraints of the environment, the code is not executable in this format."

This is the opposite of the desired behavior. V2 broke Llama's agentic execution loop — the model reverted to describing tasks rather than completing them.

---

## Key finding

**Δ(V1−V0) ≈ 0.000 for all available tasks.** GPT-4.1 showed Δ = +0.450 on the same prompt variant. The prompting lever is strongly model-dependent:

- GPT-4.1 follows explicit uncertainty instructions and produces genuine SE/CI computations.
- Llama 3.3-70B ignores uncertainty instructions entirely; the output is indistinguishable from baseline.
- Llama V2 breaks agentic execution and produces worse outputs than V0.

See [results_summary.md](results_summary.md) for the two-model comparison.

---

## Pending runs

To complete the full 5-task Llama comparison (after TPD reset or on paid tier):

```bash
# feat_002 V1, model_003 V1 (each day independently — stay under 100k TPD)
python scripts/run_uncertainty_uplift.py --model llama-3.3-70b-versatile \
  --task feat_002 --task model_003 --variant v1 --rate-limit-delay 6 --skip-completed

# model_001 and model_002 require Groq Dev tier (each task ~58-61k tokens alone)
```
