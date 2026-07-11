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
    "pin_present",       # key present with a non-null, non-empty value
    "pin_absent",        # key missing or null
    "pin_equals",        # expected={key,value} or [key,value] — strict ==
    "pin_key_missing",   # key not in pins mapping
    "observed_outcome",  # observation.observed_outcome == expected (str)
    "extra_equals",      # expected={key,value}: observation.extras[key] == value
    "extra_true",        # key present and value is True (not mere truthiness)
    "extra_false",       # key present and value is False (missing fails)
    "extra_missing",     # key not in extras
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


def _pin_presence(pins: Mapping[str, Any], key: Any) -> str:
    """Classify pin map membership for contract checks.

    Returns one of: missing | present_null | present_empty | present_false | present_value
    """
    if key not in pins:
        return "missing"
    val = pins[key]
    if val is None:
        return "present_null"
    if val is False:
        return "present_false"
    if val == "" or val == 0:
        return "present_empty"
    return "present_value"


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
        state = _pin_presence(observation.pins, key)
        if state == "present_value":
            return None
        return (
            f"pin {key!r} not a usable bound value (state={state}, "
            f"pins={dict(observation.pins)!r})"
        )

    if kind == "pin_absent":
        key = _key(exp)
        state = _pin_presence(observation.pins, key)
        if state in ("missing", "present_null"):
            return None
        return (
            f"pin {key!r} expected absent/null but state={state} "
            f"(={observation.pins.get(key)!r})"
        )

    if kind == "pin_key_missing":
        key = _key(exp)
        if key not in observation.pins:
            return None
        return f"pin key {key!r} present but expected missing"

    if kind == "pin_equals":
        key, val = _key_value(exp)
        if key not in observation.pins:
            return f"pin {key!r} missing (cannot equal {val!r})"
        got = observation.pins[key]
        if got == val:
            return None
        return f"pin {key!r}={got!r} != expected {val!r}"

    if kind == "observed_outcome":
        if observation.observed_outcome == exp:
            return None
        return f"observed_outcome={observation.observed_outcome!r} != expected {exp!r}"

    if kind == "extra_equals":
        key, val = _key_value(exp)
        if key not in observation.extras:
            return f"extra {key!r} missing (cannot equal {val!r})"
        got = observation.extras[key]
        if got == val:
            return None
        return f"extra {key!r}={got!r} != expected {val!r}"

    if kind == "extra_true":
        key = _key(exp)
        if key not in observation.extras:
            return f"extra {key!r} missing (expected True)"
        got = observation.extras[key]
        if got is True:
            return None
        return f"extra {key!r} is {got!r}, expected True (strict, not truthy)"

    if kind == "extra_false":
        key = _key(exp)
        if key not in observation.extras:
            return f"extra {key!r} missing (expected False — missing ≠ false)"
        got = observation.extras[key]
        if got is False:
            return None
        return f"extra {key!r} is {got!r}, expected False (strict, not falsy)"

    if kind == "extra_missing":
        key = _key(exp)
        if key not in observation.extras:
            return None
        return f"extra {key!r} present but expected missing (={observation.extras[key]!r})"

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
