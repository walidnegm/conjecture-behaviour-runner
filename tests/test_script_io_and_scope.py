"""ScriptScope, JSON/YAML load, and multi-turn serialization."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from conjecture_behaviour_runner import (
    CognitionPin,
    ConjectureScript,
    DialogueTurn,
    InvariantSpec,
    LlmMode,
    NullControlPlaneAdapter,
    ScriptScope,
    load_script_json,
    run_script,
    script_from_dict,
)

_EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
_JSON = _EXAMPLES / "sole_continue_golden.json"
_YAML = _EXAMPLES / "sole_continue_golden.yaml"


class ScriptScopeAndIoTests(unittest.TestCase):
    def test_scope_roundtrip_and_artifact(self) -> None:
        scope = ScriptScope(
            in_scope=("sole-continue mid-flight",),
            out_of_scope=("model scoring",),
            expected_refusal=("illegal restart",),
        )
        script = ConjectureScript(
            script_id="s",
            description="scope smoke",
            conversation_id="c",
            scope=scope,
            tags=("t",),
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
        self.assertTrue(result.passed)
        self.assertEqual(result.artifact["scope"]["in_scope"], ["sole-continue mid-flight"])
        self.assertEqual(result.artifact["tags"], ["t"])

    def test_script_from_dict_roundtrip(self) -> None:
        raw = {
            "script_id": "rt",
            "description": "d",
            "conversation_id": "c",
            "scope": {
                "in_scope": ["a"],
                "out_of_scope": ["b"],
                "expected_refusal": ["c"],
            },
            "turns": [
                {
                    "actor": "user",
                    "user_text": "hello",
                    "pin": {"task_intent": "continue"},
                    "invariants": [{"kind": "always_true"}],
                }
            ],
        }
        script = script_from_dict(raw)
        self.assertEqual(script.script_id, "rt")
        self.assertIsNotNone(script.scope)
        assert script.scope is not None
        self.assertEqual(list(script.scope.in_scope), ["a"])
        self.assertEqual(script.turns[0].pin.task_intent, "continue")
        again = script_from_dict(script.to_dict())
        self.assertEqual(again.to_dict()["script_id"], "rt")
        self.assertEqual(again.to_dict()["scope"]["expected_refusal"], ["c"])

    def test_load_sole_continue_json_example(self) -> None:
        self.assertTrue(_JSON.is_file(), f"missing {_JSON}")
        script = load_script_json(str(_JSON))
        self.assertEqual(script.script_id, "sole_continue_owns_the_turn")
        self.assertEqual(len(script.turns), 2)
        self.assertIsNotNone(script.scope)
        assert script.scope is not None
        self.assertTrue(script.scope.in_scope)
        kinds = [inv.kind for inv in script.turns[1].invariants]
        self.assertIn("exclusive_owner", kinds)
        self.assertIn("extra_true", kinds)
        # Null adapter cannot satisfy real invariants — structure only.
        result = run_script(
            ConjectureScript(
                script_id=script.script_id,
                description=script.description,
                conversation_id=script.conversation_id,
                turns=[
                    DialogueTurn(
                        user_text=t.user_text,
                        pin=t.pin,
                        invariants=[InvariantSpec(kind="always_true")],
                    )
                    for t in script.turns
                ],
                scope=script.scope,
            ),
            adapter=NullControlPlaneAdapter(),
            llm_mode=LlmMode.STUB,
        )
        self.assertTrue(result.passed)
        self.assertIn("scope", result.artifact)

    def test_load_sole_continue_yaml_when_pyyaml_present(self) -> None:
        try:
            import yaml  # noqa: F401
        except ImportError:
            self.skipTest("PyYAML not installed")
        from conjecture_behaviour_runner import load_script_yaml

        self.assertTrue(_YAML.is_file())
        script = load_script_yaml(str(_YAML))
        from_json = load_script_json(str(_JSON))
        self.assertEqual(script.script_id, from_json.script_id)
        self.assertEqual(len(script.turns), len(from_json.turns))
        self.assertEqual(
            script.turns[1].invariants[-1].kind,
            from_json.turns[1].invariants[-1].kind,
        )

    def test_json_file_parses_as_json(self) -> None:
        data = json.loads(_JSON.read_text(encoding="utf-8"))
        self.assertEqual(data["script_id"], "sole_continue_owns_the_turn")


if __name__ == "__main__":
    unittest.main()
