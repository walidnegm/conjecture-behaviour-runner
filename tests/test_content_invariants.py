"""Content invariants: stage-by-stage grading of what an agent said (0.1.7).

No model is called: the judge here is a fake. A DeepEval-backed judge is an
optional extra (``contrib.deepeval_judge``) and is exercised by hosts.
"""
from __future__ import annotations

import unittest

from conjecture_behaviour_runner import (
    CONTENT_INVARIANT_KINDS,
    BaseControlPlaneAdapter,
    GoldenCase,
    JudgeScore,
    TurnObservation,
    case_script,
    check_content_invariant,
    load_golden_cases,
    run_script,
    summarize,
)
from conjecture_behaviour_runner.script import InvariantSpec


class FakeJudge:
    def __init__(self, score: float) -> None:
        self.value = score
        self.calls = 0

    def score(self, metric, *, question, answer, contexts):
        self.calls += 1
        return JudgeScore(metric, self.value, f"fake {metric}")


def _obs(**extras):
    return TurnObservation(extras=dict(extras))


class StageInvariants(unittest.TestCase):
    def test_retrieve_includes_within_k(self) -> None:
        obs = _obs(retrieved_ids=["a", "b", "c"])
        self.assertIsNone(check_content_invariant(obs, InvariantSpec("retrieved_includes", {"id": "b", "k": 2})))
        self.assertIn("not in top 1", check_content_invariant(obs, InvariantSpec("retrieved_includes", {"id": "b", "k": 1})))

    def test_retrieve_excludes(self) -> None:
        obs = _obs(retrieved_ids=["a", "bad"])
        self.assertIn("forbidden", check_content_invariant(obs, InvariantSpec("retrieved_excludes", {"ids": ["bad"]})))
        self.assertIsNone(check_content_invariant(obs, InvariantSpec("retrieved_excludes", {"ids": ["bad"], "k": 1})))

    def test_missing_keys_fail_closed(self) -> None:
        self.assertIn("no 'retrieved_ids'", check_content_invariant(_obs(), InvariantSpec("retrieved_includes", "a")))
        self.assertIn("no 'selected_id'", check_content_invariant(_obs(), InvariantSpec("abstained")))

    def test_select_and_abstain(self) -> None:
        picked = _obs(selected_id="a")
        none = _obs(selected_id=None)
        self.assertIsNone(check_content_invariant(picked, InvariantSpec("selected_in", ["a", "b"])))
        self.assertIsNotNone(check_content_invariant(none, InvariantSpec("selected_in", ["a"])))
        self.assertIsNotNone(check_content_invariant(picked, InvariantSpec("selected_not_in", ["a"])))
        self.assertIsNone(check_content_invariant(none, InvariantSpec("selected_not_in", ["a"])))
        self.assertIsNone(check_content_invariant(none, InvariantSpec("abstained")))
        self.assertIsNotNone(check_content_invariant(picked, InvariantSpec("abstained")))

    def test_judged_fails_closed_without_a_judge(self) -> None:
        obs = _obs(answer="x", question="q", contexts=["c"])
        msg = check_content_invariant(obs, InvariantSpec("judged_at_least", {"metric": "faithfulness", "threshold": 0.5}))
        self.assertIn("no ContentJudge", msg)

    def test_judged_threshold_and_the_score_reaches_extras(self) -> None:
        spec = InvariantSpec("judged_at_least", {"metric": "faithfulness", "threshold": 0.7})
        ok = _obs(answer="x", question="q", contexts=["c"])
        self.assertIsNone(check_content_invariant(ok, spec, judge=FakeJudge(0.9)))
        self.assertEqual(ok.extras["judged"]["faithfulness"]["score"], 0.9)
        low = _obs(answer="x", question="q", contexts=["c"])
        self.assertIn("0.40 < 0.70", check_content_invariant(low, spec, judge=FakeJudge(0.4)))

    def test_unknown_kind_fails_closed(self) -> None:
        self.assertIn("unknown content", check_content_invariant(_obs(), InvariantSpec("retrieved_somewhere")))


class GoldenCases(unittest.TestCase):
    def test_a_case_is_validated(self) -> None:
        with self.assertRaises(ValueError):
            GoldenCase("x", "q")  # neither primary nor abstain
        with self.assertRaises(ValueError):
            GoldenCase("x", "q", primary="a", expect_abstain=True)
        with self.assertRaises(ValueError):
            GoldenCase("x", "q", primary="a", forbidden=("a",))
        with self.assertRaises(ValueError):
            load_golden_cases([{"id": "d", "utterance": "q", "primary": "a"}] * 2)

    def test_summarize_reports_forbidden_selection_on_its_own(self) -> None:
        cases = load_golden_cases([
            {"id": "1", "utterance": "q1", "primary": "a", "acceptable": ["b"], "forbidden": ["z"]},
            {"id": "2", "utterance": "q2", "primary": "c", "forbidden": ["z"]},
            {"id": "3", "utterance": "q3", "expect_abstain": True},
        ])
        out = summarize(cases, {"1": "b", "2": "z", "3": None})
        self.assertEqual(out["top1"], 0.0)
        self.assertEqual(out["acceptable_hit"], 0.5)
        self.assertEqual(out["forbidden_selection"], 0.5)
        self.assertEqual(out["forbidden_cases"], ["2"])
        self.assertEqual(out["abstention_correct"], 1.0)


class _Host(BaseControlPlaneAdapter):
    """A toy retrieval host: answers from a fixed index."""

    INDEX = {"throughput": ["throughput-analysis", "financial-model"], "weather": []}

    def apply_effect(self, context, effect):
        return dict(context)

    def observe_turn(self, *, context, user_text, pin):
        key = next((k for k in self.INDEX if k in user_text), "weather")
        ids = self.INDEX[key]
        sel = ids[0] if ids else None
        return TurnObservation(context=dict(context), extras={
            "question": user_text, "answer": f"about {sel}" if sel else "",
            "contexts": [f"text of {i}" for i in ids], "retrieved_ids": ids, "selected_id": sel,
        })


class ThroughTheHarness(unittest.TestCase):
    def test_a_case_runs_as_a_script_and_names_the_stage(self) -> None:
        host = _Host()
        host.content_judge = FakeJudge(0.95)
        case = GoldenCase("t", "explain throughput", primary="throughput-analysis",
                          forbidden=("financial-model",), judged={"faithfulness": 0.7})
        res = run_script(case_script(case), adapter=host)
        self.assertTrue(res.passed, res.failures)
        self.assertEqual(host.content_judge.calls, 1)
        self.assertIn("judged", res.turn_results[0]["observation"]["extras"])

        wrong = GoldenCase("w", "explain throughput", primary="financial-model-x",
                           forbidden=("throughput-analysis",))
        res = run_script(case_script(wrong, stages=("select",)), adapter=_Host())
        self.assertFalse(res.passed)
        self.assertTrue(any("selected_not_in" in f for f in res.failures))

    def test_deterministic_stages_never_call_the_judge(self) -> None:
        host = _Host()
        host.content_judge = FakeJudge(0.0)
        case = GoldenCase("t", "explain throughput", primary="throughput-analysis",
                          judged={"faithfulness": 0.7})
        res = run_script(case_script(case, stages=("retrieve", "select")), adapter=host)
        self.assertTrue(res.passed, res.failures)
        self.assertEqual(host.content_judge.calls, 0)

    def test_every_content_kind_is_handled(self) -> None:
        for kind in CONTENT_INVARIANT_KINDS:
            msg = check_content_invariant(_obs(), InvariantSpec(kind, {}))
            self.assertNotIn("unknown content", msg or "")


if __name__ == "__main__":
    unittest.main()
