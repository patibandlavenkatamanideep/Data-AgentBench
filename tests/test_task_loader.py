"""Tests for task schema loading and validation."""

import pytest
from pathlib import Path
from pydantic import ValidationError

from realdataagentbench.core.task import TaskSchema
from realdataagentbench.core.registry import TaskRegistry

TASKS_DIR = Path(__file__).parent.parent / "tasks"


class TestTaskLoading:
    def test_eda_001_loads(self):
        task = TaskSchema.from_yaml(TASKS_DIR / "eda/eda_001_income_distribution.yaml")
        assert task.task_id == "eda_001"
        assert task.difficulty == "easy"
        assert task.category == "eda"

    def test_eda_002_loads(self):
        task = TaskSchema.from_yaml(TASKS_DIR / "eda/eda_002_patient_records.yaml")
        assert task.task_id == "eda_002"
        assert task.difficulty == "medium"

    def test_eda_003_loads(self):
        task = TaskSchema.from_yaml(TASKS_DIR / "eda/eda_003_confounding_detection.yaml")
        assert task.task_id == "eda_003"
        assert task.difficulty == "hard"

    def test_scoring_weights_sum_to_one(self):
        for yaml_file in TASKS_DIR.rglob("*.yaml"):
            task = TaskSchema.from_yaml(yaml_file)
            total = (
                task.scoring.correctness_weight
                + task.scoring.code_quality_weight
                + task.scoring.efficiency_weight
                + task.scoring.stat_validity_weight
            )
            assert abs(total - 1.0) < 1e-6, f"{task.task_id} weights sum to {total}"

    def test_evaluation_fields(self):
        task = TaskSchema.from_yaml(TASKS_DIR / "eda/eda_001_income_distribution.yaml")
        assert task.evaluation.max_steps > 0
        assert task.evaluation.timeout_seconds > 0
        assert len(task.evaluation.allowed_tools) > 0

    def test_dataset_fields(self):
        task = TaskSchema.from_yaml(TASKS_DIR / "eda/eda_001_income_distribution.yaml")
        assert task.dataset.generator == "income_distribution"
        assert task.dataset.n_rows == 1000
        assert task.dataset.seed == 42
        assert "income" in task.dataset.columns

    def test_ground_truth_present(self):
        for yaml_file in TASKS_DIR.rglob("*.yaml"):
            task = TaskSchema.from_yaml(yaml_file)
            assert task.ground_truth, f"{task.task_id} has empty ground_truth"

    def test_tags_present(self):
        for yaml_file in TASKS_DIR.rglob("*.yaml"):
            task = TaskSchema.from_yaml(yaml_file)
            assert len(task.tags) > 0, f"{task.task_id} has no tags"


class TestValidationRejection:
    def _make_valid(self) -> dict:
        return {
            "task_id": "test_001",
            "title": "Test Task",
            "difficulty": "easy",
            "category": "eda",
            "description": "A test task.",
            "dataset": {
                "generator": "income_distribution",
                "seed": 42,
                "n_rows": 100,
                "schema": {"income": "float"},
            },
            "ground_truth": {"answer": "yes"},
            "scoring": {
                "correctness_weight": 0.50,
                "code_quality_weight": 0.20,
                "efficiency_weight": 0.15,
                "stat_validity_weight": 0.15,
            },
            "evaluation": {
                "max_steps": 5,
                "timeout_seconds": 60,
                "allowed_tools": ["run_code"],
            },
        }

    def test_rejects_invalid_difficulty(self):
        d = self._make_valid()
        d["difficulty"] = "extreme"
        with pytest.raises(ValidationError):
            TaskSchema.model_validate(d)

    def test_rejects_weights_not_summing_to_one(self):
        d = self._make_valid()
        d["scoring"]["correctness_weight"] = 0.99
        with pytest.raises(ValidationError):
            TaskSchema.model_validate(d)

    def test_rejects_zero_n_rows(self):
        d = self._make_valid()
        d["dataset"]["n_rows"] = 0
        with pytest.raises(ValidationError):
            TaskSchema.model_validate(d)

    def test_rejects_zero_max_steps(self):
        d = self._make_valid()
        d["evaluation"]["max_steps"] = 0
        with pytest.raises(ValidationError):
            TaskSchema.model_validate(d)

    def test_rejects_invalid_task_id(self):
        d = self._make_valid()
        d["task_id"] = "invalid id with spaces"
        with pytest.raises(ValidationError):
            TaskSchema.model_validate(d)


class TestRegistry:
    def test_registry_loads_all(self):
        registry = TaskRegistry(TASKS_DIR)
        assert len(registry) == 39

    def test_registry_get(self):
        registry = TaskRegistry(TASKS_DIR)
        task = registry.get("eda_001")
        assert task.task_id == "eda_001"

    def test_registry_get_missing_raises(self):
        registry = TaskRegistry(TASKS_DIR)
        with pytest.raises(KeyError):
            registry.get("nonexistent_task")

    def test_registry_filter_by_difficulty(self):
        registry = TaskRegistry(TASKS_DIR)
        easy = registry.filter(difficulty="easy")
        assert len(easy) >= 1
        assert all(t.difficulty == "easy" for t in easy)

    def test_registry_filter_by_category(self):
        registry = TaskRegistry(TASKS_DIR)
        eda = registry.filter(category="eda")
        assert len(eda) == 7
        feat = registry.filter(category="feature_engineering")
        assert len(feat) == 8

    def test_registry_summary(self):
        registry = TaskRegistry(TASKS_DIR)
        summary = registry.summary()
        assert summary["total"] == 39
        assert summary["by_category"]["eda"] == 7
        assert summary["by_category"]["feature_engineering"] == 8

    def test_contains(self):
        registry = TaskRegistry(TASKS_DIR)
        assert "eda_001" in registry
        assert "fake_task" not in registry
