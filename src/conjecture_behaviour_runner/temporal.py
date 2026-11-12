"""Trajectory-level (cross-turn) verifier checks.

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
        # expected = pin key.
        # Once established (first non-empty), the pin must remain present with
        # the same value on every later turn. Disappearance is a failure
        # (wf_1 → missing → wf_1 must FAIL).
        key = exp if isinstance(exp, str) else (exp or {}).get("key") if isinstance(exp, Mapping) else None
        if not key:
            return "pin_stable: expected pin key string"
        seen = None
        established = False
        for i, pins in enumerate(pins_list):
            val = pins.get(key) if isinstance(pins, Mapping) else None
            empty = val is None or val == ""
            if not established:
                if empty:
                    continue
                seen = val
                established = True
                continue
            if empty:
                return (
                    f"pin_stable: pin {key!r} missing/empty at turn[{i}] "
                    f"after established {seen!r}"
                )
            if val != seen:
                return (
                    f"pin_stable: pin {key!r} changed {seen!r} → {val!r} at turn[{i}]"
                )
        return None

    if kind == "act_stable":
        # The act the host DISPATCHED, turn by turn — `extras["act"]`.
        #
        # Cognition commits one canonical act; every later stage may refine
        # refs, ASK, REJECT, DEFER, DENY or FAIL, but may not answer a
        # DIFFERENT act. This is the cross-turn form of that law, and the
        # reason it needs a trajectory check rather than a per-turn one: no
        # single turn looks wrong. The failure is that turn 2 answered
        # something turn 1 did not ask.
        #
        # `expected` is optional. Omit it to mean "whatever was committed
        # first"; give an act id to pin it.
        want = exp if isinstance(exp, str) and exp else None
        acts = [
            (t.get("extras") or {}).get("act")
            if isinstance(t.get("extras"), Mapping) else None
            for t in turn_observations
        ]
        seen = want
        for i, act in enumerate(acts):
            if act is None or act == "":
                # A turn that dispatched no act cannot contradict one.
                continue
            if seen is None:
                seen = act
                continue
            if act != seen:
                return (
                    f"act_stable: act changed {seen!r} → {act!r} at turn[{i}] "
                    f"(acts={acts!r}) — downstream reinterpreted the act"
                )
        if want is not None and seen != want:
            return f"act_stable: never saw act {want!r} (acts={acts!r})"
        return None

    if kind == "never_invented":
        # Unresolved means ASK / REJECT / DEFER — never a fabricated answer.
        #
        # Reads `extras["grounded"]`: the host says, per turn, whether the act
        # had everything it needed. Where it did NOT, the outcome must be one
        # the product is allowed to give while it still does not know. Prose
        # in that slot is the invention this forbids.
        #
        # `expected` is the allowed set; it defaults to ask/reject/defer so a
        # script that simply names the kind gets the law.
        allowed = exp if isinstance(exp, (list, tuple, set)) else None
        if allowed is None:
            allowed = ("ask", "reject", "defer")
        allowed_norm = {str(a).strip().lower() for a in allowed}
        for i, t in enumerate(turn_observations):
            extras = t.get("extras") if isinstance(t.get("extras"), Mapping) else {}
            if "grounded" not in extras:
                # Silent when the host does not report it — an invariant that
                # guesses is worse than one that abstains.
                continue
            if extras.get("grounded"):
                continue
            outcome = str(t.get("observed_outcome") or "").strip().lower()
            if outcome not in allowed_norm:
                return (
                    f"never_invented: turn[{i}] was not grounded but answered "
                    f"{outcome!r}; allowed {sorted(allowed_norm)!r}"
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
        f"always_pin_present, pin_stable, act_stable, never_invented, "
        f"owner_changes_at_most, active_kind_sequence_prefix, always_true)"
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
    "act_stable",
    "never_invented",
    "owner_changes_at_most",
    "active_kind_sequence_prefix",
)
