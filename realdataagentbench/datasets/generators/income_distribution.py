"""Income distribution generator — right-skewed, seed-stable."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 1000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Log-normal income: right-skewed, skewness ~3.8 at seed=42
    log_mean, log_std = 10.8, 0.9
    income = rng.lognormal(mean=log_mean, sigma=log_std, size=n_rows)

    age = rng.integers(22, 65, size=n_rows)
    education_years = rng.integers(10, 22, size=n_rows)

    return pd.DataFrame({
        "income": np.round(income, 2),
        "age": age,
        "education_years": education_years,
    })
