"""Runner — orchestrates task → dataset → agent → trace → results JSON."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ..core.registry import TaskRegistry
from ..core.task import TaskSchema
from ..datasets import get_generator
from .agent import Agent
from .tracer import Trace


class Runner:
    def __init__(
        self,
        registry: TaskRegistry,
        model: str = "claude-sonnet-4-6",
        output_dir: Path | str = "outputs",
        api_key: str | None = None,
        dry_run: bool = False,
    ):
        self.registry = registry
        self.model = model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.agent = Agent(model=model, api_key=api_key)
        self.dry_run = dry_run

    def run_task(self, task_id: str) -> dict:
        task = self.registry.get(task_id)
        df = self._load_dataset(task)

        if self.dry_run:
            return self._dry_run_result(task, df)

        trace = self.agent.run(
            task_description=task.description,
            dataframe=df,
            task_id=task.task_id,
            max_steps=task.evaluation.max_steps,
            timeout_seconds=task.evaluation.timeout_seconds,
            allowed_tools=task.evaluation.allowed_tools,
        )

        result = self._build_result(task, trace, df)
        self._save_result(result)
        return result

    def run_all(
        self,
        difficulty: str | None = None,
        category: str | None = None,
    ) -> list[dict]:
        tasks = self.registry.filter(difficulty=difficulty, category=category)
        results = []
        for task in tasks:
            result = self.run_task(task.task_id)
            results.append(result)
        manifest = {
            "run_at": datetime.now(timezone.utc).isoformat(),
            "model": self.model,
            "num_tasks": len(results),
            "results": [r["task_id"] for r in results],
        }
        (self.output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2)
        )
        return results

    def _load_dataset(self, task: TaskSchema) -> pd.DataFrame:
        gen = get_generator(task.dataset.generator)
        return gen(n_rows=task.dataset.n_rows, seed=task.dataset.seed)

    def _build_result(self, task: TaskSchema, trace: Trace, df: pd.DataFrame) -> dict:
        return {
            "task_id": task.task_id,
            "title": task.title,
            "difficulty": task.difficulty,
            "category": task.category,
            "model": self.model,
            "run_at": datetime.now(timezone.utc).isoformat(),
            "dataset_shape": list(df.shape),
            "trace": trace.to_dict(),
        }

    def _dry_run_result(self, task: TaskSchema, df: pd.DataFrame) -> dict:
        return {
            "task_id": task.task_id,
            "title": task.title,
            "difficulty": task.difficulty,
            "category": task.category,
            "model": self.model,
            "dry_run": True,
            "dataset_shape": list(df.shape),
            "dataset_columns": list(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
        }

    def _save_result(self, result: dict) -> Path:
        fname = f"{result['task_id']}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json"
        path = self.output_dir / fname
        path.write_text(json.dumps(result, indent=2))
        return path
