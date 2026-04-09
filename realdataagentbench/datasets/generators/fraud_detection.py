"""Fraud detection generator — imbalanced (~5% fraud)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 1000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    merchant_category = rng.choice(
        ["grocery", "electronics", "travel", "dining", "clothing"], n_rows
    )
    transaction_hour = rng.integers(0, 24, n_rows)
    customer_age = rng.integers(18, 75, n_rows)
    num_transactions_today = rng.integers(1, 20, n_rows)
    account_balance = rng.lognormal(8, 1, n_rows).clip(10, 100000).round(2)
    is_foreign = rng.binomial(1, 0.1, n_rows)

    # Base transaction amount varies by category
    cat_base = {
        "grocery": 60, "electronics": 400, "travel": 800,
        "dining": 50, "clothing": 150,
    }
    base_amount = np.array([cat_base[c] for c in merchant_category], dtype=float)
    transaction_amount = (base_amount * rng.lognormal(0, 0.5, n_rows)).clip(1, 10000).round(2)

    # Fraud: ~5%, more likely for foreign, late-night, high-amount
    logit = (
        -4.5
        + is_foreign * 2.0
        + (transaction_hour < 5).astype(float) * 1.5
        + (transaction_amount > np.percentile(transaction_amount, 90)).astype(float) * 1.2
        + (num_transactions_today > 10).astype(float) * 0.8
    )
    prob = (1 / (1 + np.exp(-logit))).clip(0.001, 0.99)
    fraud = rng.binomial(1, prob, n_rows)

    return pd.DataFrame({
        "transaction_amount": transaction_amount,
        "merchant_category": merchant_category,
        "transaction_hour": transaction_hour,
        "customer_age": customer_age,
        "num_transactions_today": num_transactions_today,
        "account_balance": account_balance,
        "is_foreign": is_foreign,
        "fraud": fraud,
    })
