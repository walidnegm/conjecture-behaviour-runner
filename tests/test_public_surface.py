"""Portable package smoke — no monorepo imports."""
from __future__ import annotations

import unittest

from conjecture_behaviour_runner import (
    CognitionPin,
    ConjectureScript,
    DialogueTurn,
    InvariantSpec,
    LlmMode,
    NullControlPlaneAdapter,
    __version__,
    run_script,
)


class PublicSurfaceTests(unittest.TestCase):
    def test_version(self) -> None:
        self.assertTrue(__version__)

    def test_minimal_script_passes_null_adapter(self) -> None:
        script = ConjectureScript(
            script_id="t",
            description="unit",
            conversation_id="c",
            turns=[
                DialogueTurn(
                    user_text="x",
                    pin=CognitionPin(),
                    invariants=[InvariantSpec(kind="always_true")],
                ),
            ],
        )
        result = run_script(
            script, adapter=NullControlPlaneAdapter(), llm_mode=LlmMode.STUB
        )
        self.assertTrue(result.passed, result.to_dict())

    def test_null_adapter_fails_unknown_invariant(self) -> None:
        script = ConjectureScript(
            script_id="t2",
            description="unit",
            conversation_id="c",
            turns=[
                DialogueTurn(
                    user_text="x",
                    pin=CognitionPin(),
                    invariants=[
                        InvariantSpec(kind="exclusive_owner", expected="estimate_stream")
                    ],
                ),
            ],
        )
        result = run_script(
            script, adapter=NullControlPlaneAdapter(), llm_mode=LlmMode.STUB
        )
        self.assertFalse(result.passed)
        self.assertTrue(any("exclusive_owner" in f for f in result.failures))

    def test_pin_roundtrip(self) -> None:
        p = CognitionPin(task_intent="new_task", reason="r")
        p2 = CognitionPin.from_dict(p.to_dict())
        self.assertEqual(p2.task_intent, "new_task")
        self.assertEqual(p2.reason, "r")


if __name__ == "__main__":
    unittest.main()
