"""A/B test dataset — conversion rate experiment with treatment/control groups."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 1000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Assign groups: 50/50 split
    group = rng.choice(["control", "treatment"], n_rows, p=[0.5, 0.5])
    is_treatment = (group == "treatment").astype(int)

    # Conversion: control ~8%, treatment ~12% (real lift of ~4pp)
    base_conv = 0.08
    lift = 0.04
    conv_prob = np.where(is_treatment, base_conv + lift, base_conv)
    converted = (rng.uniform(0, 1, n_rows) < conv_prob).astype(int)

    # Revenue per converted user
    revenue = np.where(
        converted,
        rng.lognormal(mean=3.5, sigma=0.8, size=n_rows),
        0.0
    )

    # User characteristics
    age = rng.integers(18, 65, n_rows)
    device = rng.choice(["mobile", "desktop", "tablet"], n_rows, p=[0.55, 0.35, 0.10])
    session_duration_sec = rng.exponential(120, n_rows).clip(5, 1800)
    prior_purchases = rng.integers(0, 10, n_rows)

    return pd.DataFrame({
        "group": group,
        "converted": converted,
        "revenue": np.round(revenue, 2),
        "age": age,
        "device": device,
        "session_duration_sec": np.round(session_duration_sec, 1),
        "prior_purchases": prior_purchases,
    })
