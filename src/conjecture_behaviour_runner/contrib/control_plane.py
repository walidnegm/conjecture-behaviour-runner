"""Real ``ControlPlaneAdapter`` — bind Conjecture to the Conversation Control Plane.

This is the missing companion glue: it runs the **real** CCP multi-turn stream
contract (``conversation_control_plane.multi_turn_stream_contract``) over a context
projection to decide turn ownership. No database, CI-safe — it exercises the pure
contract functions (sole-continue stickiness, phase-gated entity resolve, pin
identity), **not** a fake ledger.

Requires the companion package::

    pip install conjecture-behaviour-runner[control-plane]
    # or have `conversation_control_plane` importable on the path

Ownership model (what ``observe_turn`` projects):

* An active **sole-continue** kind owns the turn while ``task_intent`` is
  ``continue`` → ``exclusive_owner == <kind>``.
* ``task_intent`` in {detour, new_task, abandon, handoff} lets the front door
  supersede → ``exclusive_owner == "front_door"``.
* After a pin lands in a continue phase, greenfield entity resolve is blocked
  (``extras["blocks_resolve"] is True``) and ``preferred_workflow_id`` comes from
  the ledger pin, not ambient ``last_read_*`` — the A14/A15 anti-pattern guard.
"""
from __future__ import annotations

from typing import Any

from conjecture_behaviour_runner.invariants import BaseControlPlaneAdapter
from conjecture_behaviour_runner.pins import CognitionPin
from conjecture_behaviour_runner.protocol import TurnObservation
from conjecture_behaviour_runner.script import (
    ConjectureScript,
    DialogueTurn,
    InvariantSpec,
    LedgerEffect,
)

try:
    from conversation_control_plane import multi_turn_stream_contract as _mtsc
except Exception as _exc:  # pragma: no cover - exercised only without the companion
    _mtsc = None
    _IMPORT_ERROR: Exception | None = _exc
else:
    _IMPORT_ERROR = None

#: Owner id used when a detour / new_task supersedes an active stream.
FRONT_DOOR_OWNER = "front_door"


def control_plane_available() -> bool:
    """True when the Conversation Control Plane package is importable."""
    return _mtsc is not None


class ControlPlaneStreamAdapter(BaseControlPlaneAdapter):
    """Bind Conjecture to the CCP multi-turn stream contract.

    ``apply_effect`` builds the ledger projection shape the contract reads
    (``active_task = {agent, kind, phase, payload: {pins}}``); ``observe_turn``
    runs the real ownership predicates. Invariant checking is inherited from
    :class:`BaseControlPlaneAdapter` (the standard library).
    """

    def __init__(self) -> None:
        if _mtsc is None:
            raise ImportError(
                "conversation_control_plane is not importable — install the "
                "companion package: pip install conjecture-behaviour-runner[control-plane]"
            ) from _IMPORT_ERROR

    def apply_effect(
        self, context: dict[str, Any], effect: LedgerEffect
    ) -> dict[str, Any]:
        ctx = dict(context)
        op = effect.op
        payload = dict(effect.payload or {})

        if op in ("begin_task", "ensure_task"):
            ctx["active_task"] = {
                "agent": payload.get("agent", ""),
                "kind": payload.get("kind", ""),
                "phase": payload.get("phase", ""),
                "payload": dict(payload.get("pins") or payload.get("payload") or {}),
            }
        elif op in ("set_phase", "update_phase"):
            task = dict(ctx.get("active_task") or {})
            task["phase"] = payload.get("phase", task.get("phase", ""))
            ctx["active_task"] = task
        elif op == "set_pin":
            task = dict(ctx.get("active_task") or {})
            pins = dict(task.get("payload") or {})
            pins.update(payload)
            task["payload"] = pins
            ctx["active_task"] = task
        elif op in ("clear_task", "complete_task", "abandon_task"):
            ctx.pop("active_task", None)
        elif op == "set_ambient":
            # e.g. {"last_read_workflow_id": "wf_2"} — the mirror that must NOT
            # override a ledger pin (A15).
            ctx.update(payload)
        else:
            raise ValueError(
                f"ControlPlaneStreamAdapter: unknown effect op {op!r} "
                "(known: begin_task, set_phase, set_pin, clear_task, set_ambient)"
            )
        return ctx

    def observe_turn(
        self,
        *,
        context: dict[str, Any],
        user_text: str,
        pin: Any,
    ) -> TurnObservation:
        task_intent = "continue"
        if isinstance(pin, CognitionPin):
            task_intent = (pin.task_intent or "continue").strip() or "continue"

        kind = _mtsc.stream_kind(context)
        phase = _mtsc.stream_phase(context)
        pins = _mtsc.ledger_entity_pins(context)
        supersede = _mtsc.task_intent_allows_supersede(task_intent)
        blocks_resolve = _mtsc.sole_continue_blocks_entity_resolve(
            context, task_intent=task_intent
        )

        if kind and not supersede:
            exclusive_owner = kind
            observed_outcome = "continue_owned"
        elif kind:
            exclusive_owner = FRONT_DOOR_OWNER
            observed_outcome = "detour_superseded"
        else:
            exclusive_owner = FRONT_DOOR_OWNER
            observed_outcome = "front_door"

        # CCP projects workflow identity; expose both the CCP name and a
        # generic preferred_entity_id so hosts without workflow vocabulary
        # can still assert pin-over-ambient identity.
        preferred_workflow_id = _mtsc.preferred_workflow_id_from_stream(
            context, allow_ambient_last_read=not blocks_resolve
        )

        return TurnObservation(
            exclusive_owner=exclusive_owner,
            active_kind=kind,
            pins=dict(pins),
            context=dict(context),
            observed_outcome=observed_outcome,
            extras={
                "phase": phase,
                "task_intent": task_intent,
                "blocks_resolve": blocks_resolve,
                "front_door_blocked": bool(kind) and not supersede,
                "preferred_workflow_id": preferred_workflow_id,
                "preferred_entity_id": preferred_workflow_id,
            },
        )


# ── Reusable golden scripts (generic control-plane contract, not host-private) ──


def control_plane_golden_scripts() -> list[ConjectureScript]:
    """Three portable goldens proving the sole-continue contract across turns.

    ``cost_out`` is the public-safe example kind declared in the CCP contract
    module itself — these are contract demonstrations, not host-app goldens.
    """
    begin_cost = LedgerEffect(
        op="begin_task",
        payload={
            "agent": "cost",
            "kind": "cost_out",
            "phase": "sizing",
            "pins": {"workflow_id": "wf_1"},
        },
    )

    from conjecture_behaviour_runner.script import ScriptScope

    sole_continue_scope = ScriptScope(
        in_scope=(
            "multi-turn sole-continue on a pinned entity",
            "stub/freeze cognition labels for task_intent",
            "authenticated host session with ledger projection",
        ),
        out_of_scope=(
            "free live model quality scoring",
            "UI click paths without a control-plane adapter",
        ),
        expected_refusal=(
            "re-start assessment mid sole-continue without explicit new_task",
            "entity re-resolve from ambient last_read while blocks_resolve",
        ),
    )

    g1 = ConjectureScript(
        script_id="sole_continue_owns_the_turn",
        description="a continue turn on a pinned cost_out stream stays owned; no re-resolve",
        conversation_id="conv_g1",
        scope=sole_continue_scope,
        turns=[
            DialogueTurn(
                user_text="cost out the onboarding workflow",
                pin=CognitionPin(task_intent="continue"),
                effects=[begin_cost],
                invariants=[InvariantSpec(kind="exclusive_owner", expected="cost_out")],
            ),
            DialogueTurn(
                user_text="make the volume 10k",
                pin=CognitionPin(task_intent="continue"),
                invariants=[
                    InvariantSpec(kind="exclusive_owner", expected="cost_out"),
                    InvariantSpec(kind="active_kind", expected="cost_out"),
                    InvariantSpec(kind="pin_present", expected="workflow_id"),
                    InvariantSpec(
                        kind="extra_true",
                        expected="blocks_resolve",
                        reason="pinned continue phase must not re-resolve (A14)",
                    ),
                ],
                allowed_outcomes=["continue_owned"],
            ),
        ],
        tags=["control-plane", "sole-continue"],
    )

    g2 = ConjectureScript(
        script_id="detour_supersedes_stream",
        description="a knowledge detour supersedes the active stream (front door owns)",
        conversation_id="conv_g2",
        turns=[
            DialogueTurn(
                user_text="cost out the onboarding workflow",
                pin=CognitionPin(task_intent="continue"),
                effects=[begin_cost],
                invariants=[InvariantSpec(kind="exclusive_owner", expected="cost_out")],
            ),
            DialogueTurn(
                user_text="wait — what is a scorecard?",
                pin=CognitionPin(task_intent="detour", discovery_kind="glossary"),
                invariants=[
                    InvariantSpec(kind="owner_not", expected="cost_out"),
                    InvariantSpec(kind="exclusive_owner", expected="front_door"),
                    InvariantSpec(
                        kind="extra_false",
                        expected="blocks_resolve",
                        reason="detour releases sole-continue; resolve is allowed again",
                    ),
                ],
                allowed_outcomes=["detour_superseded"],
            ),
        ],
        tags=["control-plane", "detour"],
    )

    g3 = ConjectureScript(
        script_id="pin_survives_ambient_last_read",
        description="after pin, ambient last_read_* must not hijack identity (A15)",
        conversation_id="conv_g3",
        turns=[
            DialogueTurn(
                user_text="cost out the onboarding workflow",
                pin=CognitionPin(task_intent="continue"),
                effects=[
                    begin_cost,
                    LedgerEffect(op="set_ambient", payload={"last_read_workflow_id": "wf_2"}),
                ],
                invariants=[InvariantSpec(kind="pin_present", expected="workflow_id")],
            ),
            DialogueTurn(
                user_text="the keynote workflow",
                pin=CognitionPin(task_intent="continue"),
                invariants=[
                    InvariantSpec(kind="pin_equals", expected={"key": "workflow_id", "value": "wf_1"}),
                    InvariantSpec(
                        kind="extra_equals",
                        expected={"key": "preferred_workflow_id", "value": "wf_1"},
                        reason="ledger pin wins over ambient last_read_workflow_id=wf_2",
                    ),
                    InvariantSpec(kind="extra_true", expected="blocks_resolve"),
                ],
                allowed_outcomes=["continue_owned"],
            ),
        ],
        tags=["control-plane", "pin-hijack"],
    )

    return [g1, g2, g3]


__all__ = [
    "FRONT_DOOR_OWNER",
    "ControlPlaneStreamAdapter",
    "control_plane_available",
    "control_plane_golden_scripts",
]
