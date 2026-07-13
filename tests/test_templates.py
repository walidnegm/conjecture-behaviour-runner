"""Portable parameterized templates — any kind vocabulary."""
from __future__ import annotations

import unittest

from conjecture_behaviour_runner import LlmMode, run_script
from conjecture_behaviour_runner.templates import (
    TemplateStreamAdapter,
    demo_scripts,
    reorient_keeps_owner_script,
    sole_continue_script,
)


class TemplateBuilderTests(unittest.TestCase):
    def test_requires_kind(self) -> None:
        with self.assertRaises(ValueError):
            sole_continue_script(kind="", exclusive_owner="x")

    def test_demo_scripts_pass_stub(self) -> None:
        adapter = TemplateStreamAdapter()
        for script in demo_scripts():
            result = run_script(script, adapter=adapter, llm_mode=LlmMode.STUB)
            self.assertTrue(
                result.passed,
                msg=f"{script.script_id}: {result.failures}",
            )

    def test_invoice_vocabulary_sole_continue(self) -> None:
        script = sole_continue_script(
            kind="invoice_intake",
            exclusive_owner="invoice_intake",
            pin_key="invoice_id",
            pin_value="inv_1",
        )
        result = run_script(
            script, adapter=TemplateStreamAdapter(), llm_mode=LlmMode.STUB
        )
        self.assertTrue(result.passed, result.failures)
        # Mid turns still owned.
        self.assertEqual(
            result.turn_results[2]["observation"]["exclusive_owner"],
            "invoice_intake",
        )
        # Detour yields.
        self.assertEqual(
            result.turn_results[4]["observation"]["exclusive_owner"],
            "front_door",
        )

    def test_reorient_keeps_owner(self) -> None:
        script = reorient_keeps_owner_script(
            kind="claim_review",
            exclusive_owner="claim_review",
            pin_key="claim_id",
            pin_value="cl_9",
        )
        result = run_script(
            script, adapter=TemplateStreamAdapter(), llm_mode=LlmMode.STUB
        )
        self.assertTrue(result.passed, result.failures)
        for tr in result.turn_results:
            self.assertEqual(
                tr["observation"]["exclusive_owner"],
                "claim_review",
                msg=tr.get("user_text"),
            )

    def test_false_complete_would_fail_reorient_script(self) -> None:
        """Planted bug: clear_task on 'reorient' turn fails owner invariant."""
        from conjecture_behaviour_runner.script import (
            ConjectureScript,
            DialogueTurn,
            InvariantSpec,
            LedgerEffect,
        )
        from conjecture_behaviour_runner.pins import CognitionPin

        begin = LedgerEffect(
            op="begin_task",
            payload={
                "agent": "demo",
                "kind": "demo_task",
                "phase": "mid",
                "pins": {"record_id": "r1"},
            },
        )
        # Bug: reorient applied as complete.
        false_complete = LedgerEffect(op="complete_task", payload={})
        script = ConjectureScript(
            script_id="planted_false_complete",
            description="must fail",
            conversation_id="conv_planted_false_complete",
            turns=(
                DialogueTurn(
                    user_text="start",
                    pin=CognitionPin(task_intent="continue"),
                    effects=(begin,),
                    invariants=(
                        InvariantSpec(kind="exclusive_owner", expected="demo_task"),
                    ),
                ),
                DialogueTurn(
                    user_text="i am fine with this",
                    pin=CognitionPin(task_intent="continue"),
                    effects=(false_complete,),
                    invariants=(
                        InvariantSpec(kind="exclusive_owner", expected="demo_task"),
                    ),
                ),
            ),
        )
        result = run_script(
            script, adapter=TemplateStreamAdapter(), llm_mode=LlmMode.STUB
        )
        self.assertFalse(result.passed)
        self.assertTrue(any("exclusive_owner" in f for f in result.failures))


if __name__ == "__main__":
    unittest.main()
