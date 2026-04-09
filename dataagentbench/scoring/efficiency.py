"""Efficiency scorer — tokens used and steps taken relative to task budget."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EfficiencyResult:
    score: float
    token_ratio: float      # tokens_used / token_budget
    step_ratio: float       # steps_used / max_steps
    completed_without_error: bool


class EfficiencyScorer:
    """Score 0.0–1.0 based on token and step efficiency."""

    # Token budget per difficulty — calibrated from real claude-sonnet-4-6 runs
    TOKEN_BUDGETS = {"easy": 20_000, "medium": 50_000, "hard": 30_000}

    def score(
        self,
        total_tokens: int,
        steps_used: int,
        max_steps: int,
        difficulty: str = "medium",
        has_error: bool = False,
    ) -> float:
        return self.score_detailed(
            total_tokens, steps_used, max_steps, difficulty, has_error
        ).score

    def score_detailed(
        self,
        total_tokens: int,
        steps_used: int,
        max_steps: int,
        difficulty: str = "medium",
        has_error: bool = False,
    ) -> EfficiencyResult:
        budget = self.TOKEN_BUDGETS.get(difficulty, 8_000)
        token_ratio = total_tokens / budget if budget > 0 else 1.0
        step_ratio = steps_used / max_steps if max_steps > 0 else 1.0

        # Score: penalise for going over budget / steps; reward efficiency
        token_score = max(0.0, 1.0 - max(0.0, token_ratio - 1.0))
        step_score = max(0.0, 1.0 - max(0.0, step_ratio - 1.0) * 0.5)

        raw = (token_score * 0.6) + (step_score * 0.4)
        if has_error:
            raw *= 0.5

        return EfficiencyResult(
            score=round(raw, 4),
            token_ratio=round(token_ratio, 4),
            step_ratio=round(step_ratio, 4),
            completed_without_error=not has_error,
        )
