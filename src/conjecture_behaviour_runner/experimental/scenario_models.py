"""Scenario contract — Pydantic models.

The single source of truth for what a scenario YAML can look like. The runner
loads YAML, validates it through these models, and refuses to execute anything
that doesn't fit.

JSON Schema can be exported from the top-level `Scenario.model_json_schema()`
and is checked into `schema.json` for LLM extractors that don't run Python.

Design notes (per the 2026-05-05 framework strip-down):

- Three terminal-state buckets — `expected`, `tolerated_degraded`, `failure[]`
  with `required_graceful_handling`. A failed run is not a success; the
  framework refuses to call `simulation_run_failed` an "allowed outcome of
  success" — failures are graceful-handling contracts, not success states.

- Evidence is typed: `{type, path, assertion, confidence}`. A bare file path
  is no longer enough.

- `nondeterminism.allowed_outcomes` + `nondeterminism.required_invariants`
  is load-bearing for agentic flows; deterministic steps just set
  `nondeterminism.type=none` and leave the lists empty.

- `Scope` replaces ODD with `in_scope` / `out_of_scope` / `expected_refusal`
  — same idea, less imported AV vocabulary.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ── Enums (the scenario YAML uses these as string values) ──────────────


class Actor(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class WaitType(str, Enum):
    """How the runner knows a step has settled."""
    RENDER_WAIT = "render_wait"
    NETWORK_WAIT = "network_wait"
    ASYNC_JOB_WAIT = "async_job_wait"
    STREAM_WAIT = "stream_wait"
    HUMAN_CONFIRMATION_WAIT = "human_confirmation_wait"


class NondeterminismType(str, Enum):
    """Why a step might land in different observable outcomes per run."""
    NONE = "none"
    ASYNC = "async"
    LLM = "llm"
    STOCHASTIC = "stochastic"
    AGENTIC = "agentic"
    RACE = "race"


class EvidenceType(str, Enum):
    """The kind of artifact that proves a step happened."""
    REGRESSION_TEST = "regression_test"
    API_CONTRACT = "api_contract"
    UI_COMPONENT = "ui_component"
    DB_ASSERTION = "db_assertion"
    EVENT_LOG = "event_log"


class EvidenceConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ── Leaf models ────────────────────────────────────────────────────────


class WaitPolicy(BaseModel):
    """Temporal layer — how long to wait for a step to settle."""
    model_config = ConfigDict(extra="forbid")

    type: WaitType
    settle_condition: str = Field(
        description="Named condition the runner watches (e.g., 'agent_turn_complete', 'scenarios_list_visible')."
    )
    timeout_ms: int = Field(gt=0)
    poll_interval_ms: Optional[int] = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _async_or_stream_should_poll(self) -> "WaitPolicy":
        if self.type in (WaitType.ASYNC_JOB_WAIT, WaitType.STREAM_WAIT) and self.poll_interval_ms is None:
            # Not strictly required — some streams emit final events without polling — but we
            # surface the gap so callers can either set it or explicitly accept event-driven mode.
            object.__setattr__(self, "poll_interval_ms", 1000)
        return self


class Nondeterminism(BaseModel):
    """Agentic / stochastic layer — what outcomes are legal and what must hold across them."""
    model_config = ConfigDict(extra="forbid")

    type: NondeterminismType = NondeterminismType.NONE
    allowed_outcomes: list[str] = Field(default_factory=list)
    required_invariants: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _none_means_no_alternates(self) -> "Nondeterminism":
        if self.type == NondeterminismType.NONE and self.allowed_outcomes:
            raise ValueError(
                "nondeterminism.type='none' must not set allowed_outcomes — "
                "deterministic steps land in postconditions, not in an outcome set."
            )
        return self


class Evidence(BaseModel):
    """What proves a step happened. Typed — bare paths are not enough."""
    model_config = ConfigDict(extra="forbid")

    type: EvidenceType
    path: str
    assertion: Optional[str] = None
    confidence: EvidenceConfidence = EvidenceConfidence.MEDIUM


class FailureState(BaseModel):
    """A non-success terminal state plus its graceful-handling contract."""
    model_config = ConfigDict(extra="forbid")

    state: str
    required_graceful_handling: list[str] = Field(default_factory=list)


class TerminalStates(BaseModel):
    """Three buckets — separates success from degraded-success from failure-with-required-handling."""
    model_config = ConfigDict(extra="forbid")

    expected: list[str] = Field(default_factory=list)
    tolerated_degraded: list[str] = Field(default_factory=list)
    failure: list[FailureState] = Field(default_factory=list)


class ExecutionProfile(BaseModel):
    """Envelope the scenario must hold under — device, network, tier, SLA."""
    model_config = ConfigDict(extra="forbid")

    id: str
    device: str
    viewport: dict[str, int] = Field(default_factory=dict)
    network: str
    sla: dict[str, int] = Field(default_factory=dict)
    feature_flags: dict[str, Any] = Field(default_factory=dict)
    tenant_tier: Optional[str] = None
    input_mode: Optional[str] = None
    browser: Optional[str] = None


class Scope(BaseModel):
    """Scenario-class metadata — the input space the system claims to handle.

    Replaces ODD with plain language. `in_scope` = supported inputs;
    `out_of_scope` = unsupported (system should refuse gracefully);
    `expected_refusal` = adversarial probes the system must reject.
    """
    model_config = ConfigDict(extra="forbid")

    in_scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    expected_refusal: list[str] = Field(default_factory=list)


class Step(BaseModel):
    """One unit of forward motion in the scenario."""
    model_config = ConfigDict(extra="forbid")

    id: str
    actor: Actor
    control_point: str
    maneuver: str
    entry_surface: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    preconditions: list[str] = Field(default_factory=list)
    blocked_conditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    wait: WaitPolicy
    nondeterminism: Nondeterminism = Field(default_factory=Nondeterminism)
    evidence: list[Evidence] = Field(default_factory=list)


# ── Top-level scenario ─────────────────────────────────────────────────


class Scenario(BaseModel):
    """A goal-directed route through the experience. Validates against schema.json."""
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    scenario_class: Optional[str] = None
    scope: Optional[Scope] = None
    goal_state: list[str] = Field(min_length=1)
    initial_state: list[str] = Field(default_factory=list)
    execution_profiles: list[ExecutionProfile] = Field(min_length=1)
    steps: list[Step] = Field(min_length=1)
    terminal_states: TerminalStates = Field(default_factory=TerminalStates)

    @model_validator(mode="after")
    def _profile_ids_unique(self) -> "Scenario":
        ids = [p.id for p in self.execution_profiles]
        if len(ids) != len(set(ids)):
            raise ValueError(f"execution_profile ids must be unique: {ids}")
        return self

    @model_validator(mode="after")
    def _step_ids_unique(self) -> "Scenario":
        ids = [s.id for s in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError(f"step ids must be unique: {ids}")
        return self

    @model_validator(mode="after")
    def _terminal_states_at_least_one_expected(self) -> "Scenario":
        if not self.terminal_states.expected:
            raise ValueError(
                "terminal_states.expected must list at least one canonical-success state. "
                "If success is genuinely undefined for this scenario, consider whether "
                "the scenario itself has a goal."
            )
        return self


def load_scenario_from_yaml(path: str) -> Scenario:
    """Load and validate a scenario YAML. Raises ValidationError on failure.

    Requires optional dependency ``PyYAML``::

        pip install conjecture-behaviour-runner[scenarios]
    """
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - depends on install
        raise ImportError(
            "load_scenario_from_yaml requires PyYAML — install the optional "
            "extra: pip install conjecture-behaviour-runner[scenarios]"
        ) from exc
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return Scenario.model_validate(data)
