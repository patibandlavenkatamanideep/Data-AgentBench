# Contributing to RealDataAgentBench

Anyone can add a new task or a new model in about 10 minutes. This guide walks through both, plus the full PR checklist.

---

## Quick-start

```bash
git clone https://github.com/patibandlavenkatamanideep/RealDataAgentBench
cd RealDataAgentBench
pip install -e ".[dev]"
pytest            # 150 tests, all offline — no API key needed
```

---

## Table of Contents

1. [Add a new task (~10 min)](#add-a-new-task)
2. [Add a new model provider (~10 min)](#add-a-new-model-provider)
3. [Add a new dataset generator](#add-a-new-dataset-generator)
4. [Running tests](#running-tests)
5. [Submitting a pull request](#submitting-a-pull-request)
6. [Code style](#code-style)

---

## Add a new task

A task is one YAML file. Pydantic validates it at load time — wrong fields are caught immediately.

### Step 1 — Create the YAML

```
tasks/<category>/<task_id>.yaml
```

Categories: `eda`, `feature_engineering`, `modeling`, `statistical_inference`, `ml_engineering`

```yaml
task_id: eda_004                          # unique, follows existing pattern
title: "Short descriptive title"
difficulty: easy | medium | hard
category: eda

description: |
  Numbered instructions the agent will follow.
  Reference exact column names. State what to compute and report.
  Example: "1. Compute the Pearson correlation between X and Y."

dataset:
  generator: my_generator                 # must exist in GENERATORS dict
  seed: 42
  n_rows: 800
  columns:
    - col_a
    - col_b
  schema:
    col_a: float
    col_b: int

ground_truth:
  correlation_positive: true              # booleans are easiest to score
  skewness_direction: "right"
  skewness_direction_aliases:
    - "positively skewed"
    - "right-skewed"

scoring:
  correctness_weight: 0.45
  code_quality_weight: 0.20
  efficiency_weight: 0.15
  stat_validity_weight: 0.20              # must sum to 1.0

evaluation:
  max_steps: 20
  timeout_seconds: 120
  allowed_tools:
    - run_code
    - get_dataframe_info
    - get_column_stats

tags:
  - correlation
  - eda
```

### Step 2 — Validate (no API key needed)

```bash
dab run eda_004 --dry-run
```

Fix any schema errors, then confirm the task loads and the dataset generates correctly.

### Step 3 — Add a test

```python
# tests/test_my_task.py
def test_eda_004_loads():
    from realdataagentbench.core.registry import TaskRegistry
    from pathlib import Path
    registry = TaskRegistry(Path("tasks"))
    task = registry.get("eda_004")
    weights = (task.scoring.correctness_weight + task.scoring.code_quality_weight
               + task.scoring.efficiency_weight + task.scoring.stat_validity_weight)
    assert abs(weights - 1.0) < 1e-9
```

### Step 4 — Open a PR

That's it. The CI runs all tests and validates your YAML automatically.

---

## Add a new model provider

The entire provider interface is in [realdataagentbench/harness/providers.py](realdataagentbench/harness/providers.py). Adding a new model is ~20 lines.

### Option A — OpenAI-compatible API (Groq, Together, Mistral, xAI Grok)

Most new providers expose an OpenAI-compatible endpoint. Subclass `OpenAIProvider`:

```python
# In providers.py

GROK_MODELS = {
    "grok-2",
    "grok-3",
    "grok",               # short alias
}

MODEL_ALIASES["grok"] = "grok-3"

class GrokProvider(OpenAIProvider):
    """xAI Grok — OpenAI-compatible endpoint."""
    def __init__(self, model: str):
        BaseProvider.__init__(self, model)
        from openai import OpenAI
        api_key = os.environ.get("XAI_API_KEY")
        if not api_key:
            raise EnvironmentError("XAI_API_KEY is not set.")
        self.client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
```

Then add one line to `get_provider()`:

```python
if model.startswith("grok"):
    return GrokProvider(model)
```

And add the model to `COST_PER_M_TOKENS` so `--budget` works correctly.

### Option B — Custom SDK (Gemini, Cohere, etc.)

Write a `GeminiProvider(BaseProvider)` that implements `run()` with the same signature:

```python
def run(self, task_description, dataframe, max_steps, allowed_tools, tracer, budget=None) -> str:
```

The method must:
1. Call the model API in a loop up to `max_steps`
2. Dispatch tool calls via `dispatch_tool(name, inputs, dataframe)`
3. Call `tracer.record(role, content, input_tokens, output_tokens)` after each step
4. Call `self._check_budget(compute_cost(self.model, total_in, total_out), budget)` after each step
5. Return the final answer string

See `AnthropicProvider` as the reference implementation.

### Step 3 — Update `dab models`

Add the new model set to the import in `cli.py` and add a loop in `list_models()`.

### Step 4 — Test

```bash
dab run eda_001 --model grok --dry-run   # validate without API call
dab run eda_001 --model grok             # live test (needs XAI_API_KEY)
```

---

## Add a new dataset generator

```python
# realdataagentbench/datasets/generators/my_dataset.py
import numpy as np
import pandas as pd

def generate(n_rows: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "col_a": rng.normal(0, 1, n_rows),
        "col_b": rng.integers(0, 10, n_rows),
    })
```

Register it in `realdataagentbench/datasets/__init__.py`:

```python
from .generators.my_dataset import generate as generate_my_dataset

GENERATORS = {
    ...
    "my_dataset": generate_my_dataset,
}
```

**Rules:**
- Use `numpy.random.default_rng(seed)` — never `np.random.seed()`.
- No external data files — everything generated in code.
- Column types must match the task YAML `schema`.

---

## Running tests

```bash
pytest                                     # 150 tests, ~25s, no API key needed
pytest --cov=realdataagentbench           # with coverage
pytest tests/test_eda_generators.py -v    # single file
```

---

## Submitting a pull request

1. Fork → feature branch: `git checkout -b feat/my-task`
2. Make changes, run `pytest` — all 150 must pass.
3. `dab run <task_id> --dry-run` for any new task.
4. Open a PR. CI runs automatically.

**PR checklist:**
- [ ] `pytest` passes locally (150 tests)
- [ ] New task validates with `dab run <id> --dry-run`
- [ ] Scoring weights sum to 1.0
- [ ] Generator uses `default_rng(seed)` for reproducibility
- [ ] Ground truth aliases cover common correct phrasings
- [ ] New provider: `COST_PER_M_TOKENS` entry added

---

## Code style

- Python 3.10+, type hints on all new functions.
- `numpy.random.default_rng` — never `np.random.seed()`.
- No external data files in the repo.
- Keep tasks self-contained: the dataset must fully encode the problem.

---

Questions? [Open an issue](https://github.com/patibandlavenkatamanideep/RealDataAgentBench/issues) or start a [Discussion](https://github.com/patibandlavenkatamanideep/RealDataAgentBench/discussions).
