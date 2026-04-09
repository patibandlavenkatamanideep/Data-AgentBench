"""Patient records generator — missing values and outliers injected."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 800, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    patient_id = np.arange(1, n_rows + 1)
    age = rng.integers(18, 85, size=n_rows)
    bmi = rng.normal(26.5, 4.5, size=n_rows).round(1)
    cholesterol = rng.normal(200, 35, size=n_rows).round(1)
    glucose = rng.normal(95, 18, size=n_rows).round(1)

    # blood_pressure: inject outliers (~5% extreme values)
    bp = rng.normal(120, 15, size=n_rows)
    outlier_idx = rng.choice(n_rows, size=int(n_rows * 0.05), replace=False)
    bp[outlier_idx] = rng.choice([220, 230, 240, 250, 260], size=len(outlier_idx))
    blood_pressure = np.round(bp, 1)

    diagnosis = rng.choice(
        ["healthy", "hypertension", "diabetes", "obesity"], size=n_rows
    )

    df = pd.DataFrame({
        "patient_id": patient_id,
        "age": age,
        "bmi": bmi,
        "blood_pressure": blood_pressure,
        "cholesterol": cholesterol,
        "glucose": glucose,
        "diagnosis": diagnosis,
    })

    # Inject ~15% missing in bmi
    bmi_missing_idx = rng.choice(n_rows, size=int(n_rows * 0.15), replace=False)
    df.loc[bmi_missing_idx, "bmi"] = np.nan

    # Inject ~8% missing in cholesterol
    chol_missing_idx = rng.choice(n_rows, size=int(n_rows * 0.08), replace=False)
    df.loc[chol_missing_idx, "cholesterol"] = np.nan

    return df
