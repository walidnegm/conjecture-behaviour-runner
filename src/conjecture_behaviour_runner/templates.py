"""Parameterized Conjecture script templates (portable state-law shapes).

Laws are agent-agnostic; product goldens are host-specific *instances*.
These builders fill host vocabulary (kind, exclusive_owner, pin keys) into
shared multi-turn stories so adopters do not copy another product's scripts.

See ``templates/README.md`` in the package root for narrative docs.

For CI without a product sole-continue registry, use
:class:`TemplateStreamAdapter` (generic owner = active_task.kind on continue).
CCP-backed hosts may instead use ``contrib.control_plane.ControlPlaneStreamAdapter``
with a kind already registered as sole-continue and a pin key the contract knows
(e.g. ``workflow_id``).
"""
from __future__ import annotations

from typing import Any, Optional

from conjecture_behaviour_runner.invariants import BaseControlPlaneAdapter
from conjecture_behaviour_runner.pins import CognitionPin
from conjecture_behaviour_runner.protocol import TurnObservation
from conjecture_behaviour_runner.script import (
    ConjectureScript,
    DialogueTurn,
    InvariantSpec,
    LedgerEffect,
    ScriptScope,
)

FRONT_DOOR_OWNER = "front_door"


class TemplateStreamAdapter(BaseControlPlaneAdapter):
    """Host-agnostic adapter for template scripts.

    * ``begin_task`` / ``set_phase`` / ``set_pin`` / ``clear_task`` mutate an
      in-memory projection shaped like CCP (``active_task`` + payload pins).
    * On ``task_intent=continue`` with an active kind → exclusive_owner = kind.
    * On detour / new_task / abandon / handoff → exclusive_owner = front_door.

    Does **not** require a closed sole-continue registry — any kind string works.
    """

    def apply_effect(
        self, context: dict[str, Any], effect: LedgerEffect
    ) -> dict[str, Any]:
        ctx = dict(context)
        op = effect.op
        payload = dict(effect.payload or {})

        if op in ("begin_task", "ensure_task"):
            pins = dict(payload.get("pins") or payload.get("payload") or {})
            # Allow top-level pin fields for convenience.
            for k, v in payload.items():
                if k in ("agent", "kind", "phase", "pins", "payload"):
                    continue
                if v is not None and v != "":
                    pins.setdefault(k, v)
            ctx["active_task"] = {
                "agent": payload.get("agent", ""),
                "kind": payload.get("kind", ""),
                "phase": payload.get("phase", ""),
                "payload": pins,
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
        else:
            raise ValueError(
                f"TemplateStreamAdapter: unknown effect op {op!r} "
                "(known: begin_task, set_phase, set_pin, clear_task)"
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
        elif isinstance(pin, dict):
            task_intent = str(pin.get("task_intent") or "continue").strip() or "continue"

        task = context.get("active_task") if isinstance(context.get("active_task"), dict) else {}
        kind = str(task.get("kind") or "").strip() or None
        pins = {}
        payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}
        for k, v in payload.items():
            if v is not None and v != "":
                pins[str(k)] = v

        supersede = task_intent in (
            "detour", "new_task", "abandon", "handoff", "reset",
        )
        if kind and not supersede:
            exclusive_owner = kind
            outcome = "continue_owned"
        else:
            exclusive_owner = FRONT_DOOR_OWNER
            outcome = "detour_superseded" if kind else "front_door"

        return TurnObservation(
            exclusive_owner=exclusive_owner,
            active_kind=kind,
            pins=pins,
            context=dict(context),
            observed_outcome=outcome,
            extras={
                "task_intent": task_intent,
                "front_door_blocked": bool(kind) and not supersede,
            },
        )


def sole_continue_script(
    *,
    kind: str,
    exclusive_owner: str,
    pin_key: str = "record_id",
    pin_value: str = "rec_demo_1",
    agent: str = "",
    open_phase: str = "open",
    pinned_phase: str = "anchored",
    script_id: Optional[str] = None,
    description: Optional[str] = None,
) -> ConjectureScript:
    """Open → pin → bare continue → steal-shaped continue → detour supersede.

    After open/pin, continue turns must keep ``exclusive_owner`` equal to
    ``kind`` (or the host's owner string). Detour releases ownership to the
    front door in CCP-shaped hosts (adapter-specific observe).

    Parameters are host vocabulary — use any ledger kind/owner/pin strings.
    """
    kind = (kind or "").strip()
    owner = (exclusive_owner or kind).strip()
    if not kind or not owner:
        raise ValueError("kind and exclusive_owner are required")
    agent_id = (agent or owner).strip()
    pin_key = (pin_key or "record_id").strip()
    pin_value = (pin_value or "rec_demo_1").strip()
    sid = (script_id or f"template_sole_continue_{kind}").strip()

    def _begin(phase: str) -> LedgerEffect:
        return LedgerEffect(
            op="begin_task",
            payload={
                "agent": agent_id,
                "kind": kind,
                "phase": phase,
                "pins": {pin_key: pin_value},
            },
        )

    turns = (
        DialogueTurn(
            user_text=f"start {kind} on {pin_value}",
            # begin_task effect opens the stream; observe with continue so the
            # new kind owns the turn (new_task would supersede to front_door).
            pin=CognitionPin(
                task_intent="continue",
                reason=f"open sole-continue stream {kind}",
            ),
            effects=(_begin(open_phase),),
            invariants=(
                InvariantSpec(kind="exclusive_owner", expected=owner),
                InvariantSpec(kind="kind_equals", expected=kind),
            ),
        ),
        DialogueTurn(
            user_text=f"use record {pin_value}",
            pin=CognitionPin(
                task_intent="continue",
                reason="pin lands under stream",
            ),
            effects=(
                LedgerEffect(
                    op="set_phase",
                    payload={"phase": pinned_phase},
                ),
                LedgerEffect(
                    op="set_pin",
                    payload={pin_key: pin_value},
                ),
            ),
            invariants=(
                InvariantSpec(kind="exclusive_owner", expected=owner),
                InvariantSpec(kind="pin_present", expected=pin_key),
                InvariantSpec(
                    kind="pin_equals",
                    expected={"key": pin_key, "value": pin_value},
                ),
            ),
        ),
        DialogueTurn(
            user_text="1",
            pin=CognitionPin(
                task_intent="continue",
                reason="bare ordinal continue under sole-continue",
            ),
            invariants=(
                InvariantSpec(kind="exclusive_owner", expected=owner),
                InvariantSpec(kind="pin_present", expected=pin_key),
            ),
        ),
        DialogueTurn(
            user_text="what is this product feature",
            pin=CognitionPin(
                task_intent="continue",
                reason="steal-shaped continue — owner must stick",
            ),
            invariants=(
                InvariantSpec(kind="exclusive_owner", expected=owner),
                InvariantSpec(kind="owner_not", expected="front_door"),
            ),
        ),
        DialogueTurn(
            user_text="actually show me the home dashboard instead",
            pin=CognitionPin(
                task_intent="detour",
                reason="explicit detour supersedes sole-continue",
            ),
            invariants=(
                # CCP-shaped observe: detour → front_door.
                InvariantSpec(
                    kind="exclusive_owner",
                    expected="front_door",
                    reason="detour yields to front door (CCP-shaped hosts)",
                ),
            ),
        ),
    )

    return ConjectureScript(
        script_id=sid,
        description=description
        or (
            f"Template sole-continue: kind={kind!r} owner={owner!r} "
            f"pin={pin_key}={pin_value!r}"
        ),
        conversation_id=f"conv_template_{kind}",
        turns=turns,
        scope=ScriptScope(
            in_scope=(
                f"sole-continue kind {kind}",
                "continue keeps exclusive owner and pin",
                "steal-shaped continue does not yield",
            ),
            out_of_scope=(
                "chat quality / prose",
                "classifier accuracy under live LLM",
            ),
            expected_refusal=(
                "illegal restart mid sole-continue without abandon",
            ),
        ),
    )


def reorient_keeps_owner_script(
    *,
    kind: str,
    exclusive_owner: str,
    pin_key: str = "record_id",
    pin_value: str = "rec_demo_1",
    agent: str = "",
    phase: str = "mid_flight",
    script_id: Optional[str] = None,
    description: Optional[str] = None,
) -> ConjectureScript:
    """Mid-flight → reorient CONTINUE effect → status-shaped continue.

    Proves the host must **not** clear the active task on idle reorient /
    Resume gate. Parameterize with any sole-continue kind.

    Effects use ``begin_task`` / ``set_phase`` (CONTINUE), never ``clear_task`` /
    ``complete_task``. A planted false complete would fail ``exclusive_owner``.
    """
    kind = (kind or "").strip()
    owner = (exclusive_owner or kind).strip()
    if not kind or not owner:
        raise ValueError("kind and exclusive_owner are required")
    agent_id = (agent or owner).strip()
    pin_key = (pin_key or "record_id").strip()
    pin_value = (pin_value or "rec_demo_1").strip()
    sid = (script_id or f"template_reorient_keeps_owner_{kind}").strip()

    begin = LedgerEffect(
        op="begin_task",
        payload={
            "agent": agent_id,
            "kind": kind,
            "phase": phase,
            "pins": {pin_key: pin_value},
        },
    )
    # CONTINUE after reorient gate — must not clear_task / complete_task.
    continue_effect = LedgerEffect(
        op="set_phase",
        payload={"phase": phase},
    )

    turns = (
        DialogueTurn(
            user_text=f"continue my {kind} work",
            pin=CognitionPin(
                task_intent="continue",
                reason="establish mid-flight sole-continue",
            ),
            effects=(begin,),
            invariants=(
                InvariantSpec(kind="exclusive_owner", expected=owner),
                InvariantSpec(kind="kind_equals", expected=kind),
                InvariantSpec(kind="pin_present", expected=pin_key),
            ),
        ),
        DialogueTurn(
            user_text="i am fine with this",
            pin=CognitionPin(
                task_intent="continue",
                reason="terse continue after idle — reorient gate is CONTINUE",
            ),
            effects=(continue_effect,),
            invariants=(
                InvariantSpec(
                    kind="exclusive_owner",
                    expected=owner,
                    reason="reorient must not COMPLETE the stream",
                ),
                InvariantSpec(kind="kind_equals", expected=kind),
                InvariantSpec(kind="pin_present", expected=pin_key),
            ),
        ),
        DialogueTurn(
            user_text="show me what we have so far",
            pin=CognitionPin(
                task_intent="continue",
                reason="status-shaped under still-active stream",
            ),
            effects=(continue_effect,),
            invariants=(
                InvariantSpec(kind="exclusive_owner", expected=owner),
                InvariantSpec(kind="owner_not", expected="front_door"),
                InvariantSpec(kind="pin_present", expected=pin_key),
            ),
        ),
        DialogueTurn(
            user_text="resume",
            pin=CognitionPin(
                task_intent="continue",
                reason="explicit resume under active stream",
            ),
            effects=(continue_effect,),
            invariants=(
                InvariantSpec(kind="exclusive_owner", expected=owner),
                InvariantSpec(kind="kind_equals", expected=kind),
            ),
        ),
    )

    return ConjectureScript(
        script_id=sid,
        description=description
        or (
            f"Template reorient-keeps-owner: kind={kind!r} owner={owner!r} "
            f"(CONTINUE not COMPLETE)"
        ),
        conversation_id=f"conv_template_reorient_{kind}",
        turns=turns,
        scope=ScriptScope(
            in_scope=(
                f"idle reorient CONTINUE for kind {kind}",
                "status-shaped continue keeps exclusive owner",
            ),
            out_of_scope=(
                "UI chrome for reorient cards",
                "live idle timers",
            ),
            expected_refusal=(
                "task_completed / clear_task solely because a reorient card was shown",
            ),
        ),
    )


def demo_scripts() -> list[ConjectureScript]:
    """Two synthetic-kind instances of the public templates (not product goldens).

    Run with :class:`TemplateStreamAdapter` (any kind string). For CCP registry
    kinds, swap ``kind`` / ``pin_key`` to host vocabulary and use
    ``ControlPlaneStreamAdapter``.
    """
    return [
        sole_continue_script(
            kind="demo_task",
            exclusive_owner="demo_task",
            pin_key="record_id",
            pin_value="rec_001",
            script_id="template_demo_sole_continue",
        ),
        reorient_keeps_owner_script(
            kind="demo_task",
            exclusive_owner="demo_task",
            pin_key="record_id",
            pin_value="rec_001",
            phase="awaiting_confirm",
            script_id="template_demo_reorient_keeps_owner",
        ),
    ]


__all__ = [
    "FRONT_DOOR_OWNER",
    "TemplateStreamAdapter",
    "demo_scripts",
    "reorient_keeps_owner_script",
    "sole_continue_script",
]
