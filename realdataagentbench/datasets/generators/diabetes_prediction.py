"""Diabetes prediction dataset — binary classification with medical features."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 800, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    age = rng.integers(20, 80, n_rows)
    bmi = rng.normal(28, 6, n_rows).clip(15, 55)
    glucose = rng.normal(110, 30, n_rows).clip(60, 250)
    blood_pressure = rng.normal(72, 12, n_rows).clip(40, 120)
    insulin = rng.normal(80, 50, n_rows).clip(0, 400)
    skin_thickness = rng.normal(20, 8, n_rows).clip(5, 60)
    pregnancies = rng.integers(0, 12, n_rows)
    dpf = rng.uniform(0.05, 2.5, n_rows)  # diabetes pedigree function

    # Logistic model: glucose + bmi + age are primary drivers
    log_odds = (
        -8.0
        + 0.035 * glucose
        + 0.09 * bmi
        + 0.025 * age
        + 0.015 * insulin * 0.01
        + 0.8 * dpf
        + rng.normal(0, 0.5, n_rows)
    )
    prob = 1 / (1 + np.exp(-log_odds))
    diabetes = (rng.uniform(0, 1, n_rows) < prob).astype(int)

    return pd.DataFrame({
        "pregnancies": pregnancies,
        "glucose": np.round(glucose, 1),
        "blood_pressure": np.round(blood_pressure, 1),
        "skin_thickness": np.round(skin_thickness, 1),
        "insulin": np.round(insulin, 1),
        "bmi": np.round(bmi, 2),
        "diabetes_pedigree": np.round(dpf, 3),
        "age": age,
        "diabetes": diabetes,
    })
