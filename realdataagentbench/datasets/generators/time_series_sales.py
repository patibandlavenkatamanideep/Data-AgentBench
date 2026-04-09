"""Time series sales dataset — trend + seasonality decomposition task."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 730, seed: int = 42) -> pd.DataFrame:
    """Generate 2 years of daily sales with trend, weekly, and annual seasonality."""
    rng = np.random.default_rng(seed)

    dates = pd.date_range("2022-01-01", periods=n_rows, freq="D")
    t = np.arange(n_rows)

    # Linear trend
    trend = 1000 + 0.5 * t

    # Weekly seasonality: peak Fri/Sat, trough Mon
    dow = dates.dayofweek.to_numpy()
    weekly = np.array([0.85, 0.9, 1.0, 1.05, 1.15, 1.30, 1.10])[dow] * 100

    # Annual seasonality: peak Dec, trough Feb
    annual = 150 * np.sin(2 * np.pi * (t - 60) / 365)

    # Promotions on random days (~5%)
    promo_days = rng.choice([0, 1], n_rows, p=[0.95, 0.05])
    promo_effect = promo_days * rng.uniform(100, 300, n_rows)

    # Noise
    noise = rng.normal(0, 40, n_rows)

    sales = (trend + weekly + annual + promo_effect + noise).clip(100)

    return pd.DataFrame({
        "date": dates,
        "sales": np.round(sales, 1),
        "day_of_week": dow,
        "is_promotion": promo_days,
        "month": dates.month.to_numpy(),
        "year": dates.year.to_numpy(),
    })
