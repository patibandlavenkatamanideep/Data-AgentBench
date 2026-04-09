"""Model providers — unified interface for Claude, GPT-4o, and future models."""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from .tools import TOOL_DEFINITIONS, get_column_stats, get_dataframe_info, run_code

# ── Model name aliases ────────────────────────────────────────────────────────

ANTHROPIC_MODELS = {
    "claude-sonnet-4-6",
    "claude-opus-4-6",
    "claude-haiku-4-5-20251001",
    # short aliases
    "claude", "sonnet", "opus", "haiku",
}

OPENAI_MODELS = {
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
    # short aliases
    "gpt4o", "gpt-4o-2024-11-20",
}

MODEL_ALIASES = {
    "claude": "claude-sonnet-4-6",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-6",
    "haiku": "claude-haiku-4-5-20251001",
    "gpt4o": "gpt-4o",
}

SYSTEM_PROMPT = """You are an expert data scientist working on a benchmark task.
You have access to a pandas DataFrame called `df` loaded with the task dataset.
Use the provided tools to analyse the data. After completing your analysis,
write a clear, structured final answer that directly addresses all sub-questions
in the task description. Be precise — include exact numeric values where computed."""


def resolve_model(model: str) -> str:
    """Resolve short alias to canonical model name."""
    return MODEL_ALIASES.get(model, model)


def get_provider(model: str) -> "BaseProvider":
    """Return the correct provider instance for a model name."""
    model = resolve_model(model)
    if any(model.startswith(p) for p in ("claude",)):
        return AnthropicProvider(model)
    if any(model.startswith(p) for p in ("gpt-", "gpt4")):
        return OpenAIProvider(model)
    raise ValueError(
        f"Unknown model: {model!r}. "
        f"Supported prefixes: 'claude-', 'gpt-'. "
        f"Add new providers in harness/providers.py."
    )


# ── Shared tool dispatcher ────────────────────────────────────────────────────

def dispatch_tool(name: str, inputs: dict, dataframe: pd.DataFrame) -> Any:
    if name == "run_code":
        return run_code(inputs["code"], dataframe)
    elif name == "get_dataframe_info":
        return get_dataframe_info(dataframe)
    elif name == "get_column_stats":
        return get_column_stats(inputs["column_name"], dataframe)
    return {"error": f"Unknown tool: {name!r}"}


# ── Base provider ─────────────────────────────────────────────────────────────

class BaseProvider(ABC):
    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def run(
        self,
        task_description: str,
        dataframe: pd.DataFrame,
        max_steps: int,
        allowed_tools: list[str] | None,
        tracer,
    ) -> str:
        """Run the agentic loop. Returns final answer string."""

    def _filter_tools(self, allowed: list[str] | None) -> list[dict]:
        if not allowed:
            return TOOL_DEFINITIONS
        return [t for t in TOOL_DEFINITIONS if t["name"] in allowed]


# ── Anthropic provider ────────────────────────────────────────────────────────

class AnthropicProvider(BaseProvider):
    def __init__(self, model: str):
        super().__init__(model)
        import anthropic
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )

    def run(self, task_description, dataframe, max_steps, allowed_tools, tracer):
        import anthropic
        tools = self._filter_tools(allowed_tools)
        messages: list[dict] = [{"role": "user", "content": task_description}]

        for _ in range(max_steps):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=tools,
                messages=messages,
            )

            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            assistant_text = ""
            tool_uses = []

            for block in response.content:
                if block.type == "text":
                    assistant_text += block.text
                elif block.type == "tool_use":
                    tool_uses.append(block)

            tracer.record(
                role="assistant",
                content=assistant_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

            if response.stop_reason == "end_turn" or not tool_uses:
                return assistant_text

            messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for tu in tool_uses:
                result = dispatch_tool(tu.name, tu.input, dataframe)
                result_str = json.dumps(result) if isinstance(result, dict) else str(result)
                tracer.record(
                    role="tool",
                    content=result_str,
                    tool_name=tu.name,
                    tool_input=tu.input,
                    tool_output=result,
                )
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": result_str,
                })

            messages.append({"role": "user", "content": tool_results})

        return assistant_text


# ── OpenAI provider ───────────────────────────────────────────────────────────

class OpenAIProvider(BaseProvider):
    def __init__(self, model: str):
        super().__init__(model)
        from openai import OpenAI
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def _tools_to_openai(self, tools: list[dict]) -> list[dict]:
        """Convert Anthropic tool schema format to OpenAI function format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
            for t in tools
        ]

    def run(self, task_description, dataframe, max_steps, allowed_tools, tracer):
        tools = self._filter_tools(allowed_tools)
        oai_tools = self._tools_to_openai(tools)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task_description},
        ]

        assistant_text = ""

        for _ in range(max_steps):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=oai_tools,
                tool_choice="auto",
                max_tokens=4096,
            )

            choice = response.choices[0]
            msg = choice.message
            usage = response.usage

            assistant_text = msg.content or ""
            tool_calls = msg.tool_calls or []

            tracer.record(
                role="assistant",
                content=assistant_text,
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
            )

            if choice.finish_reason == "stop" or not tool_calls:
                return assistant_text

            # Add assistant message with tool calls
            messages.append(msg)

            for tc in tool_calls:
                try:
                    inputs = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    inputs = {}

                result = dispatch_tool(tc.function.name, inputs, dataframe)
                result_str = json.dumps(result) if isinstance(result, dict) else str(result)

                tracer.record(
                    role="tool",
                    content=result_str,
                    tool_name=tc.function.name,
                    tool_input=inputs,
                    tool_output=result,
                )

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str,
                })

        return assistant_text
