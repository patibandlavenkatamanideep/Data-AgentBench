"""Composite scorer — combines all four dimensions into a DAB score."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core.task import TaskSchema
from .code_quality import CodeQualityScorer
from .correctness import CorrectnessScorer
from .efficiency import EfficiencyScorer
from .stat_validity import StatValidityScorer


@dataclass
class ScoreCard:
    task_id: str
    difficulty: str
    correctness: float
    code_quality: float
    efficiency: float
    stat_validity: float
    dab_score: float
    weights: dict[str, float] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "difficulty": self.difficulty,
            "correctness": self.correctness,
            "code_quality": self.code_quality,
            "efficiency": self.efficiency,
            "stat_validity": self.stat_validity,
            "dab_score": self.dab_score,
            "weights": self.weights,
            "details": self.details,
        }

    def __str__(self) -> str:
        return (
            f"ScoreCard({self.task_id})\n"
            f"  Correctness:   {self.correctness:.3f}\n"
            f"  Code Quality:  {self.code_quality:.3f}\n"
            f"  Efficiency:    {self.efficiency:.3f}\n"
            f"  Stat Validity: {self.stat_validity:.3f}\n"
            f"  DAB Score:     {self.dab_score:.3f}"
        )


class CompositeScorer:
    def __init__(self):
        self.correctness_scorer = CorrectnessScorer()
        self.code_quality_scorer = CodeQualityScorer()
        self.efficiency_scorer = EfficiencyScorer()
        self.stat_validity_scorer = StatValidityScorer()

    def score(self, task: TaskSchema, result: dict) -> ScoreCard:
        trace = result.get("trace", {})
        answer = trace.get("final_answer", "")
        steps = trace.get("steps", [])
        total_tokens = trace.get("total_input_tokens", 0) + trace.get("total_output_tokens", 0)
        num_steps = trace.get("num_steps", 0)
        has_error = bool(trace.get("error"))

        # Extract code snippets from tool calls
        code_snippets = [
            s["tool_input"]["code"]
            for s in steps
            if s.get("tool_name") == "run_code" and s.get("tool_input", {}).get("code")
        ]

        c_score = self.correctness_scorer.score(answer, task.ground_truth)
        q_score = self.code_quality_scorer.score(code_snippets)
        e_score = self.efficiency_scorer.score(
            total_tokens=total_tokens,
            steps_used=num_steps,
            max_steps=task.evaluation.max_steps,
            difficulty=task.difficulty,
            has_error=has_error,
        )
        s_score = self.stat_validity_scorer.score(answer, category=task.category)

        w = task.scoring
        dab_score = round(
            c_score * w.correctness_weight
            + q_score * w.code_quality_weight
            + e_score * w.efficiency_weight
            + s_score * w.stat_validity_weight,
            4,
        )

        return ScoreCard(
            task_id=task.task_id,
            difficulty=task.difficulty,
            correctness=c_score,
            code_quality=q_score,
            efficiency=e_score,
            stat_validity=s_score,
            dab_score=dab_score,
            weights={
                "correctness": w.correctness_weight,
                "code_quality": w.code_quality_weight,
                "efficiency": w.efficiency_weight,
                "stat_validity": w.stat_validity_weight,
            },
            details={
                "total_tokens": total_tokens,
                "num_steps": num_steps,
                "has_error": has_error,
                "code_snippets_count": len(code_snippets),
            },
        )

    @classmethod
    def from_result_file(cls, result_path: Path | str, task: TaskSchema) -> ScoreCard:
        data = json.loads(Path(result_path).read_text())
        return cls().score(task, data)
