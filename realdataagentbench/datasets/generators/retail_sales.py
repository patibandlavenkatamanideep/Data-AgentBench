"""Retail sales generator — datetime features + weekend effect."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 730, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # ~2 years of daily sales starting 2023-01-01
    start = pd.Timestamp("2023-01-01")
    dates = pd.date_range(start, periods=n_rows, freq="D")

    day_of_week = dates.dayofweek.to_numpy()  # 0=Mon, 6=Sun
    is_weekend = (day_of_week >= 5).astype(int)
    month = dates.month.to_numpy()
    quarter = dates.quarter.to_numpy()

    # Weekend sales are 30% higher; Q4 bump; monthly seasonality
    base = 5000
    daily_sales = (
        base
        + is_weekend * 1500
        + (quarter == 4).astype(int) * 800
        + np.sin(2 * np.pi * month / 12) * 400
        + rng.normal(0, 300, n_rows)
    ).clip(1000, 15000)

    store_id = rng.integers(1, 6, n_rows)
    promo_active = rng.binomial(1, 0.2, n_rows)

    return pd.DataFrame({
        "transaction_date": dates.strftime("%Y-%m-%d"),
        "store_id": store_id,
        "daily_sales": np.round(daily_sales, 2),
        "promo_active": promo_active,
    })
