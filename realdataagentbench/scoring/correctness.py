"""Correctness scorer — checks final answer against ground truth."""

from __future__ import annotations

import re
from typing import Any


class CorrectnessScorer:
    """Score 0.0–1.0 based on how many ground truth values appear in the answer."""

    def score(self, answer: str, ground_truth: dict[str, Any]) -> float:
        if not answer.strip():
            return 0.0

        answer_lower = answer.lower()
        checks: list[bool] = []

        for key, value in ground_truth.items():
            # Skip alias lists themselves — they're used by the primary key check
            if key.endswith("_aliases"):
                continue
            # Skip numeric tolerance/approx fields — handled separately
            if key.endswith("_tolerance") or key.endswith("_approx"):
                continue

            result = self._check_value(key, value, ground_truth, answer_lower)
            if result is not None:
                checks.append(result)

        if not checks:
            return 0.0
        return round(sum(checks) / len(checks), 4)

    def _check_value(
        self,
        key: str,
        value: Any,
        ground_truth: dict,
        answer_lower: str,
    ) -> bool | None:
        if isinstance(value, bool):
            # Check direction-change type keys
            aliases_key = f"{key}_aliases"
            aliases = ground_truth.get(aliases_key, [])
            if value:
                return any(a.lower() in answer_lower for a in aliases)
            return None

        if isinstance(value, str):
            aliases_key = f"{key}_aliases"
            aliases = ground_truth.get(aliases_key, [])
            candidates = [value.lower()] + [a.lower() for a in aliases]
            return any(c in answer_lower for c in candidates)

        if isinstance(value, list):
            # All items in list must appear (e.g. columns_with_missing)
            if not value:
                return None
            if isinstance(value[0], str):
                return all(item.lower() in answer_lower for item in value)
            return None

        if isinstance(value, (int, float)):
            approx_key = f"{key}_approx"
            tolerance_key = f"{key}_tolerance"
            if approx_key in ground_truth:
                # This field IS the approx — check nearby
                approx = float(ground_truth[approx_key])
                tolerance = float(ground_truth.get(tolerance_key, approx * 0.15))
                return self._numeric_in_answer(answer_lower, approx, tolerance)
            return None  # raw numeric keys without _approx — skip

        return None

    def _numeric_in_answer(self, answer_lower: str, target: float, tolerance: float) -> bool:
        """Find any float in answer within tolerance of target."""
        pattern = r"[-+]?\d+\.?\d*"
        for match in re.finditer(pattern, answer_lower):
            try:
                val = float(match.group())
                if abs(val - target) <= tolerance:
                    return True
            except ValueError:
                continue
        return False
