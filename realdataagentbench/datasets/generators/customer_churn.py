"""Customer churn dataset — binary classification for telecom churn prediction."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 900, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    tenure_months = rng.integers(1, 73, n_rows)
    monthly_charges = rng.normal(65, 30, n_rows).clip(18, 120)
    total_charges = (tenure_months * monthly_charges + rng.normal(0, 50, n_rows)).clip(0)
    num_services = rng.integers(1, 9, n_rows)
    contract_type = rng.choice([0, 1, 2], n_rows, p=[0.55, 0.21, 0.24])  # month/1yr/2yr
    payment_method = rng.integers(0, 4, n_rows)
    tech_support = rng.integers(0, 2, n_rows)
    online_security = rng.integers(0, 2, n_rows)
    senior_citizen = rng.choice([0, 1], n_rows, p=[0.84, 0.16])
    paperless_billing = rng.integers(0, 2, n_rows)

    # Churn is higher for: short tenure, month-to-month, high charges, no security
    log_odds = (
        2.0
        - 0.06 * tenure_months
        - 0.015 * contract_type * 12
        + 0.02 * monthly_charges
        - 0.3 * tech_support
        - 0.3 * online_security
        + 0.4 * senior_citizen
        + rng.normal(0, 0.4, n_rows)
    )
    prob_churn = 1 / (1 + np.exp(-log_odds))
    churn = (rng.uniform(0, 1, n_rows) < prob_churn).astype(int)

    return pd.DataFrame({
        "tenure_months": tenure_months,
        "monthly_charges": np.round(monthly_charges, 2),
        "total_charges": np.round(total_charges, 2),
        "num_services": num_services,
        "contract_type": contract_type,  # 0=month, 1=1yr, 2=2yr
        "payment_method": payment_method,
        "tech_support": tech_support,
        "online_security": online_security,
        "senior_citizen": senior_citizen,
        "paperless_billing": paperless_billing,
        "churn": churn,
    })
