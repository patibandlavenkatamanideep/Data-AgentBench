from .correctness import CorrectnessScorer
from .code_quality import CodeQualityScorer
from .efficiency import EfficiencyScorer
from .stat_validity import StatValidityScorer
from .composite import CompositeScorer, ScoreCard

# LLMJudgeScorer requires the `anthropic` package; import it lazily so that the
# rest of the scoring package can be used without an active Anthropic API connection.
def __getattr__(name: str):
    if name in ("LLMJudgeScorer", "LLMJudgeResult"):
        from .llm_judge import LLMJudgeScorer, LLMJudgeResult
        globals()["LLMJudgeScorer"] = LLMJudgeScorer
        globals()["LLMJudgeResult"] = LLMJudgeResult
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
