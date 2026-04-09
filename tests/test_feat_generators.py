"""Tests for feature engineering dataset generators and task loading."""

import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from realdataagentbench.datasets.generators.house_prices import generate as gen_house
from realdataagentbench.datasets.generators.employee_attrition import generate as gen_attrition
from realdataagentbench.datasets.generators.retail_sales import generate as gen_retail
from realdataagentbench.datasets.generators.credit_risk import generate as gen_credit
from realdataagentbench.datasets.generators.fraud_detection import generate as gen_fraud
from realdataagentbench.core.registry import TaskRegistry
from realdataagentbench.datasets import get_generator

TASKS_DIR = Path(__file__).parent.parent / "tasks"


class TestHousePricesGenerator:
    def test_shape(self):
        df = gen_house(n_rows=300, seed=0)
        assert df.shape == (300, 5)

    def test_columns(self):
        df = gen_house()
        assert set(df.columns) == {"total_sqft", "num_rooms", "house_age", "garage", "price"}

    def test_positive_price(self):
        df = gen_house()
        assert (df["price"] > 0).all()

    def test_engineered_features_improve_r2(self):
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import r2_score
        df = gen_house(seed=42)
        feats = ["total_sqft", "num_rooms", "house_age", "garage"]
        y = df["price"]
        r2_orig = r2_score(y, LinearRegression().fit(df[feats], y).predict(df[feats]))
        df["sqft_per_room"] = df["total_sqft"] / df["num_rooms"]
        df["age_sqft"] = df["house_age"] * df["total_sqft"]
        feats2 = feats + ["sqft_per_room", "age_sqft"]
        r2_eng = r2_score(y, LinearRegression().fit(df[feats2], y).predict(df[feats2]))
        assert r2_eng > r2_orig, f"Engineered R²={r2_eng:.3f} should beat original R²={r2_orig:.3f}"

    def test_seed_reproducible(self):
        df1 = gen_house(seed=7)
        df2 = gen_house(seed=7)
        pd.testing.assert_frame_equal(df1, df2)

    def test_no_nulls(self):
        assert gen_house().isnull().sum().sum() == 0


class TestEmployeeAttritionGenerator:
    def test_shape(self):
        df = gen_attrition(n_rows=400, seed=0)
        assert df.shape == (400, 10)

    def test_categorical_columns(self):
        df = gen_attrition()
        cats = df.select_dtypes("object").columns.tolist()
        assert "department" in cats
        assert "gender" in cats
        assert "overtime" in cats

    def test_binary_target(self):
        df = gen_attrition()
        assert set(df["attrition"].unique()).issubset({0, 1})

    def test_high_cardinality_job_role(self):
        df = gen_attrition()
        assert df["job_role"].nunique() > 5

    def test_low_cardinality_gender(self):
        df = gen_attrition()
        assert df["gender"].nunique() <= 5

    def test_seed_reproducible(self):
        df1 = gen_attrition(seed=3)
        df2 = gen_attrition(seed=3)
        pd.testing.assert_frame_equal(df1, df2)


class TestRetailSalesGenerator:
    def test_shape(self):
        df = gen_retail(n_rows=365, seed=0)
        assert df.shape == (365, 4)

    def test_date_column_parseable(self):
        df = gen_retail()
        parsed = pd.to_datetime(df["transaction_date"])
        assert np.issubdtype(parsed.dtype, np.datetime64)

    def test_weekend_higher_sales(self):
        df = gen_retail(seed=42)
        df["dt"] = pd.to_datetime(df["transaction_date"])
        df["is_weekend"] = (df["dt"].dt.dayofweek >= 5).astype(int)
        assert df[df.is_weekend == 1]["daily_sales"].mean() > \
               df[df.is_weekend == 0]["daily_sales"].mean()

    def test_positive_sales(self):
        df = gen_retail()
        assert (df["daily_sales"] > 0).all()

    def test_seed_reproducible(self):
        df1 = gen_retail(seed=10)
        df2 = gen_retail(seed=10)
        pd.testing.assert_frame_equal(df1, df2)


class TestCreditRiskGenerator:
    def test_shape(self):
        df = gen_credit(n_rows=500, seed=0)
        assert df.shape == (500, 16)

    def test_income_log_highly_correlated(self):
        df = gen_credit(seed=42)
        r = abs(df["income"].corr(df["income_log"]))
        assert r > 0.85, f"income~income_log r={r:.3f} should be >0.85"

    def test_noise_columns_near_zero_variance(self):
        df = gen_credit(seed=42)
        assert df["dummy_noise_1"].std() < 0.01
        assert df["dummy_noise_2"].std() < 0.01

    def test_binary_target(self):
        df = gen_credit()
        assert set(df["default"].unique()).issubset({0, 1})

    def test_seed_reproducible(self):
        df1 = gen_credit(seed=5)
        df2 = gen_credit(seed=5)
        pd.testing.assert_frame_equal(df1, df2)


class TestFraudDetectionGenerator:
    def test_shape(self):
        df = gen_fraud(n_rows=500, seed=0)
        assert df.shape == (500, 8)

    def test_imbalanced_target(self):
        df = gen_fraud(seed=42)
        fraud_rate = df["fraud"].mean()
        assert 0.02 <= fraud_rate <= 0.15, f"Expected ~5% fraud, got {fraud_rate:.3f}"

    def test_transaction_hour_range(self):
        df = gen_fraud()
        assert df["transaction_hour"].between(0, 23).all()

    def test_positive_amounts(self):
        df = gen_fraud()
        assert (df["transaction_amount"] > 0).all()

    def test_three_merchant_categories_min(self):
        df = gen_fraud()
        assert df["merchant_category"].nunique() >= 3

    def test_seed_reproducible(self):
        df1 = gen_fraud(seed=99)
        df2 = gen_fraud(seed=99)
        pd.testing.assert_frame_equal(df1, df2)


class TestFeatTaskLoading:
    def test_all_feat_tasks_load(self):
        registry = TaskRegistry(TASKS_DIR)
        for tid in ["feat_001", "feat_002", "feat_003", "feat_004", "feat_005"]:
            task = registry.get(tid)
            assert task.task_id == tid

    def test_feat_task_difficulties(self):
        registry = TaskRegistry(TASKS_DIR)
        assert registry.get("feat_001").difficulty == "easy"
        assert registry.get("feat_002").difficulty == "medium"
        assert registry.get("feat_003").difficulty == "medium"
        assert registry.get("feat_004").difficulty == "hard"
        assert registry.get("feat_005").difficulty == "hard"

    def test_feat_task_category(self):
        registry = TaskRegistry(TASKS_DIR)
        for tid in ["feat_001", "feat_002", "feat_003", "feat_004", "feat_005"]:
            assert registry.get(tid).category == "feature_engineering"

    def test_registry_total_count(self):
        registry = TaskRegistry(TASKS_DIR)
        assert len(registry) == 18  # 3 EDA + 5 feat + 5 modeling + 5 stat_inference

    def test_filter_by_category(self):
        registry = TaskRegistry(TASKS_DIR)
        feat_tasks = registry.filter(category="feature_engineering")
        assert len(feat_tasks) == 5

    def test_feat_generators_registered(self):
        for name in ["house_prices", "employee_attrition", "retail_sales",
                     "credit_risk", "fraud_detection"]:
            gen = get_generator(name)
            assert callable(gen)

    def test_scoring_weights_sum_to_one(self):
        registry = TaskRegistry(TASKS_DIR)
        for tid in ["feat_001", "feat_002", "feat_003", "feat_004", "feat_005"]:
            task = registry.get(tid)
            total = (task.scoring.correctness_weight + task.scoring.code_quality_weight +
                     task.scoring.efficiency_weight + task.scoring.stat_validity_weight)
            assert abs(total - 1.0) < 1e-6, f"{tid} weights sum to {total}"
