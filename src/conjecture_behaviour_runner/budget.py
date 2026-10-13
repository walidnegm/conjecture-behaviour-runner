"""Run budget — a circuit breaker for runs that may cross a model.

A behaviour run that drives a real host can spend real tokens: a recursive
loop, an agent that keeps re-asking itself, or a step that silently starts
calling a model turns a check into a bill. A **run budget** caps that.

* The host injects a ``model_calls`` counter (how many model calls it has
  recorded since the run began — from a usage log, a gateway, a proxy).
* ``RunBudget.check(step_id)`` runs **before every step**: over the call cap or
  the time cap, it raises ``BudgetExceeded`` with the reason, so the run stops
  instead of spending on.
* An unmeasurable budget (counter returns ``None``) refuses to run blind.
* The default cap is **0**: a deterministic check spends nothing, and a
  non-zero count is itself a finding. A behaviour run raises the cap on purpose.

Per-step, the same budget can be asserted as an invariant string,
``model_calls_at_most:N`` (see ``parse_budget_invariant``).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

__all__ = ["BudgetExceeded", "RunBudget", "parse_budget_invariant"]


class BudgetExceeded(RuntimeError):
    """The run went over its model-call or time budget, or could not measure it."""


@dataclass
class RunBudget:
    model_calls: Optional[Callable[[], Optional[int]]] = None
    max_model_calls: Optional[int] = 0
    max_seconds: Optional[float] = 300.0
    _t0: float = field(default_factory=time.monotonic, init=False, repr=False)

    def used(self) -> Optional[int]:
        return None if self.model_calls is None else self.model_calls()

    def check(self, step_id: str = "") -> None:
        """Raise ``BudgetExceeded`` if this run may not take another step."""
        where = f" before step {step_id}" if step_id else ""
        if self.max_seconds is not None and time.monotonic() - self._t0 > self.max_seconds:
            raise BudgetExceeded(f"time budget exceeded ({self.max_seconds:.0f}s){where}")
        if self.max_model_calls is None:
            return
        used = self.used()
        if used is None:
            raise BudgetExceeded("model-call budget set but unmeasurable — refusing to run blind")
        if used > self.max_model_calls:
            raise BudgetExceeded(f"model-call budget exceeded: {used} > {self.max_model_calls}{where}")

    def within(self, cap: int) -> bool:
        """For a per-step invariant: True only when measured and within ``cap``."""
        used = self.used()
        return used is not None and used <= cap


def parse_budget_invariant(spec: str) -> Optional[int]:
    """``model_calls_at_most:N`` → N; anything else → None."""
    kind, _, arg = str(spec).partition(":")
    if kind.strip() not in ("model_calls_at_most", "llm_calls_at_most"):
        return None
    return int(arg.strip())
