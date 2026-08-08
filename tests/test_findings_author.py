"""Findings author — LLM proposes · code validates structured CAQ reports."""
from __future__ import annotations

import json

from conjecture_behaviour_runner.findings_author import (
    attach_findings_to_evidence,
    author_findings,
    build_deterministic_findings,
    validate_findings_payload,
)


def _scenario() -> dict:
    return {
        "scenario_id": "residual_drafting_open_improve_not_ir",
        "incident_id": "conv_1732aa88",
        "failure_mode": "draft_improve_to_ir",
        "scenario_purpose": "Open strengthen must stay on drafting refine",
        "expected_invariant": {
            "prose": "exclusive owner remains drafting",
            "machine": ["exclusive_owner≈draft", "active_kind≠workflow_build"],
        },
        "mode_detection": ["workflow_builder IR handoff"],
        "incident_turns": [
            {"index": 0, "role": "user", "what_happened": "long process"},
            {"index": 1, "role": "assistant", "what_happened": "prose draft"},
            {"index": 2, "role": "user", "what_happened": "strengthen + agentic"},
            {
                "index": 3,
                "role": "assistant",
                "what_happened": "IR handoff — FAIL",
            },
        ],
        "code_path": "referential → interpret → IR",
        "root_cause": "open NL improve classified as interpret",
    }


def _evidence_fail() -> dict:
    return {
        "scenario_id": "residual_drafting_open_improve_not_ir",
        "what_actually_happened": {
            "incident_id": "conv_1732aa88",
            "turns": _scenario()["incident_turns"],
            "code_path": "referential → interpret",
            "root_cause": "skip_llm deictic miss",
        },
        "run": {
            "passed": False,
            "failures": ["exclusive_owner expected drafting got workflow_builder"],
            "adapter": "Bot0HttpAdapter",
            "turns": [],
        },
    }


def test_deterministic_fail_fills_tables() -> None:
    rep = build_deterministic_findings(
        scenario=_scenario(),
        evidence=_evidence_fail(),
    )
    assert rep.verdict == "FAIL"
    assert rep.what_actually_happened
    assert rep.what_should_have_happened
    assert "workflow" in rep.what_went_wrong.lower() or rep.what_went_wrong
    assert rep.failure_mode_slug == "draft_improve_to_ir"
    assert rep.seal_recommendation


def test_validate_coerces_pass_when_run_passed() -> None:
    ev = {
        "scenario_id": "x",
        "what_actually_happened": {"turns": []},
        "run": {"passed": True, "failures": []},
    }
    rep = validate_findings_payload(
        {
            "headline": "ok",
            "verdict": "INCONCLUSIVE",
            "what_should_have_happened": [],
            "what_actually_happened": [],
            "expected_vs_observed": [],
            "what_went_wrong": "",
            "confidence": 0.9,
        },
        scenario={"scenario_id": "x", "expected_invariant": {"machine": ["a"]}},
        evidence=ev,
    )
    assert rep.verdict == "PASS"
    assert rep.source == "hybrid"


def test_author_with_injected_llm() -> None:
    fake = {
        "headline": "Open improve stole to IR",
        "verdict": "FAIL",
        "what_should_have_happened": [
            {"index": 0, "role": "system", "what_happened": "stay on drafting"},
        ],
        "what_actually_happened": [
            {"index": 0, "role": "assistant", "what_happened": "IR handoff"},
        ],
        "expected_vs_observed": [
            {
                "aspect": "exclusive_owner",
                "expected": "draft",
                "observed": "workflow_builder",
                "match": False,
            },
        ],
        "what_went_wrong": "Improve leaf skipped; structure won",
        "root_cause_hypothesis": "referential interpret without finite grammar",
        "code_path_hypothesis": "resolve_referential_binding → IR",
        "failure_mode_slug": "draft_improve_to_ir",
        "seal_recommendation": "finite-interpret-only IR + ratchet",
        "confidence": 0.88,
    }

    def complete(_prompt: str) -> str:
        return json.dumps(fake)

    rep = author_findings(
        scenario=_scenario(),
        evidence=_evidence_fail(),
        llm_complete=complete,
        use_llm=True,
    )
    assert rep.source == "llm"
    assert rep.verdict == "FAIL"
    assert rep.headline.startswith("Open improve")
    assert any(not r["match"] for r in rep.expected_vs_observed)


def test_attach_findings_to_evidence() -> None:
    ev = _evidence_fail()
    out = attach_findings_to_evidence(
        ev,
        scenario=_scenario(),
        use_llm=False,
    )
    assert "findings" in out
    assert out["findings"]["verdict"] == "FAIL"
