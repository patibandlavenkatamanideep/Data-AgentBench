"""Sandboxed tools available to the agent during benchmark execution."""

from __future__ import annotations

import io
import textwrap
import traceback
from contextlib import redirect_stdout

import pandas as pd


def run_code(code: str, dataframe: pd.DataFrame) -> dict:
    """Execute Python code in a restricted namespace; return stdout + error."""
    namespace = {
        "df": dataframe,
        "pd": pd,
        "__builtins__": {
            "print": print,
            "len": len,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "sorted": sorted,
            "isinstance": isinstance,
            "type": type,
            "repr": repr,
        },
    }
    # Safe imports allowed inside the code block
    _safe_import_whitelist = {
        "numpy", "np", "pandas", "pd", "scipy", "scipy.stats",
        "sklearn", "math", "statistics",
    }

    buf = io.StringIO()
    try:
        # Inject safe numpy/scipy
        import numpy as np
        import scipy.stats as stats
        namespace["np"] = np
        namespace["stats"] = stats

        with redirect_stdout(buf):
            exec(textwrap.dedent(code), namespace)  # noqa: S102
        return {"output": buf.getvalue(), "error": None}
    except Exception:
        return {"output": buf.getvalue(), "error": traceback.format_exc()}


def get_dataframe_info(dataframe: pd.DataFrame) -> dict:
    """Return shape, dtypes, missing counts, and head(3) as a dict."""
    return {
        "shape": list(dataframe.shape),
        "columns": list(dataframe.columns),
        "dtypes": {col: str(dtype) for col, dtype in dataframe.dtypes.items()},
        "missing_counts": dataframe.isnull().sum().to_dict(),
        "missing_rates": (dataframe.isnull().mean().round(4)).to_dict(),
        "head": dataframe.head(3).to_dict(orient="records"),
    }


def get_column_stats(column_name: str, dataframe: pd.DataFrame) -> dict:
    """Return descriptive statistics for a single column."""
    if column_name not in dataframe.columns:
        return {"error": f"Column {column_name!r} not found. Available: {list(dataframe.columns)}"}
    col = dataframe[column_name].dropna()
    if pd.api.types.is_numeric_dtype(col):
        import numpy as np
        from scipy.stats import skew, kurtosis
        return {
            "column": column_name,
            "dtype": str(dataframe[column_name].dtype),
            "count": int(col.count()),
            "missing": int(dataframe[column_name].isnull().sum()),
            "mean": float(col.mean()),
            "median": float(col.median()),
            "std": float(col.std()),
            "min": float(col.min()),
            "max": float(col.max()),
            "q1": float(col.quantile(0.25)),
            "q3": float(col.quantile(0.75)),
            "skewness": float(skew(col)),
            "kurtosis": float(kurtosis(col)),
        }
    else:
        return {
            "column": column_name,
            "dtype": str(dataframe[column_name].dtype),
            "count": int(col.count()),
            "missing": int(dataframe[column_name].isnull().sum()),
            "unique": int(col.nunique()),
            "top_values": col.value_counts().head(5).to_dict(),
        }


# Anthropic tool-use definitions
TOOL_DEFINITIONS = [
    {
        "name": "run_code",
        "description": (
            "Execute Python code against the task dataframe `df`. "
            "numpy (np), pandas (pd), and scipy.stats (stats) are pre-imported. "
            "Use print() to produce output. Returns stdout and any error."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Valid Python code. Use print() for output.",
                }
            },
            "required": ["code"],
        },
    },
    {
        "name": "get_dataframe_info",
        "description": "Return shape, dtypes, missing value counts and rates, and the first 3 rows.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_column_stats",
        "description": "Return descriptive statistics for a single column (mean, std, skewness, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "column_name": {
                    "type": "string",
                    "description": "Name of the column to analyse.",
                }
            },
            "required": ["column_name"],
        },
    },
]
