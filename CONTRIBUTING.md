# Contributing to RealDataAgentBench

Thank you for your interest in contributing! This guide explains how to add tasks, generators, fix bugs, and run tests.

---

## Table of Contents

1. [Project structure](#project-structure)
2. [Adding a new task](#adding-a-new-task)
3. [Adding a new dataset generator](#adding-a-new-dataset-generator)
4. [Running tests](#running-tests)
5. [Submitting a pull request](#submitting-a-pull-request)
6. [Code style](#code-style)

---

## Project structure

```
RealDataAgentBench/
├── realdataagentbench/
│   ├── core/              # Task schema (Pydantic) and registry
│   ├── datasets/          # Dataset generators
│   │   └── generators/    # One file per dataset type
│   ├── harness/           # Agent loop, model providers, tools
│   └── scoring/           # Four-dimension scorer
├── tasks/
│   ├── eda/               # Exploratory data analysis tasks
│   ├── feature_engineering/
│   ├── modeling/
│   └── statistical_inference/
├── tests/                 # pytest suite (offline, no API calls)
├── scripts/               # build_leaderboard.py
└── docs/                  # GitHub Pages leaderboard
```

---

## Adding a new task

A task is a single YAML file under `tasks/<category>/`. The schema is validated by Pydantic — an invalid file will be rejected at load time.

### Step 1 — Create the YAML

```yaml
task_id: <category_prefix>_<NNN>          # e.g. model_006
title: "Short descriptive title"
difficulty: easy | medium | hard
category: eda | feature_engineering | modeling | statistical_inference

description: |
  Clear, numbered instructions the agent will follow.
  Include exact column names and expected outputs.

dataset:
  generator: <generator_name>             # must exist in GENERATORS dict
  seed: 42
  n_rows: 800
  schema:
    column_a: float
    column_b: int
    target: int

ground_truth:
  some_fact: true                         # boolean ground truths
  some_fact_aliases:                      # phrases that count as correct
    - "exact phrase"
    - "synonym"

scoring:
  correctness_weight: 0.40
  code_quality_weight: 0.15
  efficiency_weight: 0.15
  stat_validity_weight: 0.30              # weights must sum to 1.0

evaluation:
  max_steps: 25
  timeout_seconds: 180
  allowed_tools:
    - run_code
    - get_dataframe_info
    - get_column_stats

tags:
  - relevant_tag
```

### Step 2 — Validate

```bash
dab run <task_id> --dry-run
```

This loads and validates the task without calling any API.

### Step 3 — Add tests (optional but encouraged)

Add a test in `tests/` that checks the generator produces expected schema and the task loads correctly.

---

## Adding a new dataset generator

Each generator is a Python module under `realdataagentbench/datasets/generators/`.

```python
# realdataagentbench/datasets/generators/my_dataset.py
import numpy as np
import pandas as pd

def generate(n_rows: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    # ... build DataFrame ...
    return df
```

**Requirements:**
- Must accept `n_rows` and `seed` parameters.
- Must use `numpy.random.default_rng(seed)` for reproducibility.
- Column types must match the schema declared in the task YAML.
- No external data files — everything generated in code.

Then register it in `realdataagentbench/datasets/__init__.py`:

```python
from .generators.my_dataset import generate as generate_my_dataset

GENERATORS = {
    ...
    "my_dataset": generate_my_dataset,
}
```

---

## Running tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests (no API key required)
pytest

# Run with coverage
pytest --cov=realdataagentbench
```

All 120+ tests are offline — they test schema validation, generator shapes, scoring logic, and CLI dry-runs. No LLM API calls are made in tests.

---

## Submitting a pull request

1. Fork the repo and create a feature branch: `git checkout -b feat/my-task`
2. Make your changes.
3. Run `pytest` — all tests must pass.
4. Run `dab run <task_id> --dry-run` for any new task.
5. Open a PR with a clear description of what you added and why.

**PR checklist:**
- [ ] New task validates with `--dry-run`
- [ ] `pytest` passes locally
- [ ] Generator uses `default_rng(seed)` for reproducibility
- [ ] Task YAML scoring weights sum to 1.0
- [ ] Ground truth aliases cover common correct phrasings

---

## Code style

- Python 3.10+, type hints on all new functions.
- Use `numpy.random.default_rng` — never `np.random.seed()`.
- Generators must be deterministic given the same `seed`.
- No external data files in the repo.
- Keep tasks self-contained: the dataset must fully encode the problem.

---

Questions? Open an issue or email the maintainer via GitHub.
