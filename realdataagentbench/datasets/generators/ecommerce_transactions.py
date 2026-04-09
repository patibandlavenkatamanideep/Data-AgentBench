"""E-commerce transactions generator — Simpson's Paradox setup."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 2000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Three segments with very different baseline revenues
    # Enterprise: large orders, large revenue, but also large discounts (procurement)
    # SMB: medium orders, medium revenue, small discounts
    # Consumer: small orders, low revenue, tiny discounts
    segments = rng.choice(
        ["enterprise", "smb", "consumer"],
        size=n_rows,
        p=[0.20, 0.35, 0.45],
    )

    discount_pct = np.zeros(n_rows)
    order_size = np.zeros(n_rows)
    revenue = np.zeros(n_rows)

    for i, seg in enumerate(segments):
        if seg == "enterprise":
            # Low discount (locked contract pricing), very high revenue
            d = rng.uniform(0.02, 0.08)
            o = rng.normal(50_000, 8_000)
            r = o * (1 + d * 0.1) + rng.normal(0, 500)   # slight +ve within-group
        elif seg == "smb":
            # Medium discount, medium revenue
            d = rng.uniform(0.08, 0.18)
            o = rng.normal(6_000, 1_500)
            r = o * (1 + d * 0.05) + rng.normal(0, 150)
        else:  # consumer
            # High discount (promotional), very low revenue
            d = rng.uniform(0.20, 0.45)
            o = rng.normal(150, 50)
            r = o * (1 + d * 0.02) + rng.normal(0, 8)

        discount_pct[i] = max(0.0, min(0.99, d))
        order_size[i] = max(10.0, o)
        revenue[i] = max(1.0, r)

    # Raw correlation: consumer = high discount + low revenue → strongly negative
    # Within each segment: discount is slightly positive (more promotions → more volume)
    # Partial (controlling order_size) collapses toward zero → Simpson's Paradox

    return pd.DataFrame({
        "transaction_id": np.arange(1, n_rows + 1),
        "customer_segment": segments,
        "order_size": np.round(order_size, 2),
        "discount_pct": np.round(discount_pct, 4),
        "revenue": np.round(revenue, 2),
    })
