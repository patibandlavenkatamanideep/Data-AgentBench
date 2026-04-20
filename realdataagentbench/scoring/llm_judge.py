"""LLM-as-judge scorer for statistical validity.

Uses Claude (haiku by default) to evaluate the four stat-validity criteria
with a structured rubric, returning the same StatValidityResult shape as the
lexical scorer so they can be compared directly.

Intended use:
  1. Calibration: run on a sample of agent answers to measure how well the
     cheap lexical scorer tracks the LLM judge (see scripts/calibrate_stat_validity.py).
  2. Gold standard: optionally replace the lexical scorer on important runs.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

try:
    import anthropic as _anthropic
except ImportError:
    _anthropic = None  # type: ignore[assignment]

from .stat_validity import StatValidityResult


_SYSTEM_PROMPT = """You are a statistical review expert evaluating LLM agent answers to data science tasks. \
You apply a strict rubric and return JSON only — no prose, no explanation."""

_RUBRIC_TEMPLATE = """\
Task category: {category}

Task description:
{task_description}

Agent answer:
{answer}

Score the answer on exactly four criteria (each: 1 = yes, 0 = no):

1. reports_uncertainty — Does the answer quantify uncertainty?
   YES if: p-values, confidence intervals, standard errors, or credible intervals are reported.
   NO if: only point estimates (e.g. "accuracy is 0.87") with no uncertainty measure.

2. uses_appropriate_method — Does the answer use a method suited to this task category?
   EDA → correlation, distribution checks, outlier detection (IQR, z-score)
   statistical_inference → hypothesis tests (t-test, z-test, chi-squared, ANOVA, Fisher, etc.)
   modeling → train/test split, cross-validation, AUC/F1/precision/recall
   feature_engineering → encoding, scaling, imputation, feature selection
   ml_engineering → nested CV, leakage detection, calibration, ensembling, pipeline
   YES if the answer demonstrates using such a method.
   NO if the answer uses wrong/unrelated methods or no analytical method at all.

3. interprets_correctly — Does the answer interpret results without logical errors?
   YES if: avoids causal claims from correlational analysis, explains significance correctly,
           notes relevant caveats, or acknowledges data limitations.
   NO if: makes unjustified causal claims, misinterprets p-values as "the probability H0 is true",
          or draws conclusions the analysis doesn't support.

4. avoids_p_hacking — No signs of cherry-picking or post-hoc method selection?
   YES if: the analysis uses one pre-specified approach and reports results transparently.
   NO if: mentions trying multiple methods until one was significant, or shows other signs
          of data dredging.

Return ONLY this JSON object (no markdown, no extra text):
{{"reports_uncertainty": <0 or 1>, "uses_appropriate_method": <0 or 1>, "interprets_correctly": <0 or 1>, "avoids_p_hacking": <0 or 1>}}
"""


@dataclass
class LLMJudgeResult:
    stat_validity: StatValidityResult
    raw_response: str
    model: str
    input_tokens: int
    output_tokens: int


class LLMJudgeScorer:
    """Score stat-validity using an LLM judge with a structured rubric.

    Args:
        model: Anthropic model to use. Defaults to haiku (cheap + fast).
        api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
    """

    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        api_key: str | None = None,
    ):
        self.model = model
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    def score(
        self,
        answer: str,
        category: str,
        task_description: str = "",
    ) -> LLMJudgeResult:
        """Call the LLM judge and return a StatValidityResult."""
        if _anthropic is None:
            raise ImportError("pip install anthropic to use LLMJudgeScorer")

        client = _anthropic.Anthropic(api_key=self._api_key)
        prompt = _RUBRIC_TEMPLATE.format(
            category=category,
            task_description=task_description or "(not provided)",
            answer=answer,
        )

        message = client.messages.create(
            model=self.model,
            max_tokens=256,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text.strip()
        usage = message.usage

        # Parse JSON response
        try:
            # Strip any accidental markdown fences
            clean = re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()
            parsed = json.loads(clean)
        except json.JSONDecodeError:
            # Fallback: extract 0/1 values via regex
            parsed = {
                "reports_uncertainty": int(bool(re.search(r'"reports_uncertainty"\s*:\s*1', raw))),
                "uses_appropriate_method": int(bool(re.search(r'"uses_appropriate_method"\s*:\s*1', raw))),
                "interprets_correctly": int(bool(re.search(r'"interprets_correctly"\s*:\s*1', raw))),
                "avoids_p_hacking": int(bool(re.search(r'"avoids_p_hacking"\s*:\s*1', raw))),
            }

        ru = bool(parsed.get("reports_uncertainty", 0))
        at = bool(parsed.get("uses_appropriate_method", 0))
        ci = bool(parsed.get("interprets_correctly", 0))
        ph = bool(parsed.get("avoids_p_hacking", 0))
        score = round(sum([ru, at, ci, ph]) / 4, 4)

        sv = StatValidityResult(
            score=score,
            reports_uncertainty=ru,
            uses_appropriate_test=at,
            interprets_correctly=ci,
            avoids_p_hacking_signals=ph,
        )

        return LLMJudgeResult(
            stat_validity=sv,
            raw_response=raw,
            model=self.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
        )
