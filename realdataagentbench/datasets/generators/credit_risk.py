"""Credit risk generator — correlated features + noise columns."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 800, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    age = rng.integers(21, 70, n_rows)
    income = rng.lognormal(10.5, 0.6, n_rows).clip(20000, 500000)
    debt_ratio = rng.beta(2, 5, n_rows).round(4)
    credit_score = rng.integers(300, 850, n_rows)
    num_loans = rng.integers(0, 8, n_rows)
    loan_amount = (income * rng.uniform(0.1, 0.5, n_rows)).round(2)
    employment_years = rng.integers(0, 30, n_rows)
    monthly_payment = (loan_amount / rng.uniform(12, 60, n_rows)).round(2)
    payment_history = rng.beta(5, 2, n_rows).round(4)
    utilization_rate = rng.beta(2, 3, n_rows).round(4)
    num_credit_lines = rng.integers(1, 15, n_rows)

    # Deliberately redundant: income_log ~ log(income), debt_income_ratio ~ debt_ratio/income
    income_log = np.log(income).round(4)               # r > 0.85 with income
    debt_income_ratio = (debt_ratio * 50000 / income).round(4)  # correlated with debt_ratio

    # Near-zero variance noise columns
    dummy_noise_1 = rng.normal(0, 0.001, n_rows).round(6)
    dummy_noise_2 = np.full(n_rows, 0.0) + rng.normal(0, 0.0005, n_rows)

    # Default driven by debt_ratio, credit_score, payment_history
    logit = (
        -2.0
        + debt_ratio * 3.0
        - (credit_score - 500) / 200
        - payment_history * 2.0
        + num_loans * 0.2
    )
    prob = (1 / (1 + np.exp(-logit))).clip(0.02, 0.98)
    default = rng.binomial(1, prob, n_rows)

    return pd.DataFrame({
        "age": age,
        "income": np.round(income, 2),
        "debt_ratio": debt_ratio,
        "credit_score": credit_score,
        "num_loans": num_loans,
        "loan_amount": loan_amount,
        "employment_years": employment_years,
        "monthly_payment": monthly_payment,
        "payment_history": payment_history,
        "utilization_rate": utilization_rate,
        "num_credit_lines": num_credit_lines,
        "income_log": income_log,
        "debt_income_ratio": debt_income_ratio,
        "dummy_noise_1": dummy_noise_1.round(6),
        "dummy_noise_2": dummy_noise_2.round(6),
        "default": default,
    })
