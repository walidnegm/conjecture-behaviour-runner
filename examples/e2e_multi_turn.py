#!/usr/bin/env python3
"""End-to-end: multi-turn agentic conversation + Conjecture contracts.

Uses the in-repo MiniChatApp (path-faithful Act via ``handle``) — our own tiny
control plane — so you can see the full loop without LangGraph/Temporal installed.

Conversation (what the user says):
  1) "cost out the onboarding workflow"   → start sole-continue mid-flight
  2) "make the volume 10k"                → continue on the same workflow

Expected ground truth after turn 2 (independent of reply wording):
  - exclusive_owner == cost_out
  - pin workflow_id still wf_1
  - blocks_resolve is True (no ambient re-resolve)

Then the same golden is run against planted bugs — Conjecture must fail them.

Run:
  pip install -e ".[dev]"
  python examples/e2e_multi_turn.py
"""
from __future__ import annotations

import json
import sys

from conjecture_behaviour_runner import LlmMode, run_script
from conjecture_behaviour_runner.path_faithful import (
    MiniAppAdapter,
    MiniChatApp,
    sole_continue_script,
)


def _banner(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def run_conversation(*, bug: str | None, label: str) -> bool:
    app = MiniChatApp(bug=bug)
    adapter = MiniAppAdapter(app)
    script = sole_continue_script()

    _banner(f"{label}  (bug={bug!r})")
    print("Script:", script.script_id)
    print("Multi-turn conversation (Act goes through app.handle):")
    for i, turn in enumerate(script.turns):
        print(f"  [{i + 1}] user: {turn.user_text!r}")
        print(f"      pin:  task_intent={turn.pin.task_intent!r}" if turn.pin else "")
        kinds = [inv.kind for inv in turn.invariants]
        if kinds:
            print(f"      expect: {', '.join(kinds)}")

    result = run_script(script, adapter=adapter, llm_mode=LlmMode.STUB)

    print()
    print("Messages the app actually received:", app.messages)
    print("Final ledger:")
    print(f"  exclusive_owner = {app.ledger.exclusive_owner!r}")
    print(f"  active_kind     = {app.ledger.active_kind!r}")
    print(f"  pins            = {app.ledger.pins!r}")
    print()
    if result.passed:
        print("RESULT: PASS — control-plane contracts held under pinned cognition (STUB).")
    else:
        print("RESULT: FAIL — verifier caught a contract break:")
        for f in result.failures:
            print(f"  • {f}")
    return result.passed


def main() -> int:
    print("Conjecture E2E — multi-turn agentic conversation")
    print("Green bar: owner + pin + blocks_resolve (not reply wording)")

    clean_ok = run_conversation(bug=None, label="1) Healthy mid-flight continue")
    dual_fail = not run_conversation(
        bug="owner_steal",
        label="2) Planted bug: owner_steal (continue reports front_door while task active)",
    )
    drop_fail = not run_conversation(
        bug="drop_pin",
        label="3) Planted bug: drop_pin (workflow_id cleared on continue)",
    )
    restart_fail = not run_conversation(
        bug="illegal_restart",
        label="4) Planted bug: illegal_restart (continue wipes the task)",
    )

    _banner("Summary")
    summary = {
        "healthy_passes": clean_ok,
        "owner_steal_caught": dual_fail,
        "drop_pin_caught": drop_fail,
        "illegal_restart_caught": restart_fail,
        "helpful": clean_ok and dual_fail and drop_fail and restart_fail,
    }
    print(json.dumps(summary, indent=2))
    print()
    if summary["helpful"]:
        print(
            "Conjecture is helpful here: wording could vary, but illegal ownership,\n"
            "lost identity, and silent restarts fail the same golden under pinned cognition."
        )
        return 0
    print("Unexpected: clean should pass and each planted bug should fail.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
