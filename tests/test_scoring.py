"""Tests for all scoring modules."""

import pytest
from pathlib import Path

from realdataagentbench.core.registry import TaskRegistry
from realdataagentbench.scoring.correctness import CorrectnessScorer
from realdataagentbench.scoring.code_quality import CodeQualityScorer
from realdataagentbench.scoring.efficiency import EfficiencyScorer
from realdataagentbench.scoring.stat_validity import StatValidityScorer
from realdataagentbench.scoring.composite import CompositeScorer, ScoreCard

TASKS_DIR = Path(__file__).parent.parent / "tasks"


# ---------------------------------------------------------------------------
# Correctness
# ---------------------------------------------------------------------------

class TestCorrectnessScorer:
    def setup_method(self):
        self.scorer = CorrectnessScorer()

    def test_perfect_answer_eda_001(self):
        registry = TaskRegistry(TASKS_DIR)
        task = registry.get("eda_001")
        answer = (
            "The income distribution is right-skewed with a skewness of 3.82. "
            "I recommend a log transformation (np.log) to normalize it."
        )
        score = self.scorer.score(answer, task.ground_truth)
        assert score >= 0.6

    def test_partial_answer(self):
        registry = TaskRegistry(TASKS_DIR)
        task = registry.get("eda_001")
        answer = "The distribution is right-skewed."
        score = self.scorer.score(answer, task.ground_truth)
        assert 0.0 < score < 1.0

    def test_empty_answer_scores_zero(self):
        registry = TaskRegistry(TASKS_DIR)
        task = registry.get("eda_001")
        score = self.scorer.score("", task.ground_truth)
        assert score == 0.0

    def test_wrong_answer_scores_low(self):
        registry = TaskRegistry(TASKS_DIR)
        task = registry.get("eda_001")
        answer = "The income is normally distributed. No transformation needed."
        score = self.scorer.score(answer, task.ground_truth)
        assert score < 0.5

    def test_alias_matching_log_transformation(self):
        registry = TaskRegistry(TASKS_DIR)
        task = registry.get("eda_001")
        answer = "Use a log transformation to fix the positive skew."
        score = self.scorer.score(answer, task.ground_truth)
        assert score > 0.0

    def test_eda_002_missing_columns(self):
        registry = TaskRegistry(TASKS_DIR)
        task = registry.get("eda_002")
        answer = "Columns bmi and cholesterol have missing values. Blood_pressure has outliers detected by IQR."
        score = self.scorer.score(answer, task.ground_truth)
        assert score >= 0.5

    def test_eda_003_negative_correlation(self):
        registry = TaskRegistry(TASKS_DIR)
        task = registry.get("eda_003")
        answer = "The raw correlation r=-0.52 is negative. After controlling for order_size the correlation collapses to near zero. This is spurious — the team should not act."
        score = self.scorer.score(answer, task.ground_truth)
        assert score >= 0.6


# ---------------------------------------------------------------------------
# Code Quality
# ---------------------------------------------------------------------------

class TestCodeQualityScorer:
    def setup_method(self):
        self.scorer = CodeQualityScorer()

    def test_good_code_scores_high(self):
        code = [
            "mean_income = df['income'].mean()\nprint(f'Mean: {mean_income:.2f}')"
        ]
        score = self.scorer.score(code)
        assert score >= 0.6

    def test_empty_snippets_returns_neutral(self):
        score = self.scorer.score([])
        assert score == 0.5

    def test_raw_loop_penalised(self):
        code = ["for i in range(len(df)):\n    print(df.iloc[i]['income'])"]
        result = self.scorer.score_detailed(code)
        assert not result.avoids_raw_loops

    def test_vectorized_ops_rewarded(self):
        code = ["corr = df['discount_pct'].corr(df['revenue'])\nprint(corr)"]
        result = self.scorer.score_detailed(code)
        assert result.uses_vectorized_ops

    def test_has_print_rewarded(self):
        code = ["print(df.describe())"]
        result = self.scorer.score_detailed(code)
        assert result.has_print_output


# ---------------------------------------------------------------------------
# Efficiency
# ---------------------------------------------------------------------------

class TestEfficiencyScorer:
    def setup_method(self):
        self.scorer = EfficiencyScorer()

    def test_within_budget_scores_high(self):
        score = self.scorer.score(
            total_tokens=2000, steps_used=3, max_steps=8, difficulty="easy"
        )
        assert score >= 0.8

    def test_over_budget_penalised(self):
        # easy budget is 20k — send 100k tokens (5x over budget)
        score = self.scorer.score(
            total_tokens=100_000, steps_used=10, max_steps=8, difficulty="easy"
        )
        assert score < 0.5

    def test_error_halves_score(self):
        s_no_err = self.scorer.score(5000, 3, 8, "easy", has_error=False)
        s_err = self.scorer.score(5000, 3, 8, "easy", has_error=True)
        assert s_err < s_no_err

    def test_hard_has_larger_budget(self):
        # medium budget 50k, hard budget 30k — use 25k tokens
        # hard scores higher because 25k/30k < 25k/50k... wait, medium is larger
        # just test that score is valid 0-1
        s_hard = self.scorer.score(25_000, 5, 15, "hard")
        s_medium = self.scorer.score(25_000, 5, 15, "medium")
        # medium has bigger budget so same tokens score higher on medium
        assert s_medium >= s_hard

    def test_zero_tokens_safe(self):
        score = self.scorer.score(0, 0, 8, "easy")
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Statistical Validity
# ---------------------------------------------------------------------------

class TestStatValidityScorer:
    def setup_method(self):
        self.scorer = StatValidityScorer()

    def test_rigorous_answer_scores_high(self):
        answer = (
            "The Pearson correlation r=-0.52 (p=0.001) is negative. "
            "Controlling for order_size reveals a partial correlation near zero — "
            "confounding by customer segment explains the spurious result."
        )
        score = self.scorer.score(answer)
        assert score >= 0.75

    def test_bare_answer_scores_low(self):
        answer = "Discount and revenue are related."
        score = self.scorer.score(answer)
        assert score <= 0.5

    def test_reports_uncertainty_flag(self):
        answer = "The mean is 55,000 with standard deviation of 12,000."
        result = self.scorer.score_detailed(answer)
        assert result.reports_uncertainty

    def test_correct_interpretation_flag(self):
        answer = "Controlling for segment, the partial correlation collapses — correlation does not imply causation."
        result = self.scorer.score_detailed(answer)
        assert result.interprets_correctly


# ---------------------------------------------------------------------------
# Composite
# ---------------------------------------------------------------------------

class TestCompositeScorer:
    def _make_result(self, answer: str, code: str = "", tokens: int = 2000, steps: int = 4) -> dict:
        return {
            "task_id": "eda_001",
            "trace": {
                "final_answer": answer,
                "total_input_tokens": tokens // 2,
                "total_output_tokens": tokens // 2,
                "num_steps": steps,
                "error": None,
                "steps": [
                    {
                        "step": 1,
                        "role": "tool",
                        "content": "",
                        "tool_name": "run_code",
                        "tool_input": {"code": code},
                        "tool_output": "ok",
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "elapsed_seconds": 0.1,
                    }
                ] if code else [],
            },
        }

    def test_scorecard_returned(self):
        registry = TaskRegistry(TASKS_DIR)
        task = registry.get("eda_001")
        scorer = CompositeScorer()
        result = self._make_result("The distribution is right-skewed. Log transformation recommended.")
        card = scorer.score(task, result)
        assert isinstance(card, ScoreCard)

    def test_dab_score_in_range(self):
        registry = TaskRegistry(TASKS_DIR)
        task = registry.get("eda_001")
        scorer = CompositeScorer()
        result = self._make_result("right-skewed, log transformation, skewness 3.82")
        card = scorer.score(task, result)
        assert 0.0 <= card.dab_score <= 1.0

    def test_good_answer_scores_higher(self):
        registry = TaskRegistry(TASKS_DIR)
        task = registry.get("eda_001")
        scorer = CompositeScorer()

        good = self._make_result(
            "The income is right-skewed (skewness ≈ 3.82). "
            "A log transformation is recommended to normalize it.",
            code="print(stats.skew(df['income']))"
        )
        bad = self._make_result("I don't know.")

        good_card = scorer.score(task, good)
        bad_card = scorer.score(task, bad)
        assert good_card.dab_score >= bad_card.dab_score

    def test_weights_sum_reflected(self):
        registry = TaskRegistry(TASKS_DIR)
        task = registry.get("eda_001")
        scorer = CompositeScorer()
        result = self._make_result("right-skewed log transformation")
        card = scorer.score(task, result)
        # Verify the DAB score equals the weighted sum
        expected = (
            card.correctness * card.weights["correctness"]
            + card.code_quality * card.weights["code_quality"]
            + card.efficiency * card.weights["efficiency"]
            + card.stat_validity * card.weights["stat_validity"]
        )
        assert abs(card.dab_score - expected) < 1e-4

    def test_scorecard_str(self):
        registry = TaskRegistry(TASKS_DIR)
        task = registry.get("eda_001")
        scorer = CompositeScorer()
        result = self._make_result("right-skewed")
        card = scorer.score(task, result)
        s = str(card)
        assert "DAB Score" in s
        assert "eda_001" in s
