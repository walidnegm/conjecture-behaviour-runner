"""Host adapter protocol — bind Conjecture to a control plane.

Public consumers implement this protocol against the Conversation Control
Plane package or their own turn-ownership ledger.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Protocol, runtime_checkable

from conjecture_behaviour_runner.pins import CognitionPin
from conjecture_behaviour_runner.script import InvariantSpec, LedgerEffect


@dataclass
class TurnObservation:
    """What the harness saw after applying a turn (host-filled)."""

    exclusive_owner: Optional[str] = None
    active_kind: Optional[str] = None
    pins: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    observed_outcome: Optional[str] = None
    extras: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ControlPlaneAdapter(Protocol):
    """Minimal surface the harness needs from a host control plane."""

    def apply_effect(
        self, context: dict[str, Any], effect: LedgerEffect
    ) -> dict[str, Any]:
        """Apply a ledger effect; return updated context projection."""
        ...

    def observe_turn(
        self,
        *,
        context: dict[str, Any],
        user_text: str,
        pin: Optional[CognitionPin],
    ) -> TurnObservation:
        """Project exclusive owner / pins after cognition for this turn."""
        ...

    def check_invariant(
        self,
        *,
        observation: TurnObservation,
        context: dict[str, Any],
        spec: InvariantSpec,
    ) -> Optional[str]:
        """Return failure message if invariant fails, else None."""
        ...


class NullControlPlaneAdapter:
    """No-op adapter for packaging smoke tests and examples.

    Always reports empty observation; only ``kind == \"always_true\"``
    invariants pass. Replace with a real control-plane binding for host use.
    """

    def apply_effect(
        self, context: dict[str, Any], effect: LedgerEffect
    ) -> dict[str, Any]:
        ctx = dict(context)
        ctx.setdefault("_effects", []).append(
            {"op": effect.op, "payload": dict(effect.payload)}
        )
        return ctx

    def observe_turn(
        self,
        *,
        context: dict[str, Any],
        user_text: str,
        pin: Optional[CognitionPin],
    ) -> TurnObservation:
        return TurnObservation(
            exclusive_owner=None,
            active_kind=None,
            pins={},
            context=dict(context),
            observed_outcome="null_adapter",
            extras={"user_text": user_text, "pin": pin.to_dict() if pin else None},
        )

    def check_invariant(
        self,
        *,
        observation: TurnObservation,
        context: Mapping[str, Any],
        spec: InvariantSpec,
    ) -> Optional[str]:
        if spec.kind == "always_true":
            return None
        if spec.kind == "observed_outcome" and observation.observed_outcome == spec.expected:
            return None
        return (
            f"null_adapter cannot verify invariant kind={spec.kind!r} "
            f"(expected={spec.expected!r}); bind a real ControlPlaneAdapter"
        )
