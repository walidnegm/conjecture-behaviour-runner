"""Harness contracts: allowed_outcomes non-vacuous; context None vs {}."""
from __future__ import annotations

import unittest
from typing import Any, Mapping, Optional

from conjecture_behaviour_runner import (
    CognitionPin,
    ConjectureScript,
    DialogueTurn,
    InvariantSpec,
    LlmMode,
    TurnObservation,
    run_script,
)
from conjecture_behaviour_runner.script import LedgerEffect


class _OutcomeAdapter:
    def __init__(self, outcome: Optional[str], context_mode: str = "carry") -> None:
        self.outcome = outcome
        self.context_mode = context_mode
        self.seen: list[dict[str, Any]] = []

    def apply_effect(self, context: dict[str, Any], effect: LedgerEffect) -> dict[str, Any]:
        return dict(context)

    def observe_turn(
        self,
        *,
        context: dict[str, Any],
        user_text: str,
        pin: Any,
    ) -> TurnObservation:
        self.seen.append(dict(context))
        if self.context_mode == "none":
            ctx: Optional[dict[str, Any]] = None
        elif self.context_mode == "clear":
            ctx = {}
        else:
            ctx = dict(context)
            ctx["touched"] = user_text
        return TurnObservation(
            exclusive_owner=None,
            active_kind=None,
            pins={},
            context=ctx,
            observed_outcome=self.outcome,
            extras={},
        )

    def check_invariant(
        self,
        *,
        observation: TurnObservation,
        context: Mapping[str, Any],
        spec: InvariantSpec,
    ) -> Optional[str]:
        if spec.kind == "always_true":
            return None
        return f"unexpected {spec.kind}"


class HarnessContractTests(unittest.TestCase):
    def test_allowed_outcomes_fail_when_observed_outcome_none(self) -> None:
        script = ConjectureScript(
            script_id="vacuous",
            description="must not pass without an outcome",
            conversation_id="c",
            turns=[
                DialogueTurn(
                    user_text="x",
                    pin=CognitionPin(),
                    allowed_outcomes=["continue_owned"],
                    invariants=[InvariantSpec(kind="always_true")],
                ),
            ],
        )
        result = run_script(script, adapter=_OutcomeAdapter(None), llm_mode=LlmMode.STUB)
        self.assertFalse(result.passed)
        self.assertTrue(any("observed_outcome is None" in f for f in result.failures))

    def test_allowed_outcomes_membership(self) -> None:
        script = ConjectureScript(
            script_id="member",
            description="d",
            conversation_id="c",
            turns=[
                DialogueTurn(
                    user_text="x",
                    pin=CognitionPin(),
                    allowed_outcomes=["continue_owned"],
                    invariants=[InvariantSpec(kind="always_true")],
                ),
            ],
        )
        ok = run_script(
            script, adapter=_OutcomeAdapter("continue_owned"), llm_mode=LlmMode.STUB
        )
        self.assertTrue(ok.passed, ok.failures)
        bad = run_script(
            script, adapter=_OutcomeAdapter("other"), llm_mode=LlmMode.STUB
        )
        self.assertFalse(bad.passed)

    def test_context_none_keeps_prior(self) -> None:
        script = ConjectureScript(
            script_id="ctx_none",
            description="d",
            conversation_id="c",
            initial_context={"seed": 1},
            turns=[
                DialogueTurn(
                    user_text="a",
                    pin=CognitionPin(),
                    invariants=[InvariantSpec(kind="always_true")],
                ),
                DialogueTurn(
                    user_text="b",
                    pin=CognitionPin(),
                    invariants=[InvariantSpec(kind="always_true")],
                ),
            ],
        )
        adapter = _OutcomeAdapter("null_adapter", context_mode="none")
        result = run_script(script, adapter=adapter, llm_mode=LlmMode.STUB)
        self.assertTrue(result.passed, result.failures)
        # Second turn still saw seed=1
        self.assertEqual(adapter.seen[1].get("seed"), 1)

    def test_context_empty_dict_clears(self) -> None:
        script = ConjectureScript(
            script_id="ctx_clear",
            description="d",
            conversation_id="c",
            initial_context={"seed": 1},
            turns=[
                DialogueTurn(
                    user_text="a",
                    pin=CognitionPin(),
                    invariants=[InvariantSpec(kind="always_true")],
                ),
                DialogueTurn(
                    user_text="b",
                    pin=CognitionPin(),
                    invariants=[InvariantSpec(kind="always_true")],
                ),
            ],
        )
        adapter = _OutcomeAdapter("null_adapter", context_mode="clear")
        result = run_script(script, adapter=adapter, llm_mode=LlmMode.STUB)
        self.assertTrue(result.passed, result.failures)
        # After turn 0 cleared, turn 1 must not see seed
        self.assertNotIn("seed", adapter.seen[1])


if __name__ == "__main__":
    unittest.main()
