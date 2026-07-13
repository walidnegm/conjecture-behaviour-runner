"""Minimal path-faithful vertical: real Act path through an in-process mini-app.

This is the credibility shape:
  Arrange (optional seed) → Act (app.handle message) → Observe → Assert

Planted bugs prove Conjecture catches owner steal, dropped pin, and illegal restart.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from conjecture_behaviour_runner.pins import CognitionPin
from conjecture_behaviour_runner.protocol import TurnObservation
from conjecture_behaviour_runner.script import (
    ConjectureScript,
    DialogueTurn,
    InvariantSpec,
    LedgerEffect,
    ScriptScope,
)


# ── System under test ──────────────────────────────────────────────────


@dataclass
class MiniLedger:
    exclusive_owner: Optional[str] = None
    active_kind: Optional[str] = None
    phase: str = ""
    pins: dict[str, Any] = field(default_factory=dict)
    completed: bool = False


class MiniChatApp:
    """Tiny multi-turn control plane with optional planted bugs.

    ``bug``:
      - None — correct behaviour
      - ``owner_steal`` — continue reports front_door while task still active
        (wrong exclusive owner / steal — not two simultaneous owners)
      - ``dual_owner`` — legacy alias for ``owner_steal``
      - ``drop_pin`` — continue clears workflow_id
      - ``illegal_restart`` — continue clears task (greenfield restart)
      - ``pin_without_open`` — inventory open pins entity id but leaves
        ``blocks_resolve`` false (pin-status only; hollow open)
      - ``cold_system_suggest_miss`` — cold system-suggest open routes to
        thin-structure refuse (no sketch); short re-ask forgets domain pin
    """

    def __init__(self, *, bug: Optional[str] = None) -> None:
        if bug == "dual_owner":
            bug = "owner_steal"
        self.bug = bug
        self.ledger = MiniLedger()
        self.messages: list[str] = []
        self._sketch_produced: bool = False

    def reset(self) -> None:
        self.ledger = MiniLedger()
        self.messages.clear()
        self._sketch_produced = False

    def handle(
        self,
        message: str,
        *,
        pin: Optional[CognitionPin] = None,
    ) -> TurnObservation:
        """Public interface — the only Act surface for the path-faithful demo."""
        self.messages.append(message)
        intent = (pin.task_intent if pin else "continue") or "continue"
        intent = intent.strip() or "continue"
        read_kind = (
            (pin.read_kind if pin else "") or ""
        ).strip()

        # Inventory / scenario open — identity pin + open leaf (blocks_resolve).
        # Portable shape for pin_without_open: pin is not the product answer.
        if read_kind in ("inventory_open", "scenario_open"):
            self.ledger.pins["scenario_id"] = self.ledger.pins.get(
                "scenario_id", "scen_1",
            )
            self.ledger.exclusive_owner = "front_door"
            self.ledger.active_kind = None
            self.ledger.phase = ""
            if self.bug == "pin_without_open":
                # Pin written; delivery is status-only (no open surface).
                return self._obs("pin_status_only", blocks_resolve=False)
            return self._obs("inventory_open", blocks_resolve=True)

        # Cold system-suggest open — user asks the system to invent a first
        # multi-step sketch for a named domain (no process body yet). Portable
        # law: authoring leaf + sketch_produced, not "structure empty seed".
        if read_kind == "system_suggest_open":
            domain = "domain_1"
            if pin is not None:
                domain = str(pin.extra("domain_label") or domain)
            if self.bug == "cold_system_suggest_miss":
                # Wrong leaf: treat as empty-structure refuse; no sketch, no domain.
                self.ledger.exclusive_owner = "front_door"
                self.ledger.active_kind = None
                self.ledger.phase = ""
                self._sketch_produced = False
                return self._obs("thin_structure_refuse", blocks_resolve=False)
            self.ledger.active_kind = "authoring"
            self.ledger.exclusive_owner = "authoring"
            self.ledger.phase = "sketch"
            self.ledger.pins["domain_label"] = domain
            self._sketch_produced = True
            return self._obs("authoring_sketch", blocks_resolve=True)

        # Short re-ask after cold open ("give me something to start with") —
        # must keep domain pin + authoring owner (history bind), not amnesia.
        if read_kind == "system_suggest_insist":
            if self.bug == "cold_system_suggest_miss":
                self.ledger.exclusive_owner = "front_door"
                self.ledger.active_kind = None
                self.ledger.pins.pop("domain_label", None)
                self._sketch_produced = False
                return self._obs("front_door_amnesia", blocks_resolve=False)
            if self.ledger.active_kind == "authoring" or self.ledger.pins.get(
                "domain_label",
            ):
                self.ledger.active_kind = "authoring"
                self.ledger.exclusive_owner = "authoring"
                self.ledger.phase = "sketch"
                if "domain_label" not in self.ledger.pins:
                    self.ledger.pins["domain_label"] = "domain_1"
                self._sketch_produced = True
                return self._obs("authoring_sketch", blocks_resolve=True)
            # No prior open — front door (cannot invent domain from bare insist).
            self.ledger.exclusive_owner = "front_door"
            return self._obs("front_door", blocks_resolve=False)

        # Detour supersedes sole-continue (glossary / front-door yield).
        if intent == "detour":
            self.ledger.exclusive_owner = "front_door"
            self.ledger.active_kind = None
            self.ledger.phase = ""
            return self._obs("detour_superseded", blocks_resolve=False)

        # New task / begin — pin-driven only (no keyword/NL short-circuit).
        # Matches project rule: cognition labels own meaning; code executes.
        if intent == "new_task":
            self.ledger.active_kind = "cost_out"
            self.ledger.exclusive_owner = "cost_out"
            self.ledger.phase = "sizing"
            if "workflow_id" not in self.ledger.pins:
                self.ledger.pins["workflow_id"] = "wf_1"
            return self._obs("continue_owned", blocks_resolve=True)

        # Continue mid-flight
        if self.ledger.active_kind and intent == "continue":
            if self.bug == "owner_steal":
                # Wrong exclusive owner while mid-flight (steal), not dual concurrent owners.
                self.ledger.exclusive_owner = "front_door"
                return self._obs("continue_owned", blocks_resolve=True)
            if self.bug == "drop_pin":
                self.ledger.pins.pop("workflow_id", None)
                self.ledger.exclusive_owner = "cost_out"
                return self._obs("continue_owned", blocks_resolve=True)
            if self.bug == "illegal_restart":
                self.ledger = MiniLedger()
                self._sketch_produced = False
                return self._obs("front_door", blocks_resolve=False)
            # correct
            self.ledger.exclusive_owner = self.ledger.active_kind
            return self._obs("continue_owned", blocks_resolve=True)

        # Idle front door
        self.ledger.exclusive_owner = "front_door"
        return self._obs("front_door", blocks_resolve=False)

    def _obs(self, outcome: str, *, blocks_resolve: bool) -> TurnObservation:
        return TurnObservation(
            exclusive_owner=self.ledger.exclusive_owner,
            active_kind=self.ledger.active_kind,
            pins=dict(self.ledger.pins),
            context={
                "exclusive_owner": self.ledger.exclusive_owner,
                "active_kind": self.ledger.active_kind,
                "pins": dict(self.ledger.pins),
                "phase": self.ledger.phase,
            },
            observed_outcome=outcome,
            extras={
                "blocks_resolve": blocks_resolve,
                "preferred_workflow_id": self.ledger.pins.get("workflow_id"),
                "sketch_produced": self._sketch_produced,
            },
        )


class MiniAppAdapter:
    """Driver+Observer: Act is ``app.handle``; effects only Arrange."""

    def __init__(self, app: MiniChatApp) -> None:
        self.app = app

    def apply_effect(
        self, context: dict[str, Any], effect: LedgerEffect
    ) -> dict[str, Any]:
        # Arrange-only ops for demos; production apps usually seed via API.
        op = effect.op
        payload = effect.payload or {}
        if op == "reset":
            self.app.reset()
        elif op == "seed_task":
            self.app.ledger.active_kind = str(payload.get("kind") or "cost_out")
            self.app.ledger.exclusive_owner = self.app.ledger.active_kind
            self.app.ledger.phase = str(payload.get("phase") or "sizing")
            pins = payload.get("pins") or {}
            self.app.ledger.pins.update(dict(pins))
        ctx = dict(context)
        ctx["seeded"] = True
        return ctx

    def observe_turn(
        self,
        *,
        context: dict[str, Any],
        user_text: str,
        pin: Any,
    ) -> TurnObservation:
        p = pin if isinstance(pin, CognitionPin) else None
        if isinstance(pin, Mapping):
            p = CognitionPin.from_dict(pin)
        return self.app.handle(user_text, pin=p)

    def check_invariant(
        self,
        *,
        observation: TurnObservation,
        context: Mapping[str, Any],
        spec: InvariantSpec,
    ) -> Optional[str]:
        from conjecture_behaviour_runner.invariants import check_standard_invariant

        return check_standard_invariant(observation, spec)


def sole_continue_script() -> ConjectureScript:
    """Golden: open cost-out then continue — owner + pin + blocks_resolve."""
    from conjecture_behaviour_runner.pins import CognitionPin

    return ConjectureScript(
        script_id="path_faithful_sole_continue",
        description="path-faithful: continue keeps owner and pin",
        conversation_id="conv_pf_1",
        scope=ScriptScope(
            in_scope=["sole-continue mid-flight via public handle()"],
            out_of_scope=["model quality scoring"],
            expected_refusal=["illegal restart mid-continue"],
        ),
        tags=["path-faithful", "sole-continue"],
        trajectory_invariants=[
            InvariantSpec(kind="eventually_exclusive_owner", expected="cost_out"),
            InvariantSpec(kind="pin_stable", expected="workflow_id"),
            InvariantSpec(kind="owner_changes_at_most", expected=1),
        ],
        turns=[
            DialogueTurn(
                user_text="cost out the onboarding workflow",
                pin=CognitionPin(task_intent="new_task", read_kind="cost_out"),
                invariants=[
                    InvariantSpec(kind="exclusive_owner", expected="cost_out"),
                    InvariantSpec(kind="pin_present", expected="workflow_id"),
                ],
                allowed_outcomes=["continue_owned"],
            ),
            DialogueTurn(
                user_text="make the volume 10k",
                pin=CognitionPin(task_intent="continue"),
                invariants=[
                    InvariantSpec(kind="exclusive_owner", expected="cost_out"),
                    InvariantSpec(kind="pin_equals", expected={"key": "workflow_id", "value": "wf_1"}),
                    InvariantSpec(kind="extra_true", expected="blocks_resolve"),
                ],
                allowed_outcomes=["continue_owned"],
                outcome_invariants={
                    "continue_owned": [
                        InvariantSpec(kind="active_kind", expected="cost_out"),
                    ],
                },
            ),
        ],
    )


def sole_continue_story() -> dict[str, Any]:
    """Plain-English story for UI / docs (planned turns + must-hold)."""
    return {
        "title": "What this golden tests",
        "why": (
            "LLM proposes · code enforces. We are not grading chat prose. We check "
            "whether the coded ledger + handoff rules still hold after Act. "
            "This demo’s mid-flight kind is cost_out with pin workflow_id — host-defined "
            "strings, not a Conjecture enum. Your ledger might use claim_review + claim_id "
            "(or any other type). Same shape: owner and pin must hold on continue, even when "
            "a message looks like ordinary chat or a model would try to steal to the front door."
        ),
        "plot": (
            "Demo vocabulary: user starts cost_out on a workflow, then continues with a "
            "volume change. Owner must stay cost_out and workflow_id must stay pinned. "
            "On your host, substitute your own exclusive_owner / pin keys."
        ),
        "what_green_means": (
            "PASS = measured owner/pin/blocks match the rule-set after each turn "
            "(enforcement held under pinned labels for whatever kind strings you asserted). "
            "FAIL = steal, pin drop, or illegal restart — even if a reply could still look fine."
        ),
        "turns": [
            {
                "index": 0,
                "user_says": "cost out the onboarding workflow",
                "story": "Turn 0: start cost-out and bind a workflow pin.",
                "must_hold": [
                    "Owner is cost_out",
                    "workflow_id pin is present",
                    "Landing in continue_owned",
                ],
            },
            {
                "index": 1,
                "user_says": "make the volume 10k",
                "story": "Turn 1: continue mid-flight — must not steal owner or drop pin.",
                "must_hold": [
                    "Owner is still cost_out",
                    "workflow_id still equals wf_1",
                    "blocks_resolve stays true",
                ],
            },
        ],
        "planted_bugs": [
            {
                "id": "owner_steal",
                "plain": "Continue reports front_door while task active (owner steal)",
            },
            {
                "id": "drop_pin",
                "plain": "Continue drops workflow_id",
            },
            {
                "id": "illegal_restart",
                "plain": "Continue wipes the active task",
            },
            {
                "id": "pin_without_open",
                "plain": "Inventory open pins scenario_id but blocks_resolve is false",
            },
        ],
    }


def run_path_faithful_demo(*, bug: Optional[str] = None) -> dict[str, Any]:
    """Run sole-continue golden against mini-app; return result dict for UI/CLI."""
    from conjecture_behaviour_runner.harness import run_script
    from conjecture_behaviour_runner.modes import LlmMode

    app = MiniChatApp(bug=bug)
    adapter = MiniAppAdapter(app)
    script = sole_continue_script()
    result = run_script(script, adapter=adapter, llm_mode=LlmMode.STUB)
    story = sole_continue_story()
    # Merge planned must_hold into observed turns for the UI timeline.
    planned = {t["index"]: t for t in story["turns"]}
    turns_out: list[dict[str, Any]] = []
    for tr in result.turn_results:
        idx = int(tr.get("index", 0))
        plan = planned.get(idx) or {}
        obs = tr.get("observation") or {}
        turns_out.append(
            {
                "index": idx,
                "user_text": tr.get("user_text"),
                "story": plan.get("story"),
                "must_hold": plan.get("must_hold") or [],
                "passed": not (tr.get("failures") or []),
                "failures": list(tr.get("failures") or []),
                "exclusive_owner": obs.get("exclusive_owner"),
                "active_kind": obs.get("active_kind"),
                "pins": dict(obs.get("pins") or {}),
                "observed_outcome": obs.get("observed_outcome"),
                "extras": dict(obs.get("extras") or {}),
            }
        )
    return {
        "bug": bug,
        "passed": result.passed,
        "failures": list(result.failures),
        "script_id": result.script_id,
        "messages": list(app.messages),
        "story": story,
        "turns": turns_out,
        "result": result.to_dict(),
    }


def prove_planted_bugs() -> dict[str, Any]:
    """Correct app passes; each planted bug fails the same golden."""
    clean = run_path_faithful_demo(bug=None)
    steal = run_path_faithful_demo(bug="owner_steal")
    drop = run_path_faithful_demo(bug="drop_pin")
    restart = run_path_faithful_demo(bug="illegal_restart")
    steal_caught = not steal["passed"]
    return {
        "clean_passes": clean["passed"],
        "owner_steal_caught": steal_caught,
        # Legacy key (misnamed — was never two concurrent owners)
        "dual_owner_caught": steal_caught,
        "drop_pin_caught": not drop["passed"],
        "illegal_restart_caught": not restart["passed"],
        "cognition_mode": "stub_pinned",
        "helpful": (
            clean["passed"]
            and steal_caught
            and (not drop["passed"])
            and (not restart["passed"])
        ),
        "story": sole_continue_story(),
        "details": {
            "clean": clean,
            "owner_steal": steal,
            "drop_pin": drop,
            "illegal_restart": restart,
        },
    }
