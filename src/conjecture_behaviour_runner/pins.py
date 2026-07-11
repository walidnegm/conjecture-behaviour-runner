"""Cognition pins — structured labels only (no free-form NL interpretation)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Mapping


@dataclass(frozen=True)
class CognitionPin:
    """Pinned classifier/router output for one turn.

    Hosts map these fields onto their control-plane router signal. Values are
    **enums / flags**, not prose — code owns execution; the pin stands in for
    LLM cognition under ``LlmMode.STUB`` / ``FREEZE``.
    """

    task_intent: str = "continue"
    route_intent: str = "default"
    discovery_kind: str = "none"
    read_kind: str = "none"
    product_concept_kind: str = "none"
    cost_estimate_request: bool = False
    workflow_draft_request: bool = False
    catalog_role_request: bool = False
    reset_request: bool = False
    attachment_capability_request: bool = False
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

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CognitionPin":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})
