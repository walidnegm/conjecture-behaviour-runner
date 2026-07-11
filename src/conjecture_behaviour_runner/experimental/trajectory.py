"""Trajectory — what every runner emits.

The scenario contract is harness-agnostic; the trajectory shape is the bridge
between any runner (Playwright, Cypress, real-device cloud, custom) and the
downstream capture / diagnose / distribution-monitoring layers.

A trajectory is one observed run of one (scenario, profile) pair. Across N
trajectories of the same pair, the distribution of `observed_outcome` and the
union of `invariants_violated` are the regression surface — drift in either is
a regression even if every individual run "passed."
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class StepResult(BaseModel):
    """One step's observed result inside a trajectory."""
    model_config = ConfigDict(extra="forbid")

    step_id: str
    started_at: datetime
    finished_at: datetime
    latency_ms: int
    settled_within_sla: bool

    # Which `nondeterminism.allowed_outcomes` was reached.
    # For deterministic steps (`nondeterminism.type=none`), this is "deterministic".
    observed_outcome: str

    # Per-evidence results — each entry pairs an Evidence ref to its assertion outcome.
    evidence_results: list[dict[str, Any]] = Field(default_factory=list)

    # Invariant ledger — separated so distribution monitoring can aggregate cleanly.
    invariants_held: list[str] = Field(default_factory=list)
    invariants_violated: list[str] = Field(default_factory=list)

    # Free-form notes the runner can attach (e.g., the streamed reply text, the tool calls fired).
    runner_notes: dict[str, Any] = Field(default_factory=dict)

    # The verdict on this step. False if any required invariant was violated, even if an
    # allowed_outcome was reached.
    passed: bool


class Trajectory(BaseModel):
    """One observed run of one (scenario, profile) pair."""
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    profile_id: str
    run_id: str
    base_sha: Optional[str] = None  # the deployment SHA at run time (for code-dose attribution)

    started_at: datetime
    finished_at: datetime

    # The terminal-state bucket this run landed in. One of:
    #   - "expected"            canonical success
    #   - "tolerated_degraded"  success with caveats (retry-then-succeed, etc.)
    #   - "failure"              real regression — code under test is broken
    #   - "setup_error"          the *test environment* was wrong (e.g. test
    #                            tenant on free tier when scenario needs
    #                            enterprise). Surfaced separately from
    #                            "failure" so distribution monitoring can
    #                            triage them differently and CI can fail
    #                            with a different exit code.
    #   - "incomplete"           the run aborted mid-flight (driver crash,
    #                            network kill, etc.)
    terminal_bucket: str
    terminal_state: Optional[str] = None  # the specific named state reached, if any

    # When `terminal_bucket = "setup_error"`, this carries the human
    # explanation of what was wrong with the setup (tier mismatch, missing
    # seed data, etc.). Stays None for any other bucket.
    setup_error_message: Optional[str] = None

    overall_pass: bool
    step_results: list[StepResult] = Field(default_factory=list)

    # Pointers to external artifacts (screenshots, HAR file, DB snapshot diff, audit-event dump).
    # Absolute paths or URLs. Optional so a minimal runner can emit a trajectory without artifacts.
    artifact_urls: list[str] = Field(default_factory=list)


def write_trajectory(trajectory: Trajectory, path: str) -> None:
    """Persist a trajectory to disk as JSON. The scenario_runs DB table (when wired)
    can ingest this same JSON shape."""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(trajectory.model_dump_json(indent=2))
