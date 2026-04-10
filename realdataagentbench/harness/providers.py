"""Model providers — unified interface for Claude, GPT-4o, Groq, Grok, Gemini, and future models."""

from __future__ import annotations

import json
import os
import time
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from .pricing import COST_PER_M_TOKENS, compute_cost  # single source of truth
from .tools import TOOL_DEFINITIONS, get_column_stats, get_dataframe_info, run_code


def _json_safe(obj: Any) -> str:
    """Fallback for json.dumps — converts un-serializable types to strings."""
    import numpy as np
    import pandas as pd
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)

# ── Model name aliases ────────────────────────────────────────────────────────

ANTHROPIC_MODELS = {
    "claude-sonnet-4-6",
    "claude-opus-4-6",
    "claude-haiku-4-5-20251001",
    # short aliases
    "claude", "sonnet", "opus", "haiku",
}

OPENAI_MODELS = {
    "gpt-5",
    "gpt-5-mini",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
    # short aliases
    "gpt4o", "gpt4.1", "gpt5", "gpt-4o-2024-11-20",
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

GROK_MODELS = {
    "grok-3",
    "grok-3-mini",
    "grok-3-fast",
    "grok-2-1212",
    # short aliases
    "grok", "grok-mini", "grok-fast",
}

GEMINI_MODELS = {
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    # short aliases
    "gemini", "gemini-pro", "gemini-flash",
}

MODEL_ALIASES = {
    "claude": "claude-sonnet-4-6",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-6",
    "haiku": "claude-haiku-4-5-20251001",
    # OpenAI shortcuts
    "gpt4o": "gpt-4o",
    "gpt5": "gpt-5",
    "gpt4.1": "gpt-4.1",
    # Groq shortcuts
    "groq": "llama-3.3-70b-versatile",
    "llama": "llama-3.3-70b-versatile",
    "llama-70b": "llama-3.3-70b-versatile",
    "llama-8b": "llama-3.1-8b-instant",
    "mixtral": "mixtral-8x7b-32768",
    # Grok shortcuts
    "grok": "grok-3",
    "grok-mini": "grok-3-mini",
    "grok-fast": "grok-3-fast",
    # Gemini shortcuts
    "gemini": "gemini-2.5-flash",
    "gemini-pro": "gemini-2.5-pro",
    "gemini-flash": "gemini-2.5-flash",
}

# COST_PER_M_TOKENS and compute_cost are imported from pricing.py above.


SYSTEM_PROMPT = """You are an expert data scientist working on a benchmark task.
You have access to a pandas DataFrame called `df` loaded with the task dataset.

The run_code tool executes Python in a sandboxed namespace. The following are
pre-imported and ready to use WITHOUT any import statements:
  - np        (numpy)
  - pd        (pandas) — `df` is already loaded
  - stats     (scipy.stats)
  - sklearn   (scikit-learn, including sklearn.linear_model, sklearn.ensemble,
               sklearn.preprocessing, sklearn.metrics, sklearn.model_selection)

Do NOT write import statements inside run_code — they will raise an error.
Use np, pd, stats, sklearn directly.

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
    if model in GROQ_MODELS or model.startswith(("llama", "mixtral", "gemma2")):
        return GroqProvider(model)
    if model in GROK_MODELS or model.startswith("grok"):
        return GrokProvider(model)
    if model in GEMINI_MODELS or model.startswith("gemini"):
        return GeminiProvider(model)
    raise ValueError(
        f"Unknown model: {model!r}. "
        f"Supported prefixes: 'claude-*', 'gpt-*', 'llama-*'/'mixtral-*' (Groq), "
        f"'grok-*' (xAI), 'gemini-*' (Google). "
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
                result_str = json.dumps(result, default=_json_safe) if isinstance(result, dict) else str(result)
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

    def _chat_with_retry(self, **kwargs) -> Any:
        """Call chat.completions.create with exponential backoff on 429 / 503 / connection errors."""
        from openai import APIConnectionError, APIStatusError, RateLimitError
        delay = 5.0
        for attempt in range(5):
            try:
                return self.client.chat.completions.create(**kwargs)
            except RateLimitError:
                if attempt == 4:
                    raise
                time.sleep(delay)
                delay *= 2
            except APIConnectionError:
                # Transient network error — retry with backoff
                if attempt == 4:
                    raise
                time.sleep(delay)
                delay *= 2
            except APIStatusError as e:
                # 503 = server overloaded (transient); retry with backoff
                if e.status_code == 503 and attempt < 4:
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise

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
            response = self._chat_with_retry(
                model=self.model,
                messages=messages,
                tools=oai_tools,
                tool_choice="auto",
                max_completion_tokens=4096,
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
                result_str = json.dumps(result, default=_json_safe) if isinstance(result, dict) else str(result)

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

    # Llama models on Groq sometimes emit malformed tool-call XML instead of
    # proper JSON function calls.  A more explicit system prompt helps significantly.
    _GROQ_SYSTEM_PROMPT = (
        SYSTEM_PROMPT
        + "\n\nIMPORTANT: When calling a tool you MUST use the JSON function-call "
        "format provided by the API. Do NOT write <function=...> tags or any other "
        "format — only use the structured tool_calls mechanism."
    )

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

    def run(self, task_description, dataframe, max_steps, allowed_tools, tracer,
            budget=None):
        tools = self._filter_tools(allowed_tools)
        oai_tools = self._tools_to_openai(tools)

        messages = [
            {"role": "system", "content": self._GROQ_SYSTEM_PROMPT},
            {"role": "user", "content": task_description},
        ]

        assistant_text = ""
        total_in, total_out = 0, 0

        for _ in range(max_steps):
            response = self._chat_with_retry(
                model=self.model,
                messages=messages,
                tools=oai_tools,
                tool_choice="auto",
                max_completion_tokens=4096,
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
                result_str = json.dumps(result, default=_json_safe) if isinstance(result, dict) else str(result)

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


# ── xAI Grok provider (OpenAI-compatible endpoint) ───────────────────────────

class GrokProvider(OpenAIProvider):
    """
    xAI's Grok models via an OpenAI-compatible API.
    Get an API key at https://console.x.ai — set XAI_API_KEY in your .env file.

    Models to try:
      dab run eda_001 --model grok           # grok-3 (flagship)
      dab run eda_001 --model grok-mini      # grok-3-mini (cheap, fast)
      dab run eda_001 --model grok-2-1212    # grok-2 (previous gen)
    """

    def __init__(self, model: str):
        BaseProvider.__init__(self, model)
        from openai import OpenAI
        xai_key = os.environ.get("XAI_API_KEY")
        if not xai_key:
            raise EnvironmentError(
                "XAI_API_KEY is not set. "
                "Get a key at https://console.x.ai and add it to your .env file."
            )
        self.client = OpenAI(
            api_key=xai_key,
            base_url="https://api.x.ai/v1",
        )


# ── Google Gemini provider (OpenAI-compatible endpoint) ──────────────────────

class GeminiProvider(OpenAIProvider):
    """
    Google Gemini models via the OpenAI-compatible REST endpoint.
    Get a free API key at https://aistudio.google.com — set GEMINI_API_KEY in your .env file.

    Models to try:
      dab run eda_001 --model gemini              # gemini-2.5-flash (fast + cheap)
      dab run eda_001 --model gemini-pro          # gemini-2.5-pro (highest quality)
      dab run eda_001 --model gemini-2.0-flash    # gemini-2.0-flash (previous gen)
    """

    def __init__(self, model: str):
        BaseProvider.__init__(self, model)
        from openai import OpenAI
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            raise EnvironmentError(
                "GEMINI_API_KEY is not set. "
                "Get a free key at https://aistudio.google.com and add it to your .env file."
            )
        self.client = OpenAI(
            api_key=gemini_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

