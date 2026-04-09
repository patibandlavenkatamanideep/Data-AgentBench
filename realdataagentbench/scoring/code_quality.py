"""Code quality scorer — evaluates structure and hygiene of agent-generated code."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class CodeQualityResult:
    score: float
    uses_vectorized_ops: bool
    avoids_raw_loops: bool
    uses_descriptive_names: bool
    no_magic_numbers: bool
    has_print_output: bool


class CodeQualityScorer:
    """Score 0.0–1.0 based on code quality signals extracted from agent trace."""

    def score(self, code_snippets: list[str]) -> float:
        if not code_snippets:
            return 0.5  # neutral if no code submitted

        scores = [self._score_snippet(c) for c in code_snippets]
        return round(sum(s.score for s in scores) / len(scores), 4)

    def score_detailed(self, code_snippets: list[str]) -> CodeQualityResult:
        if not code_snippets:
            return CodeQualityResult(0.5, False, True, False, True, False)

        all_code = "\n".join(code_snippets)
        vectorized = self._uses_vectorized(all_code)
        no_loops = self._avoids_raw_loops(all_code)
        descriptive = self._uses_descriptive_names(all_code)
        no_magic = self._no_magic_numbers(all_code)
        has_print = "print(" in all_code

        checks = [vectorized, no_loops, descriptive, no_magic, has_print]
        score = round(sum(checks) / len(checks), 4)

        return CodeQualityResult(
            score=score,
            uses_vectorized_ops=vectorized,
            avoids_raw_loops=no_loops,
            uses_descriptive_names=descriptive,
            no_magic_numbers=no_magic,
            has_print_output=has_print,
        )

    def _score_snippet(self, code: str) -> CodeQualityResult:
        return self.score_detailed([code])

    def _uses_vectorized(self, code: str) -> bool:
        vectorized_patterns = [
            r"df\[", r"\.mean\(\)", r"\.std\(\)", r"\.sum\(\)",
            r"\.corr\(", r"\.groupby\(", r"np\.", r"stats\.",
        ]
        return any(re.search(p, code) for p in vectorized_patterns)

    def _avoids_raw_loops(self, code: str) -> bool:
        loop_patterns = [r"\bfor\s+\w+\s+in\s+range\(", r"\bwhile\s+True"]
        return not any(re.search(p, code) for p in loop_patterns)

    def _uses_descriptive_names(self, code: str) -> bool:
        # Flag single-letter variable names (excluding i, n, df, x)
        single_letter = re.findall(r"\b([a-eg-moq-wyz])\s*=", code)
        return len(single_letter) == 0

    def _no_magic_numbers(self, code: str) -> bool:
        # Magic numbers are bare numeric literals not assigned to a name
        # Exclude 0, 1, 2, 100 (common in data science)
        magic = re.findall(r"(?<![=\w])\b(?!0\b|1\b|2\b|100\b)\d{2,}\b(?!\s*[=\w])", code)
        return len(magic) <= 2  # allow up to 2 (e.g. seed=42, n_rows)
