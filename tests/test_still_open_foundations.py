"""Foundations for previously open items: cognition, temporal, compile, path-faithful, CLI."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from conjecture_behaviour_runner import (
    CognitionPin,
    ConjectureScript,
    DialogueTurn,
    FreezeStore,
    InvariantSpec,
    LlmMode,
    NullControlPlaneAdapter,
    RecordCognitionProvider,
    FreezeCognitionProvider,
    run_script,
    check_trajectory_invariant,
)
from conjecture_behaviour_runner.path_faithful import (
    MiniAppAdapter,
    MiniChatApp,
    prove_planted_bugs,
    sole_continue_script,
)
from conjecture_behaviour_runner.compile_scenario import (
    compile_scenario_to_script,
    run_result_to_trajectory,
)
from conjecture_behaviour_runner.cli import main as cli_main
from conjecture_behaviour_runner.report import results_to_junit_xml, results_to_json_report


class CognitionFreezeTests(unittest.TestCase):
    def test_record_then_freeze_replay(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            store = FreezeStore(td)
            rec = RecordCognitionProvider(store)
            script = ConjectureScript(
                script_id="frz",
                description="d",
                conversation_id="c",
                turns=[
                    DialogueTurn(
                        user_text="hi",
                        pin=CognitionPin(task_intent="continue", reason="r1"),
                        freeze_key="k1",
                        invariants=[InvariantSpec(kind="always_true")],
                    ),
                ],
            )
            r1 = run_script(
                script,
                adapter=NullControlPlaneAdapter(),
                llm_mode=LlmMode.RECORD,
                cognition=rec,
                freeze_dir=td,
            )
            self.assertTrue(r1.passed, r1.failures)
            self.assertTrue(store.exists("k1"))

            # Replay without pin on turn
            frozen = ConjectureScript(
                script_id="frz2",
                description="d",
                conversation_id="c",
                turns=[
                    DialogueTurn(
                        user_text="hi",
                        freeze_key="k1",
                        invariants=[InvariantSpec(kind="always_true")],
                    ),
                ],
            )
            r2 = run_script(
                frozen,
                adapter=NullControlPlaneAdapter(),
                llm_mode=LlmMode.FREEZE,
                cognition=FreezeCognitionProvider(store),
            )
            self.assertTrue(r2.passed, r2.failures)
            cog = r2.turn_results[0]["cognition"]
            self.assertEqual(cog["source"], "freeze")
            self.assertEqual(cog["pin"]["task_intent"], "continue")


class TemporalVerifierTests(unittest.TestCase):
    def test_eventually_and_never(self) -> None:
        obs = [
            {"exclusive_owner": "front_door", "pins": {}, "observed_outcome": "a"},
            {"exclusive_owner": "cost_out", "pins": {"workflow_id": "1"}, "observed_outcome": "b"},
        ]
        self.assertIsNone(
            check_trajectory_invariant(
                obs, InvariantSpec(kind="eventually_exclusive_owner", expected="cost_out")
            )
        )
        self.assertIsNotNone(
            check_trajectory_invariant(
                obs, InvariantSpec(kind="never_exclusive_owner", expected="cost_out")
            )
        )
        self.assertIsNone(
            check_trajectory_invariant(
                obs, InvariantSpec(kind="pin_stable", expected="workflow_id")
            )
        )


class PathFaithfulTests(unittest.TestCase):
    def test_clean_and_planted_bugs(self) -> None:
        report = prove_planted_bugs()
        self.assertTrue(report["clean_passes"], report)
        self.assertTrue(report["dual_owner_caught"], report)
        self.assertTrue(report["drop_pin_caught"], report)
        self.assertTrue(report["illegal_restart_caught"], report)

    def test_outcome_specific_invariants(self) -> None:
        app = MiniChatApp()
        adapter = MiniAppAdapter(app)
        script = sole_continue_script()
        result = run_script(script, adapter=adapter, llm_mode=LlmMode.STUB)
        self.assertTrue(result.passed, result.failures)
        # trajectory invariants ran
        self.assertIn("observations", result.artifact)


class CompileScenarioTests(unittest.TestCase):
    def test_compile_and_trajectory_bridge(self) -> None:
        from conjecture_behaviour_runner.experimental.scenario_models import (
            Actor,
            ExecutionProfile,
            Nondeterminism,
            NondeterminismType,
            Scenario,
            Scope,
            Step,
            TerminalStates,
            WaitPolicy,
            WaitType,
        )

        scenario = Scenario(
            scenario_id="sc1",
            goal_state=["done"],
            scope=Scope(in_scope=["x"], out_of_scope=["y"], expected_refusal=["z"]),
            terminal_states=TerminalStates(expected=["done"]),
            execution_profiles=[
                ExecutionProfile(id="default", device="desktop", network="fast"),
            ],
            steps=[
                Step(
                    id="s0",
                    actor=Actor.USER,
                    control_point="chat",
                    maneuver="open",
                    wait=WaitPolicy(
                        type=WaitType.STREAM_WAIT,
                        settle_condition="agent_turn_complete",
                        timeout_ms=1000,
                    ),
                    nondeterminism=Nondeterminism(
                        type=NondeterminismType.AGENTIC,
                        allowed_outcomes=["continue_owned"],
                    ),
                    payload={
                        "user_text": "cost out x",
                        "pin": {"task_intent": "new_task"},
                        "invariants": [
                            {"kind": "exclusive_owner", "expected": "cost_out"},
                        ],
                    },
                ),
            ],
        )
        script = compile_scenario_to_script(scenario)
        self.assertEqual(script.script_id, "sc1")
        self.assertEqual(script.turns[0].user_text, "cost out x")
        self.assertIsNotNone(script.scope)

        app = MiniChatApp()
        result = run_script(
            script, adapter=MiniAppAdapter(app), llm_mode=LlmMode.STUB
        )
        traj = run_result_to_trajectory(result, scenario_id="sc1")
        self.assertEqual(traj.scenario_id, "sc1")
        self.assertEqual(len(traj.step_results), 1)
        self.assertEqual(traj.overall_pass, result.passed)


class CliAndReportTests(unittest.TestCase):
    def test_cli_path_faithful_prove(self) -> None:
        code = cli_main(["path-faithful", "--prove-bugs"])
        self.assertEqual(code, 0)

    def test_cli_version(self) -> None:
        code = cli_main(["--version"])
        self.assertEqual(code, 0)

    def test_junit_and_json_report(self) -> None:
        app = MiniChatApp()
        r = run_script(
            sole_continue_script(),
            adapter=MiniAppAdapter(app),
            llm_mode=LlmMode.STUB,
        )
        junit = results_to_junit_xml([r])
        self.assertIn("testcase", junit)
        rep = results_to_json_report([r])
        self.assertEqual(rep["passed"], 1)


if __name__ == "__main__":
    unittest.main()
