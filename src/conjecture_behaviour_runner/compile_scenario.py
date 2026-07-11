"""Compile Conjecture Scenario → Conjecture Script (ExecutionPlan thin form).

Experimental preconditions/postconditions remain **descriptions** unless the step
``payload`` carries executable ``invariants`` / ``pin`` / ``effects`` / ``user_text``.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from conjecture_behaviour_runner.script import (
    ConjectureScript,
    DialogueTurn,
    InvariantSpec,
    LedgerEffect,
    ScriptScope,
)


def _invariants_from_payload(payload: Optional[Mapping[str, Any]]) -> tuple[InvariantSpec, ...]:
    if not payload:
        return ()
    raw = payload.get("invariants") or []
    return tuple(InvariantSpec.from_dict(i) for i in raw)


def _effects_from_payload(payload: Optional[Mapping[str, Any]]) -> tuple[LedgerEffect, ...]:
    if not payload:
        return ()
    raw = payload.get("effects") or []
    return tuple(LedgerEffect.from_dict(e) for e in raw)


def compile_scenario_to_script(
    scenario: Any,
    *,
    profile_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> ConjectureScript:
    """Map a validated experimental ``Scenario`` into a runnable ``ConjectureScript``.

    Step payload keys (executable):
      user_text, pin, effects, invariants, allowed_outcomes, freeze_key,
      outcome_invariants
    Step fields used as metadata:
      actor, id → freeze_key default, postconditions → description notes only
    """
    from conjecture_behaviour_runner.experimental.scenario_models import Scenario

    if not isinstance(scenario, Scenario):
        # Allow duck-typed / already-validated objects
        pass

    sid = getattr(scenario, "scenario_id", None) or "compiled"
    scope_obj = getattr(scenario, "scope", None)
    scope = None
    if scope_obj is not None:
        scope = ScriptScope(
            in_scope=tuple(getattr(scope_obj, "in_scope", None) or ()),
            out_of_scope=tuple(getattr(scope_obj, "out_of_scope", None) or ()),
            expected_refusal=tuple(getattr(scope_obj, "expected_refusal", None) or ()),
        )

    turns: list[DialogueTurn] = []
    for step in getattr(scenario, "steps", ()) or ():
        payload = getattr(step, "payload", None) or {}
        if not isinstance(payload, Mapping):
            payload = {}
        actor = getattr(getattr(step, "actor", None), "value", None) or getattr(
            step, "actor", "user"
        )
        if hasattr(actor, "value"):
            actor = actor.value
        user_text = str(
            payload.get("user_text")
            or payload.get("message")
            or getattr(step, "maneuver", "")
            or getattr(step, "control_point", "")
            or ""
        )
        pin = payload.get("pin")
        allowed = tuple(payload.get("allowed_outcomes") or ())
        # nondeterminism.allowed_outcomes on step as fallback
        nd = getattr(step, "nondeterminism", None)
        if not allowed and nd is not None:
            allowed = tuple(getattr(nd, "allowed_outcomes", None) or ())
        freeze_key = str(
            payload.get("freeze_key") or getattr(step, "id", "") or ""
        )
        oi_raw = payload.get("outcome_invariants") or {}
        outcome_invariants = {}
        if isinstance(oi_raw, Mapping):
            for k, specs in oi_raw.items():
                outcome_invariants[str(k)] = tuple(
                    InvariantSpec.from_dict(s) for s in (specs or ())
                )

        turns.append(
            DialogueTurn(
                user_text=user_text,
                pin=pin,
                effects=_effects_from_payload(payload),
                invariants=_invariants_from_payload(payload),
                allowed_outcomes=allowed,
                outcome_invariants=outcome_invariants,
                freeze_key=freeze_key,
                actor=str(actor or "user"),
            )
        )

    if not turns:
        raise ValueError("scenario has no steps to compile")

    tags = ["compiled-from-scenario"]
    if profile_id:
        tags.append(f"profile:{profile_id}")
    sc = getattr(scenario, "scenario_class", None)
    if sc:
        tags.append(f"class:{sc}")

    traj_raw = ()
    # Optional trajectory_invariants on scenario as extra attr (not in strict schema)
    extra = getattr(scenario, "model_extra", None) or {}
    # Pydantic v2 extra forbid — allow via payload on first profile notes
    return ConjectureScript(
        script_id=str(sid),
        description=f"compiled from scenario {sid}",
        conversation_id=conversation_id or f"conv_{sid}",
        turns=tuple(turns),
        initial_context={},
        tags=tuple(tags),
        scope=scope,
        trajectory_invariants=traj_raw,
    )


def run_result_to_trajectory(
    result: Any,
    *,
    scenario_id: str,
    profile_id: str = "default",
    run_id: str = "",
) -> Any:
    """Bridge ``RunResult`` → experimental ``Trajectory`` for capture/diagnose."""
    from datetime import datetime, timezone

    from conjecture_behaviour_runner.experimental.trajectory import (
        StepResult,
        Trajectory,
    )

    now = datetime.now(timezone.utc)
    step_results: list[StepResult] = []
    for tr in getattr(result, "turn_results", None) or []:
        held = list(tr.get("invariants_held") or [])
        violated = list(tr.get("invariants_violated") or [])
        obs = tr.get("observation") or {}
        outcome = obs.get("observed_outcome") or "unspecified"
        step_results.append(
            StepResult(
                step_id=str(tr.get("index", len(step_results))),
                started_at=now,
                finished_at=now,
                latency_ms=0,
                settled_within_sla=True,
                observed_outcome=str(outcome),
                evidence_results=[],
                invariants_held=held,
                invariants_violated=violated,
                runner_notes={
                    "user_text": tr.get("user_text"),
                    "actor": tr.get("actor"),
                    "failures": tr.get("failures") or [],
                },
                passed=not (tr.get("failures") or []),
            )
        )

    passed = bool(getattr(result, "passed", False))
    return Trajectory(
        scenario_id=scenario_id,
        profile_id=profile_id,
        run_id=run_id or getattr(result, "script_id", "run"),
        started_at=now,
        finished_at=now,
        terminal_bucket="expected" if passed else "failure",
        overall_pass=passed,
        step_results=step_results,
        artifact_urls=[],
    )
