"""Employee attrition generator — mixed categorical + numeric."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 600, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    departments = rng.choice(["Engineering", "Sales", "HR", "Finance", "Marketing"], n_rows)
    job_roles = rng.choice(
        ["Manager", "Analyst", "Engineer", "Director", "Intern",
         "Consultant", "Specialist", "Lead", "Associate", "Executive"],
        n_rows,
    )
    education = rng.choice(["High School", "Bachelor", "Master", "PhD"], n_rows)
    gender = rng.choice(["Male", "Female"], n_rows)
    overtime = rng.choice(["Yes", "No"], n_rows)

    age = rng.integers(22, 60, n_rows)
    years_at_company = rng.integers(0, 20, n_rows)
    monthly_income = (
        3000 + age * 100 + years_at_company * 200 + rng.normal(0, 500, n_rows)
    ).clip(1500, 25000)
    satisfaction_score = rng.uniform(1.0, 5.0, n_rows).round(2)

    # Attrition driven by income, satisfaction, overtime
    logit = (
        -3.0
        + (monthly_income < 5000).astype(float) * 1.5
        + (overtime == "Yes").astype(float) * 1.2
        + (satisfaction_score < 2.5).astype(float) * 1.0
    )
    prob = 1 / (1 + np.exp(-logit))
    attrition = rng.binomial(1, prob, n_rows)

    return pd.DataFrame({
        "age": age,
        "department": departments,
        "job_role": job_roles,
        "education": education,
        "gender": gender,
        "years_at_company": years_at_company,
        "monthly_income": np.round(monthly_income, 2),
        "overtime": overtime,
        "satisfaction_score": satisfaction_score,
        "attrition": attrition,
    })
