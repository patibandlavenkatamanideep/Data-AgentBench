"""Statistical validity scorer — checks correct use of statistical methods."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class StatValidityResult:
    score: float
    reports_uncertainty: bool
    uses_appropriate_test: bool
    interprets_correctly: bool
    avoids_p_hacking_signals: bool


class StatValidityScorer:
    """Score 0.0–1.0 based on statistical rigour signals in the final answer."""

    UNCERTAINTY_PATTERNS = [
        r"\bp[\s-]*value\b", r"\bconfidence interval\b", r"\bci\b",
        r"\bstd\b", r"\bstandard deviation\b", r"\bstandard error\b",
        r"\bp\s*=\s*0\.", r"\br\s*=\s*[-+]?\d",
        r"\bapproximately\b", r"\baround\b", r"\brange\b",
    ]
    CORRECT_INTERP_PATTERNS = [
        r"\bcorrelation does not imply causation\b",
        r"\bcontrolling for\b", r"\badjusting for\b",
        r"\bpartial correlation\b",
        r"\bconfound", r"\bsimpson", r"\bspurious",
        r"\bstatistically significant\b", r"\bnot significant\b",
        r"\bskew", r"\bdistribution\b",
    ]
    P_HACKING_SIGNALS = [
        r"tried.*different.*method",
        r"until.*significant",
        r"p.*just.*below.*0\.05",
    ]

    def score(self, answer: str, category: str = "eda") -> float:
        return self.score_detailed(answer, category).score

    def score_detailed(self, answer: str, category: str = "eda") -> StatValidityResult:
        answer_lower = answer.lower()

        uncertainty = any(
            re.search(p, answer_lower) for p in self.UNCERTAINTY_PATTERNS
        )
        appropriate_test = self._check_appropriate_test(answer_lower, category)
        correct_interp = any(
            re.search(p, answer_lower) for p in self.CORRECT_INTERP_PATTERNS
        )
        no_p_hacking = not any(
            re.search(p, answer_lower) for p in self.P_HACKING_SIGNALS
        )

        checks = [uncertainty, appropriate_test, correct_interp, no_p_hacking]
        score = round(sum(checks) / len(checks), 4)

        return StatValidityResult(
            score=score,
            reports_uncertainty=uncertainty,
            uses_appropriate_test=appropriate_test,
            interprets_correctly=correct_interp,
            avoids_p_hacking_signals=no_p_hacking,
        )

    def _check_appropriate_test(self, answer_lower: str, category: str) -> bool:
        eda_methods = [
            r"\bpearson\b", r"\bspearman\b", r"\bcorrelation\b",
            r"\biqr\b", r"\bz[\s-]*score\b", r"\bskewness\b",
            r"\bkurtosis\b", r"\bhistogram\b", r"\bbox[\s-]*plot\b",
            r"\blog[\s-]transform", r"\bnormalization\b", r"\bnormalise\b",
        ]
        return any(re.search(p, answer_lower) for p in eda_methods)
