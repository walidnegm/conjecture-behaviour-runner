"""Experimental — generalized trajectory *description* language (+ observed run shape).

This is **not** “who runs the test.” It is the flexible **input language** for scenarios:

- ``Scenario`` — actors, steps, scope/ODD, nondeterminism (allowed_outcomes +
  required_invariants), waits, evidence, execution profiles
- ``Trajectory`` — **observed** evidence of one run under one profile (output of a runner)
- ``schema.json`` — for LLM extractors / agents authoring description files

**Who runs a trajectory** is a separate choice: the stable control-plane runner
(``run_script`` on ``ConjectureScript``), or later Playwright/other runners.
Bridge today: ``compile_scenario_to_script`` (description → CP play-back form).

Import explicitly::

    from conjecture_behaviour_runner.experimental.scenario_models import Scenario
    from conjecture_behaviour_runner.experimental.trajectory import Trajectory

YAML loading requires::

    pip install conjecture-behaviour-runner[scenarios]

These modules may move or harden without a major version bump until promoted.
"""
from __future__ import annotations

__all__: list[str] = []
