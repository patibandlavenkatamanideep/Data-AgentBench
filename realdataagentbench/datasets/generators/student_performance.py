"""Student performance dataset — regression task predicting final exam score."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 700, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    study_hours = rng.exponential(3.5, n_rows).clip(0.5, 20)
    attendance_pct = rng.normal(78, 15, n_rows).clip(20, 100)
    prev_score = rng.normal(65, 15, n_rows).clip(20, 100)
    sleep_hours = rng.normal(7, 1.5, n_rows).clip(3, 12)
    tutoring = rng.integers(0, 2, n_rows)  # 0/1
    extracurricular = rng.integers(0, 2, n_rows)
    parental_education = rng.integers(1, 5, n_rows)  # 1=none, 4=grad
    internet_access = rng.integers(0, 2, n_rows)
    num_absences = rng.integers(0, 30, n_rows)

    # Final score is primarily driven by study hours, prev score, attendance
    final_score = (
        0.3 * prev_score
        + 2.5 * study_hours
        + 0.25 * attendance_pct
        - 0.4 * num_absences
        + 3.0 * tutoring
        + 1.5 * parental_education
        + rng.normal(0, 5, n_rows)
    ).clip(0, 100)

    return pd.DataFrame({
        "study_hours": np.round(study_hours, 1),
        "attendance_pct": np.round(attendance_pct, 1),
        "prev_score": np.round(prev_score, 1),
        "sleep_hours": np.round(sleep_hours, 1),
        "tutoring": tutoring,
        "extracurricular": extracurricular,
        "parental_education": parental_education,
        "internet_access": internet_access,
        "num_absences": num_absences,
        "final_score": np.round(final_score, 1),
    })
