"""House prices generator — engineered features improve R²."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    total_sqft = rng.normal(1800, 500, n_rows).clip(600, 5000)
    num_rooms = rng.integers(3, 10, n_rows)
    house_age = rng.integers(1, 50, n_rows)
    garage = rng.integers(0, 3, n_rows)

    # Price driven by sqft, rooms, age interaction — engineered features capture this better
    price = (
        120 * total_sqft
        + 8000 * num_rooms
        - 1500 * house_age
        + 5000 * garage
        - 0.8 * house_age * total_sqft          # interaction term
        + rng.normal(0, 15000, n_rows)
    ).clip(50000, 2_000_000)

    return pd.DataFrame({
        "total_sqft": np.round(total_sqft, 1),
        "num_rooms": num_rooms,
        "house_age": house_age,
        "garage": garage,
        "price": np.round(price, 2),
    })
