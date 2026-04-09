"""Pydantic schema for DataAgentBench task definitions."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class TaskDataset(BaseModel):
    generator: str
    seed: int = 42
    n_rows: int = Field(gt=0)
    columns: dict[str, str] = Field(alias="schema")  # avoids shadowing pydantic .schema()
    injected_issues: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class ScoringCriteria(BaseModel):
    correctness_weight: float = Field(ge=0.0, le=1.0)
    code_quality_weight: float = Field(ge=0.0, le=1.0)
    efficiency_weight: float = Field(ge=0.0, le=1.0)
    stat_validity_weight: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> "ScoringCriteria":
        total = (
            self.correctness_weight
            + self.code_quality_weight
            + self.efficiency_weight
            + self.stat_validity_weight
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Scoring weights must sum to 1.0, got {total:.4f}")
        return self


class EvaluationConfig(BaseModel):
    max_steps: int = Field(gt=0, default=10)
    timeout_seconds: int = Field(gt=0, default=120)
    allowed_tools: list[str] = Field(default_factory=list)


class TaskSchema(BaseModel):
    task_id: str
    title: str
    difficulty: Literal["easy", "medium", "hard"]
    category: str
    description: str
    dataset: TaskDataset
    ground_truth: dict[str, Any]
    scoring: ScoringCriteria
    evaluation: EvaluationConfig
    tags: list[str] = Field(default_factory=list)

    @field_validator("task_id")
    @classmethod
    def task_id_format(cls, v: str) -> str:
        if not v.replace("_", "").isalnum():
            raise ValueError(f"task_id must be alphanumeric+underscore, got: {v!r}")
        return v

    @classmethod
    def from_yaml(cls, path: Path | str) -> "TaskSchema":
        path = Path(path)
        with path.open() as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)
