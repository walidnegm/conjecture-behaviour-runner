"""Cognition providers — resolve / record / replay pins independently of the verifier.

Slice 0 goldens still put pins on turns. This module makes the *mode system* real:
stub, freeze (disk), and record (disk) with a portable freeze artifact format.
Local/cloud modes remain host-supplied via a custom CognitionProvider.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Protocol, runtime_checkable

from conjecture_behaviour_runner.pins import CognitionPin
from conjecture_behaviour_runner.script import DialogueTurn


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CognitionDecision:
    """Resolved cognition for one turn (portable)."""

    pin: CognitionPin
    source: str  # stub | freeze | record | host
    freeze_key: str = ""
    model_id: str = ""
    prompt_hash: str = ""
    schema_version: str = "1"
    temperature: Optional[float] = None
    seed: Optional[int] = None
    raw_output: Optional[str] = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pin": self.pin.to_dict(),
            "source": self.source,
            "freeze_key": self.freeze_key,
            "model_id": self.model_id,
            "prompt_hash": self.prompt_hash,
            "schema_version": self.schema_version,
            "temperature": self.temperature,
            "seed": self.seed,
            "raw_output": self.raw_output,
            "evidence": dict(self.evidence),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CognitionDecision":
        pin_raw = data.get("pin") or {}
        pin = (
            CognitionPin.from_dict(pin_raw)
            if isinstance(pin_raw, Mapping)
            else CognitionPin()
        )
        return cls(
            pin=pin,
            source=str(data.get("source") or "host"),
            freeze_key=str(data.get("freeze_key") or ""),
            model_id=str(data.get("model_id") or ""),
            prompt_hash=str(data.get("prompt_hash") or ""),
            schema_version=str(data.get("schema_version") or "1"),
            temperature=data.get("temperature"),
            seed=data.get("seed"),
            raw_output=data.get("raw_output"),
            evidence=dict(data.get("evidence") or {}),
        )


@dataclass
class FreezeArtifact:
    """On-disk freeze record for one cognition decision."""

    freeze_key: str
    decision: CognitionDecision
    recorded_at: str = field(default_factory=_utc_now_iso)
    script_id: str = ""
    turn_index: int = -1
    user_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "freeze_key": self.freeze_key,
            "decision": self.decision.to_dict(),
            "recorded_at": self.recorded_at,
            "script_id": self.script_id,
            "turn_index": self.turn_index,
            "user_text": self.user_text,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FreezeArtifact":
        return cls(
            freeze_key=str(data.get("freeze_key") or ""),
            decision=CognitionDecision.from_dict(data.get("decision") or {}),
            recorded_at=str(data.get("recorded_at") or _utc_now_iso()),
            script_id=str(data.get("script_id") or ""),
            turn_index=int(data.get("turn_index") if data.get("turn_index") is not None else -1),
            user_text=str(data.get("user_text") or ""),
        )


class FreezeStore:
    """JSON file store: ``{dir}/{freeze_key}.json``."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, freeze_key: str) -> Path:
        safe = freeze_key.replace("/", "_").replace("..", "_")
        return self.root / f"{safe}.json"

    def save(self, artifact: FreezeArtifact) -> Path:
        path = self.path_for(artifact.freeze_key)
        path.write_text(
            json.dumps(artifact.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return path

    def load(self, freeze_key: str) -> FreezeArtifact:
        path = self.path_for(freeze_key)
        if not path.is_file():
            raise FileNotFoundError(f"freeze artifact not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return FreezeArtifact.from_dict(data)

    def exists(self, freeze_key: str) -> bool:
        return self.path_for(freeze_key).is_file()


@runtime_checkable
class CognitionProvider(Protocol):
    """Controls probabilistic interpretation for a turn."""

    def resolve(
        self,
        turn: DialogueTurn,
        *,
        state: Mapping[str, Any],
        script_id: str = "",
        turn_index: int = 0,
    ) -> CognitionDecision:
        ...

    def record(
        self,
        decision: CognitionDecision,
        *,
        evidence: Mapping[str, Any] | None = None,
        script_id: str = "",
        turn_index: int = 0,
        user_text: str = "",
    ) -> Optional[FreezeArtifact]:
        ...

    def replay(self, freeze_key: str) -> CognitionDecision:
        ...


def _pin_from_turn(turn: DialogueTurn) -> Optional[CognitionPin]:
    if turn.pin is None:
        return None
    if isinstance(turn.pin, CognitionPin):
        return turn.pin
    if isinstance(turn.pin, Mapping):
        return CognitionPin.from_dict(turn.pin)
    raise TypeError(f"unsupported pin type: {type(turn.pin)!r}")


class StubCognitionProvider:
    """Resolve from the pin already on the turn (CI default)."""

    def resolve(
        self,
        turn: DialogueTurn,
        *,
        state: Mapping[str, Any],
        script_id: str = "",
        turn_index: int = 0,
    ) -> CognitionDecision:
        pin = _pin_from_turn(turn)
        if pin is None:
            pin = CognitionPin(task_intent="continue", reason="stub_default")
        key = turn.freeze_key or pin.freeze_key or f"{script_id}:t{turn_index}"
        return CognitionDecision(pin=pin, source="stub", freeze_key=key)

    def record(
        self,
        decision: CognitionDecision,
        *,
        evidence: Mapping[str, Any] | None = None,
        script_id: str = "",
        turn_index: int = 0,
        user_text: str = "",
    ) -> Optional[FreezeArtifact]:
        return None

    def replay(self, freeze_key: str) -> CognitionDecision:
        raise NotImplementedError("StubCognitionProvider has no freeze store")


class FreezeCognitionProvider:
    """Load decisions from a FreezeStore; fail closed on missing keys."""

    def __init__(self, store: FreezeStore) -> None:
        self.store = store

    def resolve(
        self,
        turn: DialogueTurn,
        *,
        state: Mapping[str, Any],
        script_id: str = "",
        turn_index: int = 0,
    ) -> CognitionDecision:
        key = turn.freeze_key or ""
        if not key:
            pin = _pin_from_turn(turn)
            if pin and pin.freeze_key:
                key = pin.freeze_key
        if not key:
            raise ValueError(
                "freeze mode requires turn.freeze_key (or pin.freeze_key)"
            )
        return self.replay(key)

    def record(
        self,
        decision: CognitionDecision,
        *,
        evidence: Mapping[str, Any] | None = None,
        script_id: str = "",
        turn_index: int = 0,
        user_text: str = "",
    ) -> Optional[FreezeArtifact]:
        return None

    def replay(self, freeze_key: str) -> CognitionDecision:
        art = self.store.load(freeze_key)
        dec = art.decision
        dec.source = "freeze"
        dec.freeze_key = freeze_key
        return dec


class RecordCognitionProvider:
    """Resolve like stub (or host delegate), then write freeze artifacts."""

    def __init__(
        self,
        store: FreezeStore,
        *,
        base: Optional[CognitionProvider] = None,
    ) -> None:
        self.store = store
        self.base = base or StubCognitionProvider()

    def resolve(
        self,
        turn: DialogueTurn,
        *,
        state: Mapping[str, Any],
        script_id: str = "",
        turn_index: int = 0,
    ) -> CognitionDecision:
        decision = self.base.resolve(
            turn, state=state, script_id=script_id, turn_index=turn_index
        )
        key = turn.freeze_key or decision.freeze_key or f"{script_id}:t{turn_index}"
        decision.freeze_key = key
        decision.source = "record"
        self.record(
            decision,
            script_id=script_id,
            turn_index=turn_index,
            user_text=turn.user_text,
        )
        return decision

    def record(
        self,
        decision: CognitionDecision,
        *,
        evidence: Mapping[str, Any] | None = None,
        script_id: str = "",
        turn_index: int = 0,
        user_text: str = "",
    ) -> Optional[FreezeArtifact]:
        if evidence:
            decision.evidence = {**decision.evidence, **dict(evidence)}
        key = decision.freeze_key or f"{script_id}:t{turn_index}"
        decision.freeze_key = key
        art = FreezeArtifact(
            freeze_key=key,
            decision=decision,
            script_id=script_id,
            turn_index=turn_index,
            user_text=user_text,
        )
        self.store.save(art)
        return art

    def replay(self, freeze_key: str) -> CognitionDecision:
        return FreezeCognitionProvider(self.store).replay(freeze_key)


def provider_for_mode(
    mode: str,
    *,
    freeze_dir: str | Path | None = None,
) -> CognitionProvider:
    """Factory for built-in providers from ``LlmMode`` values."""
    m = (mode or "stub").lower()
    if m == "stub":
        return StubCognitionProvider()
    if m == "freeze":
        if not freeze_dir:
            raise ValueError("freeze mode requires freeze_dir")
        return FreezeCognitionProvider(FreezeStore(freeze_dir))
    if m == "record":
        if not freeze_dir:
            raise ValueError("record mode requires freeze_dir")
        return RecordCognitionProvider(FreezeStore(freeze_dir))
    if m in ("local", "cloud"):
        raise ValueError(
            f"llm_mode={m!r} requires a host CognitionProvider "
            "(pass cognition=... to run_script)"
        )
    raise ValueError(f"unknown cognition mode {mode!r}")


__all__ = [
    "CognitionDecision",
    "CognitionProvider",
    "FreezeArtifact",
    "FreezeCognitionProvider",
    "FreezeStore",
    "RecordCognitionProvider",
    "StubCognitionProvider",
    "provider_for_mode",
]
