"""Ratchet: the real CCP-binding adapter + golden scripts.

Skips when the Conversation Control Plane package is not importable (bare public
clone without the ``[control-plane]`` extra). Inside the monorepo, ``conftest.py``
puts the sibling extract on the path so these run.
"""
from __future__ import annotations

import unittest

try:
    from conversation_control_plane import multi_turn_stream_contract  # noqa: F401

    _CCP = True
except Exception:  # pragma: no cover - depends on install
    _CCP = False

from conjecture_behaviour_runner import (
    CognitionPin,
    ConjectureScript,
    DialogueTurn,
    InvariantSpec,
    LedgerEffect,
    LlmMode,
    run_script,
)


@unittest.skipUnless(_CCP, "conversation_control_plane not importable (install [control-plane])")
class ControlPlaneAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        from conjecture_behaviour_runner.contrib.control_plane import (
            ControlPlaneStreamAdapter,
            control_plane_golden_scripts,
        )

        self.adapter = ControlPlaneStreamAdapter()
        self.goldens = control_plane_golden_scripts()

    def test_all_goldens_pass(self) -> None:
        self.assertEqual(len(self.goldens), 3)
        for script in self.goldens:
            result = run_script(script, adapter=self.adapter, llm_mode=LlmMode.STUB)
            self.assertTrue(result.passed, f"{script.script_id}: {result.failures}")

    def test_checker_is_not_vacuous(self) -> None:
        # A golden that asserts the WRONG owner must FAIL — proves the adapter
        # actually observes ownership rather than rubber-stamping.
        bad = ConjectureScript(
            script_id="negative_wrong_owner",
            description="asserting the wrong owner should fail",
            conversation_id="conv_neg",
            turns=[
                DialogueTurn(
                    user_text="cost out the workflow",
                    pin=CognitionPin(task_intent="continue"),
                    effects=[
                        LedgerEffect(
                            op="begin_task",
                            payload={"agent": "cost", "kind": "cost_out",
                                     "phase": "sizing", "pins": {"workflow_id": "wf_1"}},
                        )
                    ],
                    invariants=[InvariantSpec(kind="exclusive_owner", expected="front_door")],
                ),
            ],
        )
        result = run_script(bad, adapter=self.adapter, llm_mode=LlmMode.STUB)
        self.assertFalse(result.passed)
        self.assertTrue(any("exclusive_owner" in f for f in result.failures))

    def test_detour_releases_stream(self) -> None:
        # Direct assertion of the supersede contract independent of the golden.
        script = ConjectureScript(
            script_id="detour_direct",
            description="detour supersedes",
            conversation_id="conv_d",
            turns=[
                DialogueTurn(
                    user_text="cost out",
                    pin=CognitionPin(task_intent="continue"),
                    effects=[
                        LedgerEffect(
                            op="begin_task",
                            payload={"agent": "cost", "kind": "cost_out",
                                     "phase": "sizing", "pins": {"workflow_id": "wf_1"}},
                        )
                    ],
                    invariants=[InvariantSpec(kind="exclusive_owner", expected="cost_out")],
                ),
                DialogueTurn(
                    user_text="what is a scorecard?",
                    pin=CognitionPin(task_intent="detour"),
                    invariants=[
                        InvariantSpec(kind="owner_not", expected="cost_out"),
                        InvariantSpec(kind="extra_false", expected="blocks_resolve"),
                    ],
                    allowed_outcomes=["detour_superseded"],
                ),
            ],
        )
        result = run_script(script, adapter=self.adapter, llm_mode=LlmMode.STUB)
        self.assertTrue(result.passed, result.failures)


if __name__ == "__main__":
    unittest.main()
