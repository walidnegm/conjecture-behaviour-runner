"""A ``ContentJudge`` backed by DeepEval metrics (optional extra: ``deepeval``).

    pip install "conjecture-behaviour-runner[deepeval]"

Metric names map to DeepEval's RAG metrics:

=====================  ============================================  ================
name                   asks                                          reads
=====================  ============================================  ================
faithfulness           does the answer claim only what the           answer, contexts
                       contexts support?
answer_relevancy       does the answer address the question?         question, answer
contextual_relevancy   do the retrieved contexts fit the question?   question, contexts
=====================  ============================================  ================

**Pass your own judge model.** DeepEval's default calls a hosted model directly
with an environment key, outside any gateway a host uses to log, rate-limit and
budget model calls. ``DeepEvalJudge(model=...)`` takes a ``DeepEvalBaseLLM`` (or
a model name DeepEval understands); hosts with a gateway wrap it in a
``DeepEvalBaseLLM`` subclass so the judge's calls are counted by the run budget
like every other call. ``model=None`` is refused unless ``allow_default_model``.

Telemetry is opted out before DeepEval is imported.
"""
from __future__ import annotations

import os
from typing import Any, Optional, Sequence

from conjecture_behaviour_runner.content import JudgeScore

__all__ = ["DEEPEVAL_METRICS", "DeepEvalJudge"]

DEEPEVAL_METRICS: tuple[str, ...] = ("faithfulness", "answer_relevancy", "contextual_relevancy")


def _import_deepeval() -> Any:
    os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")
    os.environ.setdefault("DEEPEVAL_DISABLE_DOTENV", "1")
    try:
        import deepeval.metrics as metrics
        from deepeval.test_case import LLMTestCase
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise ImportError(
            'DeepEvalJudge needs the optional extra: pip install "conjecture-behaviour-runner[deepeval]"'
        ) from exc
    return metrics, LLMTestCase


class DeepEvalJudge:
    """Score answers with DeepEval. One metric call per ``score``."""

    def __init__(self, model: Any = None, *, allow_default_model: bool = False) -> None:
        if model is None and not allow_default_model:
            raise ValueError(
                "DeepEvalJudge: pass model= (a DeepEvalBaseLLM routed through your gateway). "
                "Set allow_default_model=True to use DeepEval's default hosted model."
            )
        self.model = model
        self._metrics, self._case = _import_deepeval()

    def _metric(self, name: str) -> Any:
        cls = {
            "faithfulness": self._metrics.FaithfulnessMetric,
            "answer_relevancy": self._metrics.AnswerRelevancyMetric,
            "contextual_relevancy": self._metrics.ContextualRelevancyMetric,
        }.get(name)
        if cls is None:
            raise ValueError(f"unknown DeepEval metric {name!r}; known: {', '.join(DEEPEVAL_METRICS)}")
        # Synchronous and one at a time: a run budget counts calls before each step.
        return cls(model=self.model, include_reason=True, async_mode=False)

    def score(
        self,
        metric: str,
        *,
        question: str,
        answer: str,
        contexts: Sequence[str],
    ) -> JudgeScore:
        m = self._metric(metric)
        case = self._case(
            input=question,
            actual_output=answer,
            retrieval_context=list(contexts) or None,
        )
        m.measure(case)
        score: Optional[float] = getattr(m, "score", None)
        return JudgeScore(
            metric=metric,
            score=float(score) if score is not None else 0.0,
            reason=str(getattr(m, "reason", "") or ""),
        )
