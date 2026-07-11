"""Built-in invariant library — make ``run_script`` prove real behaviour.

Slice 0 shipped the *slot* for invariants but no working checkers, so the only
verifiable invariant out of the box was ``always_true``. This module ships the
standard behaviour invariants an adapter needs (owner, kind, pin, outcome,
extras) plus ``BaseControlPlaneAdapter`` — subclass it, implement
``apply_effect`` + ``observe_turn``, and get ``check_invariant`` for free.

The checks read only the ``TurnObservation`` (and its ``extras``) an adapter
fills, so they are host-agnostic: the *observation* is where a host binds its
control plane; the *invariant kinds* are portable.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from conjecture_behaviour_runner.protocol import TurnObservation
from conjecture_behaviour_runner.script import InvariantSpec, LedgerEffect

# Stable invariant kinds the standard checker understands. Adapters may add more
# by overriding ``check_invariant`` and delegating unknown kinds to super().
STANDARD_INVARIANT_KINDS: tuple[str, ...] = (
    "always_true",
    "exclusive_owner",   # observation.exclusive_owner == expected (str)
    "owner_not",         # observation.exclusive_owner != expected (str)
    "active_kind",       # observation.active_kind == expected (str)
    "kind_equals",       # alias of active_kind
    "pin_present",       # expected=key: observation.pins[key] is truthy
    "pin_absent",        # expected=key: observation.pins[key] is missing/empty
    "pin_equals",        # expected={key,value} or [key,value]
    "observed_outcome",  # observation.observed_outcome == expected (str)
    "extra_equals",      # expected={key,value}: observation.extras[key] == value
    "extra_true",        # expected=key: bool(observation.extras[key]) is True
    "extra_false",       # expected=key: bool(observation.extras[key]) is False
)


def _key(expected: Any) -> Any:
    if isinstance(expected, str):
        return expected
    if isinstance(expected, Mapping):
        return expected.get("key")
    raise ValueError(f"expected a key string or {{'key': ...}} mapping, got {expected!r}")


def _key_value(expected: Any) -> tuple[Any, Any]:
    if isinstance(expected, Mapping):
        return expected.get("key"), expected.get("value")
    if isinstance(expected, (list, tuple)) and len(expected) == 2:
        return expected[0], expected[1]
    raise ValueError(
        f"expected a (key, value) pair or {{'key','value'}} mapping, got {expected!r}"
    )


def check_standard_invariant(
    observation: TurnObservation, spec: InvariantSpec
) -> Optional[str]:
    """Return a failure message if the invariant fails, else ``None``.

    Pure over the observation; no host or DB access. Unknown kinds return a
    message naming the known set (fail closed — never silently pass).
    """
    kind = spec.kind
    exp = spec.expected

    if kind == "always_true":
        return None

    if kind == "exclusive_owner":
        if observation.exclusive_owner == exp:
            return None
        return f"exclusive_owner={observation.exclusive_owner!r} != expected {exp!r}"

    if kind == "owner_not":
        if observation.exclusive_owner != exp:
            return None
        return f"exclusive_owner={observation.exclusive_owner!r} must not equal {exp!r}"

    if kind in ("active_kind", "kind_equals"):
        if observation.active_kind == exp:
            return None
        return f"active_kind={observation.active_kind!r} != expected {exp!r}"

    if kind == "pin_present":
        key = _key(exp)
        if observation.pins.get(key):
            return None
        return f"pin {key!r} absent/empty (pins={dict(observation.pins)!r})"

    if kind == "pin_absent":
        key = _key(exp)
        if not observation.pins.get(key):
            return None
        return f"pin {key!r} present but expected absent (={observation.pins.get(key)!r})"

    if kind == "pin_equals":
        key, val = _key_value(exp)
        got = observation.pins.get(key)
        if got == val:
            return None
        return f"pin {key!r}={got!r} != expected {val!r}"

    if kind == "observed_outcome":
        if observation.observed_outcome == exp:
            return None
        return f"observed_outcome={observation.observed_outcome!r} != expected {exp!r}"

    if kind == "extra_equals":
        key, val = _key_value(exp)
        got = observation.extras.get(key)
        if got == val:
            return None
        return f"extra {key!r}={got!r} != expected {val!r}"

    if kind == "extra_true":
        key = _key(exp)
        if bool(observation.extras.get(key)):
            return None
        return f"extra {key!r} not truthy (={observation.extras.get(key)!r})"

    if kind == "extra_false":
        key = _key(exp)
        if not bool(observation.extras.get(key)):
            return None
        return f"extra {key!r} truthy but expected false (={observation.extras.get(key)!r})"

    return (
        f"unknown invariant kind={kind!r} — standard kinds: "
        f"{', '.join(STANDARD_INVARIANT_KINDS)} (override check_invariant for custom kinds)"
    )


class BaseControlPlaneAdapter:
    """Adapter base that ships the standard invariant library.

    Subclasses implement ``apply_effect`` and ``observe_turn`` (the host binding)
    and inherit a working ``check_invariant``. Override ``check_invariant`` to add
    custom kinds and ``return super().check_invariant(...)`` for the standard set.
    """

    def apply_effect(
        self, context: dict[str, Any], effect: LedgerEffect
    ) -> dict[str, Any]:  # pragma: no cover - abstract
        raise NotImplementedError

    def observe_turn(
        self,
        *,
        context: dict[str, Any],
        user_text: str,
        pin: Any,
    ) -> TurnObservation:  # pragma: no cover - abstract
        raise NotImplementedError

    def check_invariant(
        self,
        *,
        observation: TurnObservation,
        context: Mapping[str, Any],
        spec: InvariantSpec,
    ) -> Optional[str]:
        return check_standard_invariant(observation, spec)
