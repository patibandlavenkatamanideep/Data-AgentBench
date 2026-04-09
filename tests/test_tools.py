"""Tests for harness tools."""

import pandas as pd
import numpy as np
import pytest

from realdataagentbench.harness.tools import run_code, get_dataframe_info, get_column_stats


@pytest.fixture
def sample_df():
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "income": rng.lognormal(10, 1, 200),
        "age": rng.integers(20, 70, 200),
        "label": rng.choice(["A", "B", "C"], 200),
    })


@pytest.fixture
def df_with_nulls(sample_df):
    df = sample_df.copy()
    df.loc[:20, "income"] = np.nan
    return df


class TestRunCode:
    def test_basic_print(self, sample_df):
        result = run_code("print(df.shape)", sample_df)
        assert result["error"] is None
        assert "(200, 3)" in result["output"]

    def test_numpy_available(self, sample_df):
        result = run_code("print(np.mean(df['income']))", sample_df)
        assert result["error"] is None
        assert result["output"].strip()

    def test_stats_available(self, sample_df):
        result = run_code("print(stats.skew(df['income']))", sample_df)
        assert result["error"] is None

    def test_syntax_error_captured(self, sample_df):
        result = run_code("this is not python", sample_df)
        assert result["error"] is not None

    def test_runtime_error_captured(self, sample_df):
        result = run_code("print(df['nonexistent_col'])", sample_df)
        assert result["error"] is not None

    def test_partial_output_on_error(self, sample_df):
        result = run_code("print('before')\nraise ValueError('boom')", sample_df)
        assert "before" in result["output"]
        assert result["error"] is not None

    def test_multiline_code(self, sample_df):
        code = "mean = df['income'].mean()\nstd = df['income'].std()\nprint(f'{mean:.2f} {std:.2f}')"
        result = run_code(code, sample_df)
        assert result["error"] is None
        assert result["output"].strip()


class TestGetDataframeInfo:
    def test_returns_shape(self, sample_df):
        info = get_dataframe_info(sample_df)
        assert info["shape"] == [200, 3]

    def test_returns_columns(self, sample_df):
        info = get_dataframe_info(sample_df)
        assert set(info["columns"]) == {"income", "age", "label"}

    def test_returns_dtypes(self, sample_df):
        info = get_dataframe_info(sample_df)
        assert "income" in info["dtypes"]

    def test_returns_missing_counts(self, df_with_nulls):
        info = get_dataframe_info(df_with_nulls)
        assert info["missing_counts"]["income"] == 21

    def test_returns_missing_rates(self, df_with_nulls):
        info = get_dataframe_info(df_with_nulls)
        assert info["missing_rates"]["income"] > 0

    def test_returns_head(self, sample_df):
        info = get_dataframe_info(sample_df)
        assert len(info["head"]) == 3


class TestGetColumnStats:
    def test_numeric_stats(self, sample_df):
        stats = get_column_stats("income", sample_df)
        assert "mean" in stats
        assert "std" in stats
        assert "skewness" in stats
        assert "q1" in stats
        assert "q3" in stats

    def test_categorical_stats(self, sample_df):
        stats = get_column_stats("label", sample_df)
        assert "unique" in stats
        assert "top_values" in stats

    def test_missing_column_returns_error(self, sample_df):
        result = get_column_stats("nonexistent", sample_df)
        assert "error" in result

    def test_missing_values_counted(self, df_with_nulls):
        stats = get_column_stats("income", df_with_nulls)
        assert stats["missing"] == 21

    def test_count_excludes_nulls(self, df_with_nulls):
        stats = get_column_stats("income", df_with_nulls)
        assert stats["count"] == 200 - 21
