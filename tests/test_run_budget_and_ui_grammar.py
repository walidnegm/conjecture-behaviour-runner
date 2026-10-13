"""Run budget (circuit breaker) and the UI step grammar — portable."""
from __future__ import annotations

import os

import pytest

from conjecture_behaviour_runner.budget import BudgetExceeded, RunBudget, parse_budget_invariant
from conjecture_behaviour_runner.ui_grammar import expand, parse_check, parse_locator


def test_default_budget_is_zero_and_stops_a_spending_run():
    b = RunBudget(model_calls=lambda: 3)
    with pytest.raises(BudgetExceeded, match="3 > 0"):
        b.check("s2")


def test_an_unmeasurable_budget_refuses_to_run_blind():
    with pytest.raises(BudgetExceeded, match="unmeasurable"):
        RunBudget(model_calls=None).check()


def test_time_budget():
    with pytest.raises(BudgetExceeded, match="time budget"):
        RunBudget(model_calls=lambda: 0, max_seconds=-1).check()


def test_a_raised_cap_lets_a_behaviour_run_spend():
    b = RunBudget(model_calls=lambda: 4, max_model_calls=5)
    b.check()
    assert b.within(5) and not b.within(3)


def test_no_cap_is_explicit():
    RunBudget(model_calls=None, max_model_calls=None, max_seconds=None).check()


def test_budget_invariant():
    assert parse_budget_invariant("model_calls_at_most:0") == 0
    assert parse_budget_invariant("llm_calls_at_most:7") == 7
    assert parse_budget_invariant("visible:testid:x") is None


def test_locators_and_checks():
    assert parse_locator("testid:drawer#1") == ("testid", "drawer", 1)
    assert parse_locator("role:button=Save") == ("role", "button=Save", 0)
    assert parse_check("count:testid:tab=0") == ("count", "testid:tab", "0")
    assert parse_check("text:testid:note~Saved") == ("text", "testid:note", "Saved")
    with pytest.raises(ValueError):
        parse_locator("css:.x")
    with pytest.raises(ValueError):
        parse_check("eventually:x")


def test_env_expansion():
    os.environ["CBR_PROBE"] = "wf_1"
    assert expand("/items/${CBR_PROBE}") == "/items/wf_1"
    assert expand(["${CBR_UNSET_PROBE}"]) == ["${CBR_UNSET_PROBE}"]
