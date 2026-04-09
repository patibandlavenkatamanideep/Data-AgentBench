"""Salary survey dataset — testing pay gap hypotheses across groups."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 600, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    gender = rng.choice(["M", "F"], n_rows, p=[0.55, 0.45])
    department = rng.choice(
        ["Engineering", "Marketing", "Sales", "HR", "Finance"],
        n_rows, p=[0.30, 0.20, 0.25, 0.10, 0.15]
    )
    years_experience = rng.integers(0, 30, n_rows)
    education = rng.choice(
        ["Bachelor", "Master", "PhD", "Associate"],
        n_rows, p=[0.45, 0.30, 0.10, 0.15]
    )
    role_level = rng.choice(
        ["Junior", "Mid", "Senior", "Lead", "Director"],
        n_rows, p=[0.25, 0.30, 0.25, 0.15, 0.05]
    )
    performance_score = rng.normal(3.5, 0.7, n_rows).clip(1, 5)

    # Base salary by department
    dept_base = {
        "Engineering": 90000, "Finance": 80000, "Marketing": 70000,
        "Sales": 65000, "HR": 60000
    }
    level_mult = {"Junior": 0.7, "Mid": 1.0, "Senior": 1.35, "Lead": 1.6, "Director": 2.0}
    edu_bonus = {"PhD": 10000, "Master": 5000, "Bachelor": 0, "Associate": -5000}

    base = np.array([dept_base[d] for d in department])
    mult = np.array([level_mult[l] for l in role_level])
    edu_add = np.array([edu_bonus[e] for e in education])

    salary = (
        base * mult
        + 1200 * years_experience
        + edu_add
        + 3000 * performance_score
        + rng.normal(0, 5000, n_rows)
    ).clip(30000, 300000)

    return pd.DataFrame({
        "gender": gender,
        "department": department,
        "years_experience": years_experience,
        "education": education,
        "role_level": role_level,
        "performance_score": np.round(performance_score, 2),
        "salary": np.round(salary, 0).astype(int),
    })
