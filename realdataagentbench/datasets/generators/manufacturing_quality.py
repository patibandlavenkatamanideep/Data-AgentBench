"""Manufacturing quality dataset — SPC/process capability and defect rate analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd


def generate(n_rows: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Two machines: machine A is in control, machine B has drift
    machine = rng.choice(["A", "B"], n_rows, p=[0.5, 0.5])
    is_b = (machine == "B").astype(int)

    shift = rng.integers(1, 4, n_rows)  # 1=day, 2=evening, 3=night

    # Measurement: target=10.0, spec_limits = [9.5, 10.5]
    true_mean = 10.0 + 0.15 * is_b  # machine B drifts high by 0.15
    sigma_a = 0.12
    sigma_b = 0.18  # machine B also has higher variability

    sigma = np.where(is_b, sigma_b, sigma_a)
    measurement = true_mean + rng.normal(0, sigma, n_rows)

    # Machine wear adds slow drift for B
    batch_num = np.arange(1, n_rows + 1)
    drift = np.where(is_b, 0.0003 * batch_num, 0)
    measurement += drift

    temperature = rng.normal(22, 2, n_rows).clip(16, 30)
    humidity = rng.normal(45, 8, n_rows).clip(20, 80)

    defect = ((measurement < 9.5) | (measurement > 10.5)).astype(int)

    return pd.DataFrame({
        "batch_id": batch_num,
        "machine": machine,
        "shift": shift,
        "measurement": np.round(measurement, 4),
        "temperature": np.round(temperature, 1),
        "humidity": np.round(humidity, 1),
        "defect": defect,
    })
