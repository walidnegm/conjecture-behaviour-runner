"""Ratchet: the standard invariant library (no companion package needed)."""
from __future__ import annotations

import unittest

from conjecture_behaviour_runner.invariants import (
    STANDARD_INVARIANT_KINDS,
    BaseControlPlaneAdapter,
    check_standard_invariant,
)
from conjecture_behaviour_runner.protocol import TurnObservation
from conjecture_behaviour_runner.script import InvariantSpec


def _obs(**kw):
    return TurnObservation(**kw)


class StandardInvariantTests(unittest.TestCase):
    def test_always_true(self) -> None:
        self.assertIsNone(
            check_standard_invariant(_obs(), InvariantSpec(kind="always_true"))
        )

    def test_exclusive_owner_pass_and_fail(self) -> None:
        obs = _obs(exclusive_owner="cost_out")
        self.assertIsNone(
            check_standard_invariant(obs, InvariantSpec(kind="exclusive_owner", expected="cost_out"))
        )
        msg = check_standard_invariant(
            obs, InvariantSpec(kind="exclusive_owner", expected="front_door")
        )
        self.assertIsNotNone(msg)
        self.assertIn("cost_out", msg)

    def test_owner_not(self) -> None:
        obs = _obs(exclusive_owner="front_door")
        self.assertIsNone(
            check_standard_invariant(obs, InvariantSpec(kind="owner_not", expected="cost_out"))
        )
        self.assertIsNotNone(
            check_standard_invariant(obs, InvariantSpec(kind="owner_not", expected="front_door"))
        )

    def test_pin_present_absent_equals(self) -> None:
        obs = _obs(pins={"workflow_id": "wf_1"})
        self.assertIsNone(
            check_standard_invariant(obs, InvariantSpec(kind="pin_present", expected="workflow_id"))
        )
        self.assertIsNotNone(
            check_standard_invariant(obs, InvariantSpec(kind="pin_present", expected="project_id"))
        )
        self.assertIsNone(
            check_standard_invariant(obs, InvariantSpec(kind="pin_absent", expected="project_id"))
        )
        self.assertIsNone(
            check_standard_invariant(
                obs, InvariantSpec(kind="pin_equals", expected={"key": "workflow_id", "value": "wf_1"})
            )
        )
        self.assertIsNotNone(
            check_standard_invariant(
                obs, InvariantSpec(kind="pin_equals", expected=["workflow_id", "wf_2"])
            )
        )

    def test_pin_presence_not_truthiness(self) -> None:
        # Empty string / 0 / False are not usable bound pin values.
        for bad in ("", 0, False, None):
            obs = _obs(pins={"workflow_id": bad})
            self.assertIsNotNone(
                check_standard_invariant(
                    obs, InvariantSpec(kind="pin_present", expected="workflow_id")
                ),
                msg=f"pin_present should fail for {bad!r}",
            )
        # missing vs present_null both "absent" for pin_absent
        self.assertIsNone(
            check_standard_invariant(
                _obs(pins={}), InvariantSpec(kind="pin_absent", expected="workflow_id")
            )
        )
        self.assertIsNone(
            check_standard_invariant(
                _obs(pins={"workflow_id": None}),
                InvariantSpec(kind="pin_absent", expected="workflow_id"),
            )
        )
        self.assertIsNone(
            check_standard_invariant(
                _obs(pins={}), InvariantSpec(kind="pin_key_missing", expected="workflow_id")
            )
        )
        self.assertIsNotNone(
            check_standard_invariant(
                _obs(pins={"workflow_id": None}),
                InvariantSpec(kind="pin_key_missing", expected="workflow_id"),
            )
        )

    def test_extra_true_false_strict_not_truthy(self) -> None:
        obs = _obs(extras={"blocks_resolve": True, "preferred_workflow_id": "wf_1", "flag": False})
        self.assertIsNone(
            check_standard_invariant(obs, InvariantSpec(kind="extra_true", expected="blocks_resolve"))
        )
        self.assertIsNotNone(
            check_standard_invariant(obs, InvariantSpec(kind="extra_false", expected="blocks_resolve"))
        )
        self.assertIsNone(
            check_standard_invariant(obs, InvariantSpec(kind="extra_false", expected="flag"))
        )
        # missing ≠ false
        self.assertIsNotNone(
            check_standard_invariant(obs, InvariantSpec(kind="extra_false", expected="missing_key"))
        )
        self.assertIsNone(
            check_standard_invariant(obs, InvariantSpec(kind="extra_missing", expected="missing_key"))
        )
        # truthy non-True fails extra_true
        self.assertIsNotNone(
            check_standard_invariant(
                _obs(extras={"blocks_resolve": 1}),
                InvariantSpec(kind="extra_true", expected="blocks_resolve"),
            )
        )
        self.assertIsNone(
            check_standard_invariant(
                obs,
                InvariantSpec(
                    kind="extra_equals",
                    expected={"key": "preferred_workflow_id", "value": "wf_1"},
                ),
            )
        )

    def test_unknown_kind_fails_closed(self) -> None:
        msg = check_standard_invariant(_obs(), InvariantSpec(kind="totally_made_up"))
        self.assertIsNotNone(msg)
        self.assertIn("unknown invariant kind", msg)

    def test_all_advertised_kinds_are_handled(self) -> None:
        # Every advertised kind must return something other than the "unknown" message
        # for a well-formed spec (fail-closed guard against silent drift).
        obs = _obs(
            exclusive_owner="x",
            active_kind="k",
            pins={"workflow_id": "1"},
            observed_outcome="o",
            extras={"f": True, "g": False},
        )
        specs = {
            "always_true": InvariantSpec(kind="always_true"),
            "exclusive_owner": InvariantSpec(kind="exclusive_owner", expected="x"),
            "owner_not": InvariantSpec(kind="owner_not", expected="y"),
            "active_kind": InvariantSpec(kind="active_kind", expected="k"),
            "kind_equals": InvariantSpec(kind="kind_equals", expected="k"),
            "pin_present": InvariantSpec(kind="pin_present", expected="workflow_id"),
            "pin_absent": InvariantSpec(kind="pin_absent", expected="project_id"),
            "pin_equals": InvariantSpec(
                kind="pin_equals", expected={"key": "workflow_id", "value": "1"}
            ),
            "pin_key_missing": InvariantSpec(kind="pin_key_missing", expected="project_id"),
            "observed_outcome": InvariantSpec(kind="observed_outcome", expected="o"),
            "extra_equals": InvariantSpec(
                kind="extra_equals", expected={"key": "f", "value": True}
            ),
            "extra_true": InvariantSpec(kind="extra_true", expected="f"),
            "extra_false": InvariantSpec(kind="extra_false", expected="g"),
            "extra_missing": InvariantSpec(kind="extra_missing", expected="nope"),
        }
        for kind in STANDARD_INVARIANT_KINDS:
            self.assertIn(kind, specs, f"advertised kind {kind!r} has no coverage here")
            msg = check_standard_invariant(obs, specs[kind])
            if msg is not None:
                self.assertNotIn("unknown invariant kind", msg, f"{kind} routed to unknown")

    def test_base_adapter_delegates(self) -> None:
        adapter = BaseControlPlaneAdapter()
        obs = _obs(exclusive_owner="cost_out")
        self.assertIsNone(
            adapter.check_invariant(
                observation=obs,
                context={},
                spec=InvariantSpec(kind="exclusive_owner", expected="cost_out"),
            )
        )


if __name__ == "__main__":
    unittest.main()
