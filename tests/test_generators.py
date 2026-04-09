"""Tests for dataset generators."""

import numpy as np
import pandas as pd
import pytest

from realdataagentbench.datasets.generators.income_distribution import generate as gen_income
from realdataagentbench.datasets.generators.patient_records import generate as gen_patient
from realdataagentbench.datasets.generators.ecommerce_transactions import generate as gen_ecommerce
from realdataagentbench.datasets import get_generator, GENERATORS


class TestIncomeGenerator:
    def test_shape(self):
        df = gen_income(n_rows=500, seed=0)
        assert df.shape == (500, 3)

    def test_columns(self):
        df = gen_income()
        assert set(df.columns) == {"income", "age", "education_years"}

    def test_seed_reproducible(self):
        df1 = gen_income(seed=42)
        df2 = gen_income(seed=42)
        pd.testing.assert_frame_equal(df1, df2)

    def test_different_seeds_differ(self):
        df1 = gen_income(seed=1)
        df2 = gen_income(seed=2)
        assert not df1["income"].equals(df2["income"])

    def test_right_skewed(self):
        from scipy.stats import skew
        df = gen_income(seed=42)
        assert skew(df["income"]) > 1.0, "Income should be right-skewed"

    def test_no_nulls(self):
        df = gen_income()
        assert df.isnull().sum().sum() == 0

    def test_positive_income(self):
        df = gen_income()
        assert (df["income"] > 0).all()


class TestPatientGenerator:
    def test_shape(self):
        df = gen_patient(n_rows=800, seed=42)
        assert df.shape == (800, 7)

    def test_columns(self):
        df = gen_patient()
        assert "bmi" in df.columns
        assert "blood_pressure" in df.columns
        assert "cholesterol" in df.columns

    def test_bmi_missing_rate(self):
        df = gen_patient(seed=42)
        rate = df["bmi"].isnull().mean()
        assert 0.10 <= rate <= 0.20, f"BMI missing rate {rate:.3f} not in [0.10, 0.20]"

    def test_cholesterol_missing_rate(self):
        df = gen_patient(seed=42)
        rate = df["cholesterol"].isnull().mean()
        assert 0.05 <= rate <= 0.12, f"Cholesterol missing rate {rate:.3f} not in [0.05, 0.12]"

    def test_blood_pressure_has_outliers(self):
        df = gen_patient(seed=42)
        q1, q3 = df["blood_pressure"].quantile([0.25, 0.75])
        iqr = q3 - q1
        outliers = df["blood_pressure"] > q3 + 1.5 * iqr
        assert outliers.sum() > 0, "Expected injected outliers in blood_pressure"

    def test_seed_reproducible(self):
        df1 = gen_patient(seed=7)
        df2 = gen_patient(seed=7)
        pd.testing.assert_frame_equal(df1, df2)


class TestEcommerceGenerator:
    def test_shape(self):
        df = gen_ecommerce(n_rows=2000, seed=42)
        assert df.shape == (2000, 5)

    def test_columns(self):
        df = gen_ecommerce()
        assert set(df.columns) == {
            "transaction_id", "customer_segment", "order_size",
            "discount_pct", "revenue"
        }

    def test_three_segments(self):
        df = gen_ecommerce()
        segments = set(df["customer_segment"].unique())
        assert segments == {"enterprise", "smb", "consumer"}

    def test_positive_values(self):
        df = gen_ecommerce()
        assert (df["revenue"] > 0).all()
        assert (df["order_size"] > 0).all()
        assert (df["discount_pct"] >= 0).all()

    def test_raw_correlation_negative(self):
        df = gen_ecommerce(seed=42)
        r = df["discount_pct"].corr(df["revenue"])
        assert r < 0, f"Raw correlation should be negative for Simpson's Paradox setup, got {r:.3f}"

    def test_seed_reproducible(self):
        df1 = gen_ecommerce(seed=99)
        df2 = gen_ecommerce(seed=99)
        pd.testing.assert_frame_equal(df1, df2)


class TestGeneratorRegistry:
    def test_known_generators(self):
        for name in ["income_distribution", "patient_records", "ecommerce_transactions"]:
            gen = get_generator(name)
            assert callable(gen)

    def test_unknown_generator_raises(self):
        with pytest.raises(KeyError):
            get_generator("nonexistent_generator")
