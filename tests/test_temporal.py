"""Trajectory / temporal invariant kinds."""
from __future__ import annotations

from conjecture_behaviour_runner.script import InvariantSpec
from conjecture_behaviour_runner.temporal import check_trajectory_invariant


def _obs(**kwargs):
    base = {
        "exclusive_owner": None,
        "active_kind": None,
        "pins": {},
        "observed_outcome": None,
    }
    base.update(kwargs)
    return base


def test_pin_stable_fails_on_disappearance() -> None:
    turns = [
        _obs(pins={"workflow_id": "wf_1"}),
        _obs(pins={}),  # missing after established
        _obs(pins={"workflow_id": "wf_1"}),
    ]
    msg = check_trajectory_invariant(
        turns, InvariantSpec(kind="pin_stable", expected="workflow_id")
    )
    assert msg is not None
    assert "missing" in msg or "empty" in msg


def test_pin_stable_fails_on_value_change() -> None:
    turns = [
        _obs(pins={"workflow_id": "wf_1"}),
        _obs(pins={"workflow_id": "wf_2"}),
    ]
    msg = check_trajectory_invariant(
        turns, InvariantSpec(kind="pin_stable", expected="workflow_id")
    )
    assert msg is not None
    assert "changed" in msg


def test_pin_stable_ok_when_held() -> None:
    turns = [
        _obs(pins={"workflow_id": "wf_1"}),
        _obs(pins={"workflow_id": "wf_1"}),
    ]
    assert (
        check_trajectory_invariant(
            turns, InvariantSpec(kind="pin_stable", expected="workflow_id")
        )
        is None
    )


def test_eventually_exclusive_owner() -> None:
    turns = [_obs(exclusive_owner="a"), _obs(exclusive_owner="cost_out")]
    assert (
        check_trajectory_invariant(
            turns,
            InvariantSpec(kind="eventually_exclusive_owner", expected="cost_out"),
        )
        is None
    )
    msg = check_trajectory_invariant(
        turns,
        InvariantSpec(kind="eventually_exclusive_owner", expected="other"),
    )
    assert msg is not None


def test_owner_changes_at_most() -> None:
    turns = [
        _obs(exclusive_owner="a"),
        _obs(exclusive_owner="a"),
        _obs(exclusive_owner="b"),
    ]
    assert (
        check_trajectory_invariant(
            turns, InvariantSpec(kind="owner_changes_at_most", expected=1)
        )
        is None
    )
    msg = check_trajectory_invariant(
        turns, InvariantSpec(kind="owner_changes_at_most", expected=0)
    )
    assert msg is not None
