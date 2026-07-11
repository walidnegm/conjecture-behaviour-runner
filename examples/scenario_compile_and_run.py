#!/usr/bin/env python3
"""Load Conjecture Scenario YAML → compile to Script → run path-faithful mini-app.

Requires: pip install -e ".[dev,scenarios]"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from conjecture_behaviour_runner import LlmMode, run_script
from conjecture_behaviour_runner.compile_scenario import compile_scenario_to_script
from conjecture_behaviour_runner.experimental.scenario_models import (
    load_scenario_from_yaml,
)
from conjecture_behaviour_runner.path_faithful import MiniAppAdapter, MiniChatApp

HERE = Path(__file__).resolve().parent
SCENARIO = HERE / "scenario_sole_continue.yaml"


def main() -> int:
    if not SCENARIO.is_file():
        print(f"missing {SCENARIO}", file=sys.stderr)
        return 2

    print("1) Load + validate Conjecture Scenario")
    scenario = load_scenario_from_yaml(str(SCENARIO))
    print(f"   scenario_id={scenario.scenario_id!r}  steps={len(scenario.steps)}")
    print(f"   class={scenario.scenario_class!r}")
    print(f"   profiles={[p.id for p in scenario.execution_profiles]}")

    print("2) Compile → Conjecture Script (play-back form)")
    script = compile_scenario_to_script(
        scenario,
        profile_id="desktop_stub_cognition",
        conversation_id="conv_from_scenario",
    )
    print(f"   script_id={script.script_id!r}  turns={len(script.turns)}")
    for i, t in enumerate(script.turns):
        kinds = [inv.kind for inv in t.invariants]
        print(f"   turn[{i}] {t.user_text!r}  expect={kinds}")

    print("3) Run control-plane runner (healthy mini-app)")
    healthy = run_script(
        script,
        adapter=MiniAppAdapter(MiniChatApp()),
        llm_mode=LlmMode.STUB,
    )
    print(f"   passed={healthy.passed}  failures={healthy.failures}")

    print("4) Same Script against owner_steal bug (must FAIL)")
    stolen = run_script(
        script,
        adapter=MiniAppAdapter(MiniChatApp(bug="owner_steal")),
        llm_mode=LlmMode.STUB,
    )
    print(f"   passed={stolen.passed}  failures={stolen.failures}")

    summary = {
        "scenario_id": scenario.scenario_id,
        "compiled_script_id": script.script_id,
        "healthy_pass": healthy.passed,
        "owner_steal_caught": not stolen.passed,
        "helpful": healthy.passed and not stolen.passed,
    }
    print()
    print(json.dumps(summary, indent=2))
    return 0 if summary["helpful"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
