"""Wine quality dataset — regression + classification on physicochemical properties."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 800, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    fixed_acidity = rng.normal(8.3, 1.7, n_rows).clip(4.0, 16.0)
    volatile_acidity = rng.normal(0.53, 0.18, n_rows).clip(0.1, 1.2)
    citric_acid = rng.normal(0.27, 0.19, n_rows).clip(0.0, 1.0)
    residual_sugar = rng.exponential(2.5, n_rows).clip(0.5, 20.0)
    chlorides = rng.normal(0.087, 0.047, n_rows).clip(0.01, 0.6)
    free_sulfur = rng.normal(15.9, 10.5, n_rows).clip(1, 72)
    total_sulfur = rng.normal(46.5, 32.9, n_rows).clip(6, 289)
    density = rng.normal(0.9967, 0.0019, n_rows).clip(0.99, 1.004)
    ph = rng.normal(3.31, 0.15, n_rows).clip(2.9, 4.0)
    sulphates = rng.normal(0.66, 0.17, n_rows).clip(0.3, 2.0)
    alcohol = rng.normal(10.4, 1.07, n_rows).clip(8.0, 14.9)

    # Quality driven by alcohol, volatile_acidity, sulphates
    quality_score = (
        3.0
        + 0.25 * alcohol
        - 1.5 * volatile_acidity
        + 0.8 * sulphates
        - 0.3 * chlorides * 10
        + rng.normal(0, 0.6, n_rows)
    ).clip(3, 9)
    quality = np.round(quality_score).astype(int)
    high_quality = (quality >= 7).astype(int)

    return pd.DataFrame({
        "fixed_acidity": np.round(fixed_acidity, 1),
        "volatile_acidity": np.round(volatile_acidity, 2),
        "citric_acid": np.round(citric_acid, 2),
        "residual_sugar": np.round(residual_sugar, 1),
        "chlorides": np.round(chlorides, 3),
        "free_sulfur_dioxide": np.round(free_sulfur, 1),
        "total_sulfur_dioxide": np.round(total_sulfur, 1),
        "density": np.round(density, 4),
        "ph": np.round(ph, 2),
        "sulphates": np.round(sulphates, 2),
        "alcohol": np.round(alcohol, 1),
        "quality": quality,
        "high_quality": high_quality,
    })
