"""Trajectory-level (cross-turn) oracle checks.

These run after all turns complete, over the list of per-turn observations.
Temporal kinds are evaluated by the harness, not by host adapters.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from conjecture_behaviour_runner.script import InvariantSpec


def check_trajectory_invariant(
    turn_observations: Sequence[Mapping[str, Any]],
    spec: InvariantSpec,
) -> Optional[str]:
    """Return failure message or None if the trajectory invariant holds."""
    kind = spec.kind
    exp = spec.expected
    owners = [t.get("exclusive_owner") for t in turn_observations]
    kinds = [t.get("active_kind") for t in turn_observations]
    pins_list = [t.get("pins") or {} for t in turn_observations]
    outcomes = [t.get("observed_outcome") for t in turn_observations]

    if kind == "always_true":
        return None

    if kind == "eventually_exclusive_owner":
        if any(o == exp for o in owners):
            return None
        return f"eventually_exclusive_owner: never saw {exp!r} in {owners!r}"

    if kind == "never_exclusive_owner":
        if any(o == exp for o in owners):
            return f"never_exclusive_owner: saw {exp!r} in {owners!r}"
        return None

    if kind == "always_exclusive_owner":
        if owners and all(o == exp for o in owners):
            return None
        return f"always_exclusive_owner: expected all {exp!r}, got {owners!r}"

    if kind == "eventually_outcome":
        if any(o == exp for o in outcomes):
            return None
        return f"eventually_outcome: never saw {exp!r} in {outcomes!r}"

    if kind == "never_outcome":
        if any(o == exp for o in outcomes):
            return f"never_outcome: saw {exp!r} in {outcomes!r}"
        return None

    if kind == "always_pin_present":
        key = exp if isinstance(exp, str) else (exp or {}).get("key") if isinstance(exp, Mapping) else None
        if not key:
            return "always_pin_present: expected pin key string"
        for i, pins in enumerate(pins_list):
            val = pins.get(key) if isinstance(pins, Mapping) else None
            if not val:
                return f"always_pin_present: pin {key!r} missing/empty at turn[{i}]"
        return None

    if kind == "pin_stable":
        # expected = pin key; value once set must not change to a different non-null
        key = exp if isinstance(exp, str) else (exp or {}).get("key") if isinstance(exp, Mapping) else None
        if not key:
            return "pin_stable: expected pin key string"
        seen = None
        for i, pins in enumerate(pins_list):
            val = pins.get(key) if isinstance(pins, Mapping) else None
            if val is None or val == "":
                continue
            if seen is None:
                seen = val
            elif val != seen:
                return (
                    f"pin_stable: pin {key!r} changed {seen!r} → {val!r} at turn[{i}]"
                )
        return None

    if kind == "owner_changes_at_most":
        # expected = int max number of changes (0 = never changes once set)
        try:
            max_changes = int(exp)
        except (TypeError, ValueError):
            return f"owner_changes_at_most: expected int, got {exp!r}"
        changes = 0
        prev = None
        for o in owners:
            if prev is None:
                prev = o
                continue
            if o != prev:
                changes += 1
                prev = o
        if changes <= max_changes:
            return None
        return (
            f"owner_changes_at_most: {changes} changes > max {max_changes} "
            f"(owners={owners!r})"
        )

    if kind == "active_kind_sequence_prefix":
        # expected = list of kinds that must appear as a prefix of non-None kinds
        if not isinstance(exp, (list, tuple)):
            return f"active_kind_sequence_prefix: expected list, got {exp!r}"
        filtered = [k for k in kinds if k is not None]
        prefix = list(exp)
        if filtered[: len(prefix)] == prefix:
            return None
        return (
            f"active_kind_sequence_prefix: wanted {prefix!r} prefix, got {filtered!r}"
        )

    return (
        f"unknown trajectory invariant kind={kind!r} "
        f"(known: eventually_exclusive_owner, never_exclusive_owner, "
        f"always_exclusive_owner, eventually_outcome, never_outcome, "
        f"always_pin_present, pin_stable, owner_changes_at_most, "
        f"active_kind_sequence_prefix, always_true)"
    )


TRAJECTORY_INVARIANT_KINDS: tuple[str, ...] = (
    "always_true",
    "eventually_exclusive_owner",
    "never_exclusive_owner",
    "always_exclusive_owner",
    "eventually_outcome",
    "never_outcome",
    "always_pin_present",
    "pin_stable",
    "owner_changes_at_most",
    "active_kind_sequence_prefix",
)
