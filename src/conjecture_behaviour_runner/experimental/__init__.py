"""Experimental — **Conjecture Scenario** language (+ observed trajectory shape).

Product naming (CBR-SPEC):

- **Conjecture Scenario** (this package) — flexible *description* of twists & turns,
  scope/ODD, nondeterminism envelopes, waits, evidence, profiles. Not tied to one driver.
- **Conjecture Script** (``ConjectureScript`` in ``script.py``) — *play-back form* a
  runner executes; usual CI golden.
- **Observed trajectory** — evidence of one run (``Trajectory`` here / ``RunResult``).

This is **not** “who runs the test.” Who runs a Scenario/Script is a separate choice:
CP runner (``run_script``), or later Playwright/other runners.
Bridge today: ``compile_scenario_to_script`` (Scenario → Script).

Import explicitly::

    from conjecture_behaviour_runner.experimental.scenario_models import Scenario
    from conjecture_behaviour_runner.experimental.trajectory import Trajectory

YAML loading requires::

    pip install conjecture-behaviour-runner[scenarios]

These modules may move or harden without a major version bump until promoted.
"""
from __future__ import annotations

__all__: list[str] = []
