"""Energy consumption dataset — regression predicting building energy use."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 600, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    building_area = rng.normal(1500, 600, n_rows).clip(200, 5000)
    num_floors = rng.integers(1, 10, n_rows)
    occupants = rng.integers(1, 50, n_rows)
    avg_temp_celsius = rng.normal(15, 8, n_rows).clip(-5, 40)
    insulation_rating = rng.uniform(1, 5, n_rows)   # 1=poor, 5=excellent
    hvac_age_years = rng.integers(0, 25, n_rows)
    windows_ratio = rng.uniform(0.1, 0.4, n_rows)   # window-to-wall ratio
    solar_panels = rng.choice([0, 1], n_rows, p=[0.7, 0.3])
    building_type = rng.integers(0, 4, n_rows)  # 0=office,1=retail,2=residential,3=industrial

    # Energy use: area + occupants drive base, insulation + solar reduce it
    energy_kwh = (
        0.06 * building_area
        + 15 * occupants
        + 8 * num_floors
        + 2.0 * abs(avg_temp_celsius - 18)  # heating/cooling delta
        - 20 * insulation_rating
        + 1.5 * hvac_age_years
        + 30 * windows_ratio * building_area / 100
        - 40 * solar_panels
        + building_type * 10
        + rng.normal(0, 30, n_rows)
    ).clip(50, 3000)

    return pd.DataFrame({
        "building_area": np.round(building_area, 1),
        "num_floors": num_floors,
        "occupants": occupants,
        "avg_temp_celsius": np.round(avg_temp_celsius, 1),
        "insulation_rating": np.round(insulation_rating, 2),
        "hvac_age_years": hvac_age_years,
        "windows_ratio": np.round(windows_ratio, 3),
        "solar_panels": solar_panels,
        "building_type": building_type,
        "energy_kwh_per_day": np.round(energy_kwh, 1),
    })
