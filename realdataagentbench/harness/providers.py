"""Model providers — unified interface for Claude, GPT-4o, Groq, and future models."""

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

GROQ_MODELS = {
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
    # short aliases
    "groq", "llama", "llama-70b", "llama-8b", "mixtral",
}

MODEL_ALIASES = {
    "claude": "claude-sonnet-4-6",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-6",
    "haiku": "claude-haiku-4-5-20251001",
    "gpt4o": "gpt-4o",
    # Groq shortcuts
    "groq": "llama-3.3-70b-versatile",
    "llama": "llama-3.3-70b-versatile",
    "llama-70b": "llama-3.3-70b-versatile",
    "llama-8b": "llama-3.1-8b-instant",
    "mixtral": "mixtral-8x7b-32768",
}

# ── Cost table (USD per million tokens) ──────────────────────────────────────
# Source: official pricing pages as of April 2026.
# Groq has a free tier with rate limits — paid tier prices shown here.

COST_PER_M_TOKENS: dict[str, tuple[float, float]] = {
    # model_id: (input_$/M, output_$/M)
    "claude-sonnet-4-6":        (3.00,  15.00),
    "claude-opus-4-6":          (15.00, 75.00),
    "claude-haiku-4-5-20251001": (0.25,   1.25),
    "gpt-4o":                   (2.50,  10.00),
    "gpt-4o-mini":              (0.15,   0.60),
    "gpt-4-turbo":              (10.00, 30.00),
    "gpt-4":                    (30.00, 60.00),
    "gpt-3.5-turbo":            (0.50,   1.50),
    # Groq — very cheap, some models have free tiers
    "llama-3.3-70b-versatile":  (0.59,   0.79),
    "llama-3.1-70b-versatile":  (0.59,   0.79),
    "llama-3.1-8b-instant":     (0.05,   0.08),
    "llama3-70b-8192":          (0.59,   0.79),
    "llama3-8b-8192":           (0.05,   0.08),
    "mixtral-8x7b-32768":       (0.24,   0.24),
    "gemma2-9b-it":             (0.20,   0.20),
}

_FALLBACK_COST = (1.00, 3.00)  # conservative fallback for unknown models


def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return estimated cost in USD for a given number of tokens."""
    in_per_m, out_per_m = COST_PER_M_TOKENS.get(model, _FALLBACK_COST)
    return (input_tokens * in_per_m + output_tokens * out_per_m) / 1_000_000


SYSTEM_PROMPT = """You are an expert data scientist working on a benchmark task.
You have access to a pandas DataFrame called `df` loaded with the task dataset.
Use the provided tools to analyse the data. After completing your analysis,
write a clear, structured final answer that directly addresses all sub-questions
in the task description. Be precise — include exact numeric values where computed."""


# ── Budget exceeded error ─────────────────────────────────────────────────────

class BudgetExceededError(Exception):
    """Raised when cumulative cost of a run exceeds the user-set budget."""
    def __init__(self, spent: float, budget: float):
        self.spent = spent
        self.budget = budget
        super().__init__(
            f"Budget exceeded: spent ${spent:.4f} > budget ${budget:.4f}. "
            "Stopping run. Use --budget to set a higher limit."
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def resolve_model(model: str) -> str:
    """Resolve short alias to canonical model name."""
    return MODEL_ALIASES.get(model, model)


def get_provider(model: str) -> "BaseProvider":
    """Return the correct provider instance for a model name."""
    model = resolve_model(model)
    if model.startswith("claude"):
        return AnthropicProvider(model)
    if model.startswith(("gpt-", "gpt4")):
        return OpenAIProvider(model)
    if model in GROQ_MODELS or model.startswith(("llama", "mixtral", "gemma")):
        return GroqProvider(model)
    raise ValueError(
        f"Unknown model: {model!r}. "
        f"Supported: 'claude-*', 'gpt-*', 'llama-*', 'mixtral-*' (Groq). "
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
        budget: float | None = None,
    ) -> str:
        """Run the agentic loop. Returns final answer string."""

    def _filter_tools(self, allowed: list[str] | None) -> list[dict]:
        if not allowed:
            return TOOL_DEFINITIONS
        return [t for t in TOOL_DEFINITIONS if t["name"] in allowed]

    def _check_budget(self, spent: float, budget: float | None) -> None:
        if budget is not None and spent > budget:
            raise BudgetExceededError(spent=spent, budget=budget)


# ── Anthropic provider ────────────────────────────────────────────────────────

class AnthropicProvider(BaseProvider):
    def __init__(self, model: str):
        super().__init__(model)
        import anthropic
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )

    def run(self, task_description, dataframe, max_steps, allowed_tools, tracer,
            budget=None):
        import anthropic
        tools = self._filter_tools(allowed_tools)
        messages: list[dict] = [{"role": "user", "content": task_description}]
        total_in, total_out = 0, 0

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
            total_in += input_tokens
            total_out += output_tokens
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

            self._check_budget(compute_cost(self.model, total_in, total_out), budget)

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

    def run(self, task_description, dataframe, max_steps, allowed_tools, tracer,
            budget=None):
        tools = self._filter_tools(allowed_tools)
        oai_tools = self._tools_to_openai(tools)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task_description},
        ]

        assistant_text = ""
        total_in, total_out = 0, 0

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

            in_tok = usage.prompt_tokens if usage else 0
            out_tok = usage.completion_tokens if usage else 0
            total_in += in_tok
            total_out += out_tok

            tracer.record(
                role="assistant",
                content=assistant_text,
                input_tokens=in_tok,
                output_tokens=out_tok,
            )

            self._check_budget(compute_cost(self.model, total_in, total_out), budget)

            if choice.finish_reason == "stop" or not tool_calls:
                return assistant_text

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


# ── Groq provider (OpenAI-compatible endpoint) ────────────────────────────────

class GroqProvider(OpenAIProvider):
    """
    Groq runs Llama and Mixtral models via an OpenAI-compatible API.
    Get a free API key at https://console.groq.com — no credit card needed.
    Set GROQ_API_KEY in your .env file.

    Fast free-tier models to try:
      dab run eda_001 --model groq          # llama-3.3-70b-versatile
      dab run eda_001 --model llama-8b      # llama-3.1-8b-instant (fastest)
      dab run eda_001 --model mixtral       # mixtral-8x7b-32768
    """

    def __init__(self, model: str):
        # Skip OpenAIProvider.__init__ — build our own client with Groq base URL
        BaseProvider.__init__(self, model)
        from openai import OpenAI
        groq_key = os.environ.get("GROQ_API_KEY")
        if not groq_key:
            raise EnvironmentError(
                "GROQ_API_KEY is not set. "
                "Get a free key at https://console.groq.com and add it to your .env file."
            )
        self.client = OpenAI(
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1",
        )
