"""Cognition pins — portable structured labels (no free-form NL interpretation).

Entity *identity* (which workflow / project / run is in flight) is **not** a
field on this pin. Hosts project entity ids via ``TurnObservation.pins`` after
ledger apply — pin keys are host/control-plane defined (e.g. CCP uses
``workflow_id``). Host-specific router flags belong in ``extras``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Mapping

@dataclass(frozen=True)
class CognitionPin:
    """Pinned classifier/router output for one turn — portable control-plane labels.

    Core fields are generic multi-turn control signals. Host-specific router
    booleans and host-specific concepts go in ``extras`` (opaque to the harness).

    Values are **enums / flags**, not prose — code owns execution; the pin
    stands in for LLM cognition under ``LlmMode.STUB`` / ``FREEZE``.
    """

    # Portable turn-ownership signals (companion control-plane vocabulary).
    task_intent: str = "continue"  # continue | detour | new_task | abandon | handoff
    route_intent: str = "default"
    discovery_kind: str = "none"
    read_kind: str = "none"
    confidence: float = 0.95
    reason: str = "conjecture_stub"
    freeze_key: str = ""
    # Host-specific extras (opaque); not interpreted by the core harness.
    extras: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if d.get("extras") is None:
            d.pop("extras", None)
        return d

    def extra(self, key: str, default: Any = None) -> Any:
        """Read a host-specific flag from ``extras``."""
        if not self.extras:
            return default
        return self.extras.get(key, default)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CognitionPin":
        """Build a pin; unknown / host-private keys land in ``extras``.

        Accepts legacy Bot0 field names (``cost_estimate_request``, …) and
        folds them into ``extras`` so freezes and monorepo exports remain
        loadable without re-baking host identity into the public type.
        """
        known = {f.name for f in fields(cls)}
        payload = dict(data)
        extras: dict[str, Any] = dict(payload.pop("extras", None) or {})
        core: dict[str, Any] = {}
        for key, value in list(payload.items()):
            if key in known and key != "extras":
                core[key] = value
            else:
                extras[key] = value
        if extras:
            core["extras"] = extras
        return cls(**core)


__all__ = ["CognitionPin"]
