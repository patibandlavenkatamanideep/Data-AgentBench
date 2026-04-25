"""Statistical validity scorer — checks correct use of statistical methods.

Four binary checks, all category-aware. Score = checks_passed / 4.

  Check 1 — uncertainty:    Does the answer quantify uncertainty?
  Check 2 — method:         Does the answer name an appropriate method for the task category?
  Check 3 — interpretation: Does the answer show analytical understanding beyond bare numbers?
  Check 4 — no_p_hacking:   Is p-hacking language absent?

Each check is scored 0 or 1; the composite is their mean (0.25 increments).
The minimum achievable score is 0.25: check 4 (absence of a bad signal) almost
always passes; the other three require the agent to produce something substantive.

Category-aware design
---------------------
All four checks use category-specific pattern lists. This prevents an EDA-focused
vocabulary from creating an artificial ceiling on modeling and ML engineering tasks,
and avoids rewarding agents that accidentally use statistical vocabulary irrelevant
to the task category.

Known limitations (see SCORING_SPEC.md §4 for full details)
------------------------------------------------------------
- Lexical: detects vocabulary, not reasoning quality. An agent that writes
  "confidence interval" without computing one still passes check 1.
- `scripts/calibrate_stat_validity.py` measures agreement with an LLM judge
  (Pearson r and Cohen's κ) to quantify this limitation empirically.
"""

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

    # ── Check 1: Uncertainty quantification ──────────────────────────────────
    # Broad vocabulary: statistical inference patterns + ML uncertainty signals.
    # These fire on any answer that acknowledges the limits of its estimates.
    UNCERTAINTY_PATTERNS = [
        r"\bp[\s-]*value\b", r"\bconfidence interval\b", r"\bci\b",
        r"\bstandard deviation\b", r"\bstandard error\b",
        r"\bp\s*=\s*0\.", r"\br\s*=\s*[-+]?\d",
        r"\bapproximately\b", r"\baround\b", r"\brange\b",
        # ML uncertainty vocabulary
        r"\buncertain", r"\bbootstrap\b",
        r"\bprediction interval\b", r"\bvariance\b",
        r"\bstability\b", r"\bstable\b",
        r"\brobust", r"\breliabilit",
        r"\berror bar", r"\bmargin of error\b",
        r"\bstd\b",
    ]

    # ── Check 2: Appropriate method vocabulary (category-specific) ────────────
    # Each category has its own expected vocabulary. Falling through to a default
    # EDA list is intentionally disallowed — an unknown category returns False.
    _METHODS_BY_CATEGORY: dict[str, list[str]] = {
        "eda": [
            r"\bpearson\b", r"\bspearman\b", r"\bcorrelation\b",
            r"\biqr\b", r"\bz[\s-]*score\b", r"\bskewness\b",
            r"\bkurtosis\b", r"\bhistogram\b", r"\bbox[\s-]*plot\b",
            r"\blog[\s-]transform", r"\bnormalization\b", r"\bnormalis",
        ],
        "statistical_inference": [
            r"\bt[\s-]*test\b", r"\bz[\s-]*test\b", r"\bchi[\s-]*squar",
            r"\bmann[\s-]*whitney\b", r"\bwilcoxon\b", r"\banova\b",
            r"\bfisher\b", r"\bhypothesis\b", r"\bnull hypothesis\b",
            r"\btest statistic\b", r"\bdegrees of freedom\b",
            r"\btwo[\s-]*proportion\b", r"\bproportion\b",
        ],
        "modeling": [
            r"\bcross[\s-]*val", r"\btrain[\s-]*test\b",
            r"\broc[\s-]*auc\b", r"\bprecision\b", r"\brecall\b",
            r"\bf1[\s-]*score\b", r"\baccuracy\b", r"\bconfusion matrix\b",
            r"\bbaseline\b", r"\boverfit", r"\bregulariz",
            r"\bfeature importance\b", r"\bcoefficient\b",
            r"\brmse\b", r"\bmae\b", r"\br[\s-]*squared\b", r"\br2\b",
            r"\blearning curve\b", r"\bvalidation\b",
        ],
        "feature_engineering": [
            r"\bone[\s-]*hot\b", r"\blabel[\s-]*encod", r"\bpolynomial\b",
            r"\bstandard[\s-]*scal", r"\bmin[\s-]*max\b", r"\bnormali[sz]",
            r"\bimputation\b", r"\bimpute\b", r"\bmissing value",
            r"\bfeature selection\b", r"\bencoding\b", r"\binteraction term\b",
            r"\blag feature\b", r"\brolling\b", r"\btime[\s-]*series\b",
            r"\bsmote\b", r"\bclass weight\b", r"\bover[\s-]*sampl",
            r"\btarget encod", r"\bordinal encod",
        ],
        "ml_engineering": [
            r"\bcross[\s-]*val", r"\bnested[\s-]*cv\b",
            r"\bdata[\s-]*leakage\b", r"\bleakage\b",
            r"\bcalibrat", r"\bensemble\b", r"\bvoting\b",
            r"\boverfitting\b", r"\bregulariz", r"\bhyperparameter\b",
            r"\bpipeline\b", r"\bstratif", r"\bthreshold\b",
            r"\bbrier\b", r"\bplatt\b", r"\bisotonic\b",
            r"\bbootstrap\b", r"\bfeature.*stabil",
        ],
    }

    # ── Check 3: Analytical interpretation (category-specific) ───────────────
    # These patterns fire when the agent goes beyond reporting numbers to showing
    # understanding of what the results mean and where they can mislead.
    # Each category has signals appropriate for that type of analysis.
    _INTERP_BY_CATEGORY: dict[str, list[str]] = {
        "eda": [
            r"\bcorrelation does not imply causation\b",
            r"\bcontrolling for\b", r"\badjusting for\b",
            r"\bpartial correlation\b",
            r"\bconfound", r"\bsimpson", r"\bspurious",
            r"\bstatistically significant\b", r"\bnot significant\b",
            r"\bskew", r"\bdistribution\b",
            r"\boutlier", r"\banomal",
        ],
        "statistical_inference": [
            r"\bstatistically significant\b", r"\bnot significant\b",
            r"\breject.{0,15}null\b", r"\bfail.{0,8}reject\b",
            r"\beffect size\b", r"\bpractical significance\b",
            r"\btype [i1] error\b", r"\bassumption",
            r"\bconfound", r"\bcontrolling for\b",
            r"\bnormality\b", r"\bpower\b",
            r"\binterpret", r"\bconclude",
        ],
        "modeling": [
            r"\boverfit", r"\bgenerali[sz]",
            r"\bbias.{0,5}variance\b", r"\bvariance.{0,5}bias\b",
            r"\btrain.{0,5}test gap\b",
            r"\bselection bias\b",
            r"\bcaution\b", r"\blimit",
            r"\binterpret\b", r"\bstabilit",
            r"\bclass imbalanc", r"\bthreshold\b",
            r"\bshould not\b", r"\bwith caution\b",
            r"\bcorrelat.{0,10}cause\b",
        ],
        "feature_engineering": [
            r"\bmulticollinear", r"\bvif\b",
            r"\bleakage\b",
            r"\bstabilit", r"\brank.{0,10}stab",
            r"\bordinal relation", r"\bimpos.{0,10}ordinal",
            r"\bcaution\b", r"\blimit",
            r"\bdimensionalit", r"\bsparsit",
            r"\bcorrelat.{0,10}target\b",
            r"\bimportance.{0,10}stab", r"\bfold.{0,10}var",
        ],
        "ml_engineering": [
            r"\bselection bias\b",
            r"\boptimist.{0,10}bias\b",
            r"\bleakage\b",
            r"\bcalibrat", r"\breliabilit",
            r"\bstratif", r"\bclass imbalanc",
            r"\boverfit", r"\buncertain",
            r"\bnested.{0,10}prevent", r"\bpipeline.{0,10}prevent",
            r"\bleak.{0,10}result", r"\btarget.{0,10}leak",
        ],
    }

    # ── Check 4 (inverted): Absence of p-hacking signals ─────────────────────
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
        appropriate_test = self._check_method_vocab(answer_lower, category)
        correct_interp = self._check_interpretation(answer_lower, category)
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

    def _check_method_vocab(self, answer_lower: str, category: str) -> bool:
        """Check 2: Does the answer use vocabulary appropriate to the task category?"""
        patterns = self._METHODS_BY_CATEGORY.get(category)
        if patterns is None:
            return False
        return any(re.search(p, answer_lower) for p in patterns)

    def _check_interpretation(self, answer_lower: str, category: str) -> bool:
        """Check 3: Does the answer show analytical understanding appropriate to the category?"""
        patterns = self._INTERP_BY_CATEGORY.get(category, self._INTERP_BY_CATEGORY["eda"])
        return any(re.search(p, answer_lower) for p in patterns)

    # Keep old name as alias for backwards compatibility
    def _check_appropriate_test(self, answer_lower: str, category: str) -> bool:
        return self._check_method_vocab(answer_lower, category)
