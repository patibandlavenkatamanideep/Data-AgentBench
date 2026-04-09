"""Execution tracer — records every step, tool call, and token count."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class TraceStep:
    step: int
    role: Literal["assistant", "tool"]
    content: str
    tool_name: str | None = None
    tool_input: dict | None = None
    tool_output: Any = None
    input_tokens: int = 0
    output_tokens: int = 0
    elapsed_seconds: float = 0.0


@dataclass
class Trace:
    task_id: str
    model: str
    steps: list[TraceStep] = field(default_factory=list)
    final_answer: str = ""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_elapsed_seconds: float = 0.0
    error: str | None = None

    def add_step(self, step: TraceStep) -> None:
        self.steps.append(step)
        self.total_input_tokens += step.input_tokens
        self.total_output_tokens += step.output_tokens
        self.total_elapsed_seconds += step.elapsed_seconds

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "model": self.model,
            "final_answer": self.final_answer,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_elapsed_seconds": round(self.total_elapsed_seconds, 3),
            "num_steps": len(self.steps),
            "error": self.error,
            "steps": [
                {
                    "step": s.step,
                    "role": s.role,
                    "content": s.content[:500],  # truncate for JSON
                    "tool_name": s.tool_name,
                    "tool_input": s.tool_input,
                    "tool_output": str(s.tool_output)[:500] if s.tool_output else None,
                    "input_tokens": s.input_tokens,
                    "output_tokens": s.output_tokens,
                    "elapsed_seconds": round(s.elapsed_seconds, 3),
                }
                for s in self.steps
            ],
        }


class Tracer:
    def __init__(self, task_id: str, model: str):
        self.trace = Trace(task_id=task_id, model=model)
        self._step_counter = 0
        self._t0 = time.monotonic()

    def record(
        self,
        role: Literal["assistant", "tool"],
        content: str,
        tool_name: str | None = None,
        tool_input: dict | None = None,
        tool_output: Any = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> TraceStep:
        self._step_counter += 1
        elapsed = time.monotonic() - self._t0
        step = TraceStep(
            step=self._step_counter,
            role=role,
            content=content,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            elapsed_seconds=elapsed,
        )
        self.trace.add_step(step)
        self._t0 = time.monotonic()
        return step

    def finalize(self, final_answer: str, error: str | None = None) -> Trace:
        self.trace.final_answer = final_answer
        self.trace.error = error
        return self.trace
