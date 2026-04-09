"""Clinical trial dataset — comparing drug vs placebo on blood pressure reduction."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 300, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Randomized trial: drug (1) vs placebo (0)
    treatment = rng.integers(0, 2, n_rows)

    age = rng.integers(30, 75, n_rows)
    baseline_bp = rng.normal(148, 15, n_rows).clip(110, 200)  # systolic mmHg
    bmi = rng.normal(28, 5, n_rows).clip(18, 45)
    smoker = rng.choice([0, 1], n_rows, p=[0.75, 0.25])
    comorbidities = rng.integers(0, 4, n_rows)

    # True drug effect: -12 mmHg reduction in systolic BP
    true_effect = -12.0
    bp_reduction = (
        true_effect * treatment
        + 0.05 * baseline_bp           # regression to mean
        - 0.1 * age
        + 2.0 * smoker
        + rng.normal(0, 8, n_rows)     # within-patient noise
    )

    follow_up_bp = (baseline_bp + bp_reduction).clip(90, 200)

    return pd.DataFrame({
        "patient_id": np.arange(1, n_rows + 1),
        "treatment": treatment,          # 1=drug, 0=placebo
        "age": age,
        "baseline_bp": np.round(baseline_bp, 1),
        "bmi": np.round(bmi, 1),
        "smoker": smoker,
        "comorbidities": comorbidities,
        "follow_up_bp": np.round(follow_up_bp, 1),
        "bp_reduction": np.round(bp_reduction, 1),
    })
