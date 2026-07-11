"""Portable script model for multi-turn behaviour runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Sequence


@dataclass(frozen=True)
class InvariantSpec:
    """A required property that must hold after a turn (or whole script).

    ``kind`` is a stable code the adapter understands, e.g.:
    ``exclusive_owner``, ``pin_present``, ``front_door_blocked``,
    ``kind_equals``, ``owner_not``.
    """

    kind: str
    expected: Any = None
    reason: str = ""


@dataclass(frozen=True)
class LedgerEffect:
    """Deterministic state mutation applied after cognition, before invariants.

    Host adapters interpret ``op`` (e.g. ensure_task, set_pin, clear_task).
    """

    op: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DialogueTurn:
    """One step in a multi-turn behaviour script.

    Slice 0 is **user-centric**: ``user_text`` is the primary stimulus. The project
    design includes agent-initiated, agent-to-agent, and system/completion turns
    (see public README / experimental ``Actor``: user | agent | system). Optional
    ``actor`` defaults to ``"user"`` so later multi-actor scripts can land without
    renaming this field; adapters may ignore it until host drivers support it.
    """

    user_text: str
    pin: Optional[Any] = None  # CognitionPin | None
    effects: Sequence[LedgerEffect] = ()
    invariants: Sequence[InvariantSpec] = ()
    # Optional envelope of legal outcomes when cognition is live.
    allowed_outcomes: Sequence[str] = ()
    freeze_key: str = ""
    # user | agent | system — Slice 0 authors leave default; multi-actor is later.
    actor: str = "user"


@dataclass(frozen=True)
class ConjectureScript:
    """A multi-turn behaviour script (golden).

    Not limited to human chat in the full design: agent and system steps are in
    scope later. Slice 0 goldens are user-led by convention.
    """

    script_id: str
    description: str
    conversation_id: str
    turns: Sequence[DialogueTurn]
    # Initial ledger projection facts (host-defined keys).
    initial_context: dict[str, Any] = field(default_factory=dict)
    tags: Sequence[str] = ()


@dataclass
class RunResult:
    """Outcome of one script run."""

    script_id: str
    passed: bool
    failures: list[str] = field(default_factory=list)
    turn_results: list[dict[str, Any]] = field(default_factory=list)
    llm_mode: str = "stub"
    artifact: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "script_id": self.script_id,
            "passed": self.passed,
            "failures": list(self.failures),
            "turn_results": list(self.turn_results),
            "llm_mode": self.llm_mode,
            "artifact": dict(self.artifact),
        }
