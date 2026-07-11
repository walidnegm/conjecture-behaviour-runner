"""Path-faithful mini-app — signature claim must stay green in CI."""
from __future__ import annotations

from conjecture_behaviour_runner.path_faithful import (
    MiniAppAdapter,
    MiniChatApp,
    prove_planted_bugs,
    run_path_faithful_demo,
    sole_continue_script,
)
from conjecture_behaviour_runner import LlmMode, run_script


def test_prove_planted_bugs_helpful() -> None:
    report = prove_planted_bugs()
    assert report["clean_passes"] is True
    assert report["owner_steal_caught"] is True
    assert report["drop_pin_caught"] is True
    assert report["illegal_restart_caught"] is True
    assert report.get("helpful") is True


def test_healthy_demo_passes() -> None:
    out = run_path_faithful_demo(bug=None)
    assert out["passed"] is True
    assert out["failures"] == []
    assert len(out.get("turns") or []) == 2


def test_owner_steal_fails() -> None:
    out = run_path_faithful_demo(bug="owner_steal")
    assert out["passed"] is False
    assert any("exclusive_owner" in f for f in out["failures"])


def test_no_keyword_cost_fallback() -> None:
    """Without new_task pin, free-text 'cost …' must not open cost_out."""
    app = MiniChatApp()
    # pin continue only — no NL short-circuit
    from conjecture_behaviour_runner.pins import CognitionPin

    obs = app.handle(
        "please cost out my workflow",
        pin=CognitionPin(task_intent="continue"),
    )
    assert obs.exclusive_owner == "front_door"
    assert obs.active_kind is None


def test_run_script_path_faithful_adapter() -> None:
    result = run_script(
        sole_continue_script(),
        adapter=MiniAppAdapter(MiniChatApp()),
        llm_mode=LlmMode.STUB,
    )
    assert result.passed, result.failures
