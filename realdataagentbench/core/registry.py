"""Task registry — discovers, loads, and filters tasks from the tasks/ directory."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from .task import TaskSchema


class TaskRegistry:
    def __init__(self, tasks_dir: Path | str | None = None):
        if tasks_dir is None:
            tasks_dir = Path(__file__).parent.parent.parent / "tasks"
        self._dir = Path(tasks_dir)
        self._tasks: dict[str, TaskSchema] = {}
        self._load_all()

    def _load_all(self) -> None:
        for yaml_file in sorted(self._dir.rglob("*.yaml")):
            task = TaskSchema.from_yaml(yaml_file)
            self._tasks[task.task_id] = task

    def get(self, task_id: str) -> TaskSchema:
        if task_id not in self._tasks:
            raise KeyError(f"Task not found: {task_id!r}. Available: {list(self._tasks)}")
        return self._tasks[task_id]

    def all(self) -> list[TaskSchema]:
        return list(self._tasks.values())

    def filter(
        self,
        difficulty: Literal["easy", "medium", "hard"] | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> list[TaskSchema]:
        results = self.all()
        if difficulty:
            results = [t for t in results if t.difficulty == difficulty]
        if category:
            results = [t for t in results if t.category == category]
        if tags:
            results = [t for t in results if all(tag in t.tags for tag in tags)]
        return results

    def summary(self) -> dict:
        tasks = self.all()
        return {
            "total": len(tasks),
            "by_difficulty": {
                d: len([t for t in tasks if t.difficulty == d])
                for d in ("easy", "medium", "hard")
            },
            "by_category": {
                cat: len([t for t in tasks if t.category == cat])
                for cat in sorted({t.category for t in tasks})
            },
        }

    def __len__(self) -> int:
        return len(self._tasks)

    def __contains__(self, task_id: str) -> bool:
        return task_id in self._tasks
