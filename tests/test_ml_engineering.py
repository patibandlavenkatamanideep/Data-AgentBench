"""Tests for ML engineering task generators and task loading."""

from __future__ import annotations

import numpy as np
import pytest

from realdataagentbench.datasets.generators.leakage_dataset import generate as gen_leakage
from realdataagentbench.datasets.generators.cv_comparison import generate as gen_cv
from realdataagentbench.datasets.generators.calibration_dataset import generate as gen_calibration
from realdataagentbench.datasets.generators.ensemble_dataset import generate as gen_ensemble
from realdataagentbench.datasets.generators.nested_cv_dataset import generate as gen_nested_cv


# ── Leakage dataset ──────────────────────────────────────────────────────────

class TestLeakageGenerator:
    def test_shape(self):
        df = gen_leakage(n_rows=600, seed=42)
        assert df.shape == (600, 8)

    def test_columns(self):
        df = gen_leakage(seed=42)
        expected = {"age", "income", "credit_score", "debt_ratio",
                    "employment_years", "num_accounts", "approval_code", "approved"}
        assert set(df.columns) == expected

    def test_binary_target(self):
        df = gen_leakage(seed=42)
        assert set(df["approved"].unique()).issubset({0, 1})

    def test_leaking_feature_correlated(self):
        df = gen_leakage(seed=42)
        corr = df["approval_code"].corr(df["approved"])
        assert abs(corr) > 0.95, f"approval_code should be nearly perfectly correlated, got {corr:.3f}"

    def test_reproducible(self):
        df1 = gen_leakage(seed=42)
        df2 = gen_leakage(seed=42)
        assert df1.equals(df2)


# ── CV comparison dataset ────────────────────────────────────────────────────

class TestCVComparisonGenerator:
    def test_shape(self):
        df = gen_cv(n_rows=500, seed=42)
        assert df.shape == (500, 6)

    def test_columns(self):
        df = gen_cv(seed=42)
        assert "target" in df.columns
        assert len([c for c in df.columns if c.startswith("feature_")]) == 5

    def test_binary_target(self):
        df = gen_cv(seed=42)
        assert set(df["target"].unique()).issubset({0, 1})

    def test_class_balance(self):
        df = gen_cv(seed=42)
        ratio = df["target"].mean()
        assert 0.3 < ratio < 0.7, f"Should be roughly balanced, got {ratio:.2f}"

    def test_reproducible(self):
        df1 = gen_cv(seed=42)
        df2 = gen_cv(seed=42)
        assert df1.equals(df2)


# ── Calibration dataset ──────────────────────────────────────────────────────

class TestCalibrationGenerator:
    def test_shape(self):
        df = gen_calibration(n_rows=800, seed=42)
        assert df.shape == (800, 8)

    def test_columns(self):
        df = gen_calibration(seed=42)
        assert "heart_disease" in df.columns
        assert "smoking" in df.columns
        assert "bmi" in df.columns

    def test_binary_target(self):
        df = gen_calibration(seed=42)
        assert set(df["heart_disease"].unique()).issubset({0, 1})

    def test_bmi_range(self):
        df = gen_calibration(seed=42)
        assert df["bmi"].between(16, 50).all()

    def test_reproducible(self):
        df1 = gen_calibration(seed=42)
        df2 = gen_calibration(seed=42)
        assert df1.equals(df2)


# ── Ensemble dataset ─────────────────────────────────────────────────────────

class TestEnsembleGenerator:
    def test_shape(self):
        df = gen_ensemble(n_rows=700, seed=42)
        assert df.shape == (700, 9)

    def test_columns(self):
        df = gen_ensemble(seed=42)
        feature_cols = [c for c in df.columns if c.startswith("feature_")]
        assert len(feature_cols) == 8
        assert "target" in df.columns

    def test_three_classes(self):
        df = gen_ensemble(seed=42)
        assert set(df["target"].unique()) == {0, 1, 2}

    def test_class_balance(self):
        df = gen_ensemble(seed=42)
        counts = df["target"].value_counts(normalize=True)
        assert all(counts > 0.15), "Each class should have > 15% of samples"

    def test_reproducible(self):
        df1 = gen_ensemble(seed=42)
        df2 = gen_ensemble(seed=42)
        assert df1.equals(df2)


# ── Nested CV dataset ────────────────────────────────────────────────────────

class TestNestedCVGenerator:
    def test_shape(self):
        df = gen_nested_cv(n_rows=400, seed=42)
        assert df.shape == (400, 11)

    def test_columns(self):
        df = gen_nested_cv(seed=42)
        assert "target" in df.columns
        noise_cols = [c for c in df.columns if c.startswith("noise_")]
        assert len(noise_cols) == 6

    def test_target_is_continuous(self):
        df = gen_nested_cv(seed=42)
        assert df["target"].nunique() > 100

    def test_informative_features_exist(self):
        df = gen_nested_cv(seed=42)
        for feat in ["x1", "x2", "x3", "x4"]:
            assert feat in df.columns

    def test_reproducible(self):
        df1 = gen_nested_cv(seed=42)
        df2 = gen_nested_cv(seed=42)
        assert df1.equals(df2)


# ── Task loading ─────────────────────────────────────────────────────────────

class TestMLEngineeringTasks:
    @pytest.fixture
    def registry(self):
        from pathlib import Path
        from realdataagentbench.core.registry import TaskRegistry
        tasks_dir = Path(__file__).parent.parent / "tasks"
        return TaskRegistry(tasks_dir)

    def test_all_mod_tasks_load(self, registry):
        for tid in ["mod_001", "mod_002", "mod_003", "mod_004", "mod_005"]:
            task = registry.get(tid)
            assert task.task_id == tid

    def test_total_task_count(self, registry):
        assert len(registry) == 29

    def test_mod_001_category(self, registry):
        task = registry.get("mod_001")
        assert task.category == "ml_engineering"

    def test_mod_001_dry_run(self, registry):
        from realdataagentbench.datasets import get_generator
        task = registry.get("mod_001")
        gen = get_generator(task.dataset.generator)
        df = gen(n_rows=task.dataset.n_rows, seed=task.dataset.seed)
        assert set(df.columns) == set(task.dataset.columns)

    def test_scoring_weights_sum_to_one(self, registry):
        for tid in ["mod_001", "mod_002", "mod_003", "mod_004", "mod_005"]:
            task = registry.get(tid)
            total = (task.scoring.correctness_weight + task.scoring.code_quality_weight
                     + task.scoring.efficiency_weight + task.scoring.stat_validity_weight)
            assert abs(total - 1.0) < 1e-9, f"{tid} weights sum to {total}"
