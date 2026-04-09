"""Claude agentic loop — now delegates to providers.py for multi-model support."""

from __future__ import annotations

import pandas as pd

from .providers import get_provider, resolve_model
from .tracer import Trace, Tracer

DEFAULT_MODEL = "claude-sonnet-4-6"


class Agent:
    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None):
        self.model = resolve_model(model)
        # api_key override kept for backwards compatibility — providers read from env
        self._api_key = api_key

    def run(
        self,
        task_description: str,
        dataframe: pd.DataFrame,
        task_id: str,
        max_steps: int = 10,
        timeout_seconds: int = 120,
        allowed_tools: list[str] | None = None,
    ) -> Trace:
        tracer = Tracer(task_id=task_id, model=self.model)
        provider = get_provider(self.model)

        try:
            final_answer = provider.run(
                task_description=task_description,
                dataframe=dataframe,
                max_steps=max_steps,
                allowed_tools=allowed_tools,
                tracer=tracer,
            )
            error = None
            steps = len(tracer.trace.steps)
            if steps >= max_steps:
                error = f"Reached max_steps={max_steps} without end_turn"
        except Exception as e:
            final_answer = ""
            error = str(e)

        return tracer.finalize(final_answer=final_answer, error=error)
