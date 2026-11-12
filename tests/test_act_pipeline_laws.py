"""I8 / I10 as trajectory law — the act survives the pipeline that carries it.

These two kinds exist because the failure they catch is invisible per turn.
`conv_5142ed5c` (2026-09-15): one chip click, four replies, none of them the
act. Every reply was well-formed; the act was never ambiguous; grounding
resolved it correctly on turn three and three separate downstream stages each
answered as though it were something else.

A per-turn assertion passes on every one of those turns in isolation. Only the
trajectory shows a single committed act producing four answers.
"""
from __future__ import annotations

import unittest

from conjecture_behaviour_runner.script import InvariantSpec
from conjecture_behaviour_runner.temporal import (
    TRAJECTORY_INVARIANT_KINDS,
    check_trajectory_invariant,
)


def turn(act=None, grounded=None, outcome=None):
    extras = {}
    if act is not None:
        extras["act"] = act
    if grounded is not None:
        extras["grounded"] = grounded
    return {"extras": extras, "observed_outcome": outcome}


class TheKindsAreDeclared(unittest.TestCase):
    def test_both_kinds_are_in_the_vocabulary(self) -> None:
        self.assertIn("act_stable", TRAJECTORY_INVARIANT_KINDS)
        self.assertIn("never_invented", TRAJECTORY_INVARIANT_KINDS)

    def test_the_unknown_kind_message_names_them(self) -> None:
        """A runner that lists its kinds wrongly teaches the wrong vocabulary."""
        msg = check_trajectory_invariant([], InvariantSpec(kind="nope"))
        self.assertIsNotNone(msg)
        self.assertIn("act_stable", msg)
        self.assertIn("never_invented", msg)


class ActStableIsI8(unittest.TestCase):
    def test_one_act_across_the_trajectory_holds(self) -> None:
        obs = [turn(act="domain_use_recommended") for _ in range(4)]
        self.assertIsNone(
            check_trajectory_invariant(obs, InvariantSpec(kind="act_stable")),
        )

    def test_a_reinterpretation_fails_and_names_both_acts(self) -> None:
        obs = [
            turn(act="domain_use_recommended"),
            turn(act="workflow_describe"),      # the conv_5142ed5c turn 3
        ]
        msg = check_trajectory_invariant(obs, InvariantSpec(kind="act_stable"))
        self.assertIsNotNone(msg)
        self.assertIn("domain_use_recommended", msg)
        self.assertIn("workflow_describe", msg)
        self.assertIn("turn[1]", msg)

    def test_a_turn_that_dispatched_no_act_cannot_contradict_one(self) -> None:
        """Absence is not a different act. A turn that acted on nothing is
        silent here — `never_invented` is the law that judges that turn."""
        obs = [turn(act="a"), turn(), turn(act=""), turn(act="a")]
        self.assertIsNone(
            check_trajectory_invariant(obs, InvariantSpec(kind="act_stable")),
        )

    def test_the_expected_act_may_be_pinned(self) -> None:
        obs = [turn(act="b"), turn(act="b")]
        msg = check_trajectory_invariant(
            obs, InvariantSpec(kind="act_stable", expected="a"),
        )
        self.assertIsNotNone(msg)
        self.assertIn("'a'", msg)

    def test_pinning_passes_when_the_act_matches(self) -> None:
        obs = [turn(act="a"), turn(act="a")]
        self.assertIsNone(
            check_trajectory_invariant(
                obs, InvariantSpec(kind="act_stable", expected="a"),
            ),
        )

    def test_a_host_reporting_nothing_abstains(self) -> None:
        """An invariant that guesses is worse than one that abstains."""
        self.assertIsNone(
            check_trajectory_invariant(
                [turn(), turn()], InvariantSpec(kind="act_stable"),
            ),
        )


class NeverInventedIsI10(unittest.TestCase):
    def test_an_ungrounded_turn_may_ask(self) -> None:
        obs = [turn(grounded=False, outcome="ask")]
        self.assertIsNone(
            check_trajectory_invariant(obs, InvariantSpec(kind="never_invented")),
        )

    def test_an_ungrounded_turn_may_not_answer(self) -> None:
        obs = [
            turn(grounded=True, outcome="answer"),
            turn(grounded=False, outcome="answer"),   # the invention
        ]
        msg = check_trajectory_invariant(obs, InvariantSpec(kind="never_invented"))
        self.assertIsNotNone(msg)
        self.assertIn("turn[1]", msg)
        self.assertIn("answer", msg)

    def test_a_grounded_turn_is_unconstrained(self) -> None:
        """This law is about not knowing. It says nothing about knowing."""
        obs = [turn(grounded=True, outcome="anything_at_all")]
        self.assertIsNone(
            check_trajectory_invariant(obs, InvariantSpec(kind="never_invented")),
        )

    def test_the_allowed_set_is_overridable(self) -> None:
        obs = [turn(grounded=False, outcome="refresh")]
        self.assertIsNotNone(
            check_trajectory_invariant(obs, InvariantSpec(kind="never_invented")),
        )
        self.assertIsNone(
            check_trajectory_invariant(
                obs,
                InvariantSpec(kind="never_invented",
                              expected=["ask", "reject", "defer", "refresh"]),
            ),
        )

    def test_a_host_that_does_not_report_grounding_abstains(self) -> None:
        obs = [turn(outcome="answer"), turn(outcome="answer")]
        self.assertIsNone(
            check_trajectory_invariant(obs, InvariantSpec(kind="never_invented")),
        )

    def test_outcome_comparison_is_case_and_space_insensitive(self) -> None:
        obs = [turn(grounded=False, outcome="  ASK ")]
        self.assertIsNone(
            check_trajectory_invariant(obs, InvariantSpec(kind="never_invented")),
        )


class TheIncidentSeedIsWellFormed(unittest.TestCase):
    def test_the_pattern_declares_both_laws(self) -> None:
        import json
        import pathlib

        root = pathlib.Path(__file__).resolve().parents[1]
        script = json.loads(
            (root / "incidents/patterns/act_reinterpreted_downstream/script.json")
            .read_text(encoding="utf-8"),
        )
        kinds = {i["kind"] for i in script["trajectory_invariants"]}
        self.assertEqual(kinds, {"act_stable", "never_invented"})
        self.assertTrue(script["turns"])
        for t in script["turns"]:
            self.assertEqual(t["actor"], "user")
        self.assertTrue(
            (root / "incidents/patterns/act_reinterpreted_downstream/INCIDENT.md")
            .exists(),
        )


if __name__ == "__main__":
    unittest.main()
