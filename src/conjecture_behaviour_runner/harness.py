"""Portable multi-turn run loop."""
from __future__ import annotations

from typing import Any, Optional

from conjecture_behaviour_runner.modes import LlmMode
from conjecture_behaviour_runner.pins import CognitionPin
from conjecture_behaviour_runner.protocol import ControlPlaneAdapter, TurnObservation
from conjecture_behaviour_runner.script import (
    ConjectureScript,
    DialogueTurn,
    RunResult,
)


def _resolve_pin(turn: DialogueTurn, llm_mode: LlmMode) -> Optional[CognitionPin]:
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
    llm_mode: LlmMode = LlmMode.STUB,
) -> RunResult:
    """Execute a Conjecture script against a control-plane adapter.

    Slice 0 portable loop: resolve pin → apply effects → observe → check
    invariants. Live cognition modes (local/cloud) require a host that
    supplies pins via ``turn.pin`` or a future recorder hook.
    """
    if llm_mode not in (LlmMode.STUB, LlmMode.FREEZE) and not any(
        t.pin for t in script.turns
    ):
        # Fail closed: portable core does not call host LLMs itself.
        return RunResult(
            script_id=script.script_id,
            passed=False,
            failures=[
                f"llm_mode={llm_mode.value} requires host-supplied pins "
                "(portable core is pin-driven; host drivers may resolve live cognition)"
            ],
            llm_mode=llm_mode.value,
        )

    context: dict[str, Any] = dict(script.initial_context or {})
    failures: list[str] = []
    turn_results: list[dict[str, Any]] = []

    for i, turn in enumerate(script.turns):
        pin = _resolve_pin(turn, llm_mode)
        for effect in turn.effects:
            context = adapter.apply_effect(context, effect)

        obs: TurnObservation = adapter.observe_turn(
            context=context,
            user_text=turn.user_text,
            pin=pin,
        )
        context = dict(obs.context or context)

        turn_failures: list[str] = []
        for inv in turn.invariants:
            msg = adapter.check_invariant(
                observation=obs, context=context, spec=inv
            )
            if msg:
                turn_failures.append(f"turn[{i}] {inv.kind}: {msg}")

        if turn.allowed_outcomes and obs.observed_outcome is not None:
            if obs.observed_outcome not in turn.allowed_outcomes:
                turn_failures.append(
                    f"turn[{i}] outcome {obs.observed_outcome!r} not in "
                    f"allowed_outcomes={list(turn.allowed_outcomes)!r}"
                )

        turn_results.append(
            {
                "index": i,
                "user_text": turn.user_text,
                "observation": {
                    "exclusive_owner": obs.exclusive_owner,
                    "active_kind": obs.active_kind,
                    "pins": dict(obs.pins),
                    "observed_outcome": obs.observed_outcome,
                },
                "failures": turn_failures,
            }
        )
        failures.extend(turn_failures)

    return RunResult(
        script_id=script.script_id,
        passed=not failures,
        failures=failures,
        turn_results=turn_results,
        llm_mode=llm_mode.value,
        artifact={
            "conversation_id": script.conversation_id,
            "description": script.description,
            "final_context_keys": sorted(context.keys()),
        },
    )
