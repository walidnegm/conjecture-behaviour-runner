"""Portable script model for multi-turn behaviour runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence


@dataclass(frozen=True)
class ScriptScope:
    """Mini-ODD / scope metadata for a script (scenario-class claim).

    Same plain-language fields as experimental Scenario ``Scope`` and SOTIF-style
    ODD: what the script claims the system handles, refuses, or must reject.
    Slice 0 treats this as **metadata on the claim** (surfaced in run artifacts
    and docs). Automated in-/out-of-scope probe generation is a later slice.
    """

    in_scope: Sequence[str] = ()
    out_of_scope: Sequence[str] = ()
    expected_refusal: Sequence[str] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "in_scope": list(self.in_scope),
            "out_of_scope": list(self.out_of_scope),
            "expected_refusal": list(self.expected_refusal),
        }

    @classmethod
    def from_dict(cls, data: Optional[Mapping[str, Any]]) -> Optional["ScriptScope"]:
        if not data:
            return None
        return cls(
            in_scope=tuple(data.get("in_scope") or ()),
            out_of_scope=tuple(data.get("out_of_scope") or ()),
            expected_refusal=tuple(data.get("expected_refusal") or ()),
        )


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

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"kind": self.kind}
        if self.expected is not None:
            d["expected"] = self.expected
        if self.reason:
            d["reason"] = self.reason
        return d

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "InvariantSpec":
        return cls(
            kind=str(data["kind"]),
            expected=data.get("expected"),
            reason=str(data.get("reason") or ""),
        )


@dataclass(frozen=True)
class LedgerEffect:
    """Deterministic state mutation applied after cognition, before invariants.

    Host adapters interpret ``op`` (e.g. ensure_task, set_pin, clear_task).
    """

    op: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"op": self.op, "payload": dict(self.payload)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LedgerEffect":
        return cls(op=str(data["op"]), payload=dict(data.get("payload") or {}))


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
    pin: Optional[Any] = None  # CognitionPin | dict | None
    effects: Sequence[LedgerEffect] = ()
    invariants: Sequence[InvariantSpec] = ()
    # Optional envelope of legal outcomes when cognition is live.
    allowed_outcomes: Sequence[str] = ()
    # Outcome → extra invariants that apply only when that outcome is observed.
    outcome_invariants: Mapping[str, Sequence[InvariantSpec]] = field(
        default_factory=dict
    )
    freeze_key: str = ""
    # user | agent | system — Slice 0 authors leave default; multi-actor is later.
    actor: str = "user"

    def to_dict(self) -> dict[str, Any]:
        from conjecture_behaviour_runner.pins import CognitionPin

        pin_out: Any = None
        if self.pin is None:
            pin_out = None
        elif isinstance(self.pin, CognitionPin):
            pin_out = self.pin.to_dict()
        elif isinstance(self.pin, Mapping):
            pin_out = dict(self.pin)
        else:
            pin_out = self.pin
        d: dict[str, Any] = {
            "user_text": self.user_text,
            "actor": self.actor,
            "effects": [e.to_dict() for e in self.effects],
            "invariants": [i.to_dict() for i in self.invariants],
            "allowed_outcomes": list(self.allowed_outcomes),
            "outcome_invariants": {
                k: [inv.to_dict() for inv in v]
                for k, v in dict(self.outcome_invariants or {}).items()
            },
        }
        if pin_out is not None:
            d["pin"] = pin_out
        if self.freeze_key:
            d["freeze_key"] = self.freeze_key
        return d

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DialogueTurn":
        from conjecture_behaviour_runner.pins import CognitionPin

        pin_raw = data.get("pin")
        pin: Any = None
        if pin_raw is not None:
            pin = (
                CognitionPin.from_dict(pin_raw)
                if isinstance(pin_raw, Mapping)
                else pin_raw
            )
        effects = tuple(
            LedgerEffect.from_dict(e) for e in (data.get("effects") or ())
        )
        invariants = tuple(
            InvariantSpec.from_dict(i) for i in (data.get("invariants") or ())
        )
        oi_raw = data.get("outcome_invariants") or {}
        outcome_invariants: dict[str, tuple[InvariantSpec, ...]] = {}
        if isinstance(oi_raw, Mapping):
            for ok, specs in oi_raw.items():
                outcome_invariants[str(ok)] = tuple(
                    InvariantSpec.from_dict(s) for s in (specs or ())
                )
        return cls(
            user_text=str(data.get("user_text") or ""),
            pin=pin,
            effects=effects,
            invariants=invariants,
            allowed_outcomes=tuple(data.get("allowed_outcomes") or ()),
            outcome_invariants=outcome_invariants,
            freeze_key=str(data.get("freeze_key") or ""),
            actor=str(data.get("actor") or "user"),
        )


@dataclass(frozen=True)
class ConjectureScript:
    """A multi-turn behaviour script (golden).

    Not limited to human chat in the full design: agent and system steps are in
    scope later. Slice 0 goldens are user-led by convention.
    Optional ``scope`` is mini-ODD metadata for the claim (see ``ScriptScope``).
    """

    script_id: str
    description: str
    conversation_id: str
    turns: Sequence[DialogueTurn]
    # Initial ledger projection facts (host-defined keys).
    initial_context: dict[str, Any] = field(default_factory=dict)
    tags: Sequence[str] = ()
    scope: Optional[ScriptScope] = None
    # Cross-turn verifier (evaluated after all turns) — see temporal.py.
    trajectory_invariants: Sequence[InvariantSpec] = ()

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "script_id": self.script_id,
            "description": self.description,
            "conversation_id": self.conversation_id,
            "turns": [t.to_dict() for t in self.turns],
            "initial_context": dict(self.initial_context),
            "tags": list(self.tags),
            "trajectory_invariants": [i.to_dict() for i in self.trajectory_invariants],
        }
        if self.scope is not None:
            d["scope"] = self.scope.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ConjectureScript":
        turns = tuple(DialogueTurn.from_dict(t) for t in (data.get("turns") or ()))
        if not turns:
            raise ValueError("ConjectureScript requires at least one turn")
        traj = tuple(
            InvariantSpec.from_dict(i)
            for i in (data.get("trajectory_invariants") or ())
        )
        return cls(
            script_id=str(data["script_id"]),
            description=str(data.get("description") or ""),
            conversation_id=str(data.get("conversation_id") or ""),
            turns=turns,
            initial_context=dict(data.get("initial_context") or {}),
            tags=tuple(data.get("tags") or ()),
            scope=ScriptScope.from_dict(data.get("scope")),
            trajectory_invariants=traj,
        )


def script_from_dict(data: Mapping[str, Any]) -> ConjectureScript:
    """Build a ``ConjectureScript`` from a JSON/YAML-loaded mapping."""
    return ConjectureScript.from_dict(data)


def load_script_json(path: str) -> ConjectureScript:
    """Load a script golden from a JSON file on disk."""
    import json
    from pathlib import Path

    text = Path(path).read_text(encoding="utf-8")
    return script_from_dict(json.loads(text))


def load_script_yaml(path: str) -> ConjectureScript:
    """Load a script golden from YAML (requires PyYAML / ``[scenarios]`` extra)."""
    from pathlib import Path

    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "YAML script loading requires PyYAML — "
            "pip install conjecture-behaviour-runner[scenarios]"
        ) from exc
    text = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, Mapping):
        raise ValueError(f"YAML root must be a mapping, got {type(data)!r}")
    return script_from_dict(data)


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
