"""Portable multi-turn run loop."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Union

from conjecture_behaviour_runner.cognition import (
    CognitionProvider,
    StubCognitionProvider,
    provider_for_mode,
)
from conjecture_behaviour_runner.modes import LlmMode
from conjecture_behaviour_runner.protocol import ControlPlaneAdapter, TurnObservation
from conjecture_behaviour_runner.script import (
    ConjectureScript,
    DialogueTurn,
    InvariantSpec,
    RunResult,
)
from conjecture_behaviour_runner.temporal import check_trajectory_invariant


def _resolve_pin_legacy(turn: DialogueTurn) -> Any:
    """Legacy path: pin already on turn (no CognitionProvider)."""
    from conjecture_behaviour_runner.pins import CognitionPin

    if turn.pin is None:
        return None
    if isinstance(turn.pin, CognitionPin):
        return turn.pin
    if isinstance(turn.pin, dict):
        return CognitionPin.from_dict(turn.pin)
    raise TypeError(f"unsupported pin type: {type(turn.pin)!r}")


def run_script(
    script: ConjectureScript,
    *,
    adapter: ControlPlaneAdapter,
    llm_mode: Union[LlmMode, str] = LlmMode.STUB,
    cognition: Optional[CognitionProvider] = None,
    freeze_dir: str | Path | None = None,
) -> RunResult:
    """Execute a Conjecture script against a control-plane adapter.

    Loop: resolve cognition → apply effects → observe → step oracles →
    trajectory oracles. Cognition is independent of the host adapter.
    """
    mode = llm_mode.value if isinstance(llm_mode, LlmMode) else str(llm_mode)

    if cognition is None:
        try:
            if mode in ("local", "cloud"):
                # Fall back to turn pins if present (host-supplied).
                if not any(t.pin for t in script.turns):
                    return RunResult(
                        script_id=script.script_id,
                        passed=False,
                        failures=[
                            f"llm_mode={mode} requires cognition=... provider "
                            "or host-supplied pins on every turn"
                        ],
                        llm_mode=mode,
                    )
                cognition = StubCognitionProvider()
            else:
                cognition = provider_for_mode(mode, freeze_dir=freeze_dir)
        except ValueError as exc:
            return RunResult(
                script_id=script.script_id,
                passed=False,
                failures=[str(exc)],
                llm_mode=mode,
            )

    context: dict[str, Any] = dict(script.initial_context or {})
    failures: list[str] = []
    turn_results: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []

    for i, turn in enumerate(script.turns):
        try:
            decision = cognition.resolve(
                turn,
                state=context,
                script_id=script.script_id,
                turn_index=i,
            )
            pin = decision.pin
        except Exception as exc:  # fail closed on cognition
            return RunResult(
                script_id=script.script_id,
                passed=False,
                failures=[f"turn[{i}] cognition: {exc}"],
                turn_results=turn_results,
                llm_mode=mode,
                artifact={"conversation_id": script.conversation_id},
            )

        for effect in turn.effects:
            context = adapter.apply_effect(context, effect)

        obs: TurnObservation = adapter.observe_turn(
            context=context,
            user_text=turn.user_text,
            pin=pin,
        )
        if obs.context is not None:
            context = dict(obs.context)

        turn_failures: list[str] = []
        held: list[str] = []
        violated: list[str] = []

        def _check(spec: InvariantSpec, label: str) -> None:
            msg = adapter.check_invariant(
                observation=obs, context=context, spec=spec
            )
            if msg:
                turn_failures.append(f"turn[{i}] {label}{spec.kind}: {msg}")
                violated.append(spec.kind)
            else:
                held.append(spec.kind)

        for inv in turn.invariants:
            _check(inv, "")

        # Outcome-specific invariant sets (branching contracts).
        if turn.outcome_invariants and obs.observed_outcome is not None:
            for inv in turn.outcome_invariants.get(obs.observed_outcome) or ():
                _check(inv, f"outcome[{obs.observed_outcome}].")

        if turn.allowed_outcomes:
            if obs.observed_outcome is None:
                turn_failures.append(
                    f"turn[{i}] allowed_outcomes declared "
                    f"{list(turn.allowed_outcomes)!r} but observed_outcome is None"
                )
            elif obs.observed_outcome not in turn.allowed_outcomes:
                turn_failures.append(
                    f"turn[{i}] outcome {obs.observed_outcome!r} not in "
                    f"allowed_outcomes={list(turn.allowed_outcomes)!r}"
                )

        obs_dict = {
            "exclusive_owner": obs.exclusive_owner,
            "active_kind": obs.active_kind,
            "pins": dict(obs.pins),
            "observed_outcome": obs.observed_outcome,
            "extras": dict(obs.extras or {}),
        }
        observations.append(obs_dict)

        turn_results.append(
            {
                "index": i,
                "actor": turn.actor,
                "user_text": turn.user_text,
                "cognition": decision.to_dict(),
                "observation": obs_dict,
                "invariants_held": held,
                "invariants_violated": violated,
                "failures": turn_failures,
            }
        )
        failures.extend(turn_failures)

    # Trajectory (cross-turn) oracle
    for inv in script.trajectory_invariants:
        msg = check_trajectory_invariant(observations, inv)
        if msg:
            failures.append(f"trajectory {inv.kind}: {msg}")

    artifact: dict[str, Any] = {
        "conversation_id": script.conversation_id,
        "description": script.description,
        "tags": list(script.tags),
        "final_context_keys": sorted(context.keys()),
        "observations": observations,
    }
    if script.scope is not None:
        artifact["scope"] = script.scope.to_dict()
    if freeze_dir is not None:
        artifact["freeze_dir"] = str(freeze_dir)

    return RunResult(
        script_id=script.script_id,
        passed=not failures,
        failures=failures,
        turn_results=turn_results,
        llm_mode=mode,
        artifact=artifact,
    )
