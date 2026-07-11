"""Generic HTTP/JSON Driver+Observer (stdlib urllib).

Configure a POST endpoint and JSON paths for owner / pins / outcome so hosts
need not implement a Python protocol first.

Example::

    adapter = HttpJsonAdapter(
        endpoint="http://localhost:8000/chat",
        owner_path="debug.owner",
        pins_path="debug.pins",
        outcome_path="debug.outcome",
    )
    result = run_script(script, adapter=adapter, llm_mode=LlmMode.STUB)

Dot-paths are simple (no full JSONPath). Missing paths → None / {}.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Mapping, Optional
from urllib.parse import urlparse

from conjecture_behaviour_runner.invariants import BaseControlPlaneAdapter
from conjecture_behaviour_runner.protocol import TurnObservation
from conjecture_behaviour_runner.script import InvariantSpec, LedgerEffect


def _dig(data: Any, path: str) -> Any:
    """Resolve a dotted path like ``debug.owner`` or ``result.pins.workflow_id``."""
    if not path:
        return None
    cur = data
    for part in path.split("."):
        if cur is None:
            return None
        if isinstance(cur, Mapping):
            cur = cur.get(part)
        else:
            return None
    return cur


class HttpJsonAdapter(BaseControlPlaneAdapter):
    """POST each turn to ``endpoint``; map JSON response into TurnObservation."""

    def __init__(
        self,
        *,
        endpoint: str,
        owner_path: str = "exclusive_owner",
        kind_path: str = "active_kind",
        pins_path: str = "pins",
        outcome_path: str = "observed_outcome",
        extras_path: str = "extras",
        timeout_seconds: float = 30.0,
        headers: Optional[Mapping[str, str]] = None,
        conversation_id_field: str = "conversation_id",
        message_field: str = "message",
    ) -> None:
        parsed = urlparse(endpoint)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"endpoint must be http(s) URL, got {endpoint!r}")
        self.endpoint = endpoint
        self.owner_path = owner_path
        self.kind_path = kind_path
        self.pins_path = pins_path
        self.outcome_path = outcome_path
        self.extras_path = extras_path
        self.timeout_seconds = timeout_seconds
        self.headers = dict(headers or {"Content-Type": "application/json"})
        self.conversation_id_field = conversation_id_field
        self.message_field = message_field
        self._conversation_id: Optional[str] = None

    def apply_effect(
        self, context: dict[str, Any], effect: LedgerEffect
    ) -> dict[str, Any]:
        # HTTP hosts usually arrange via the app; keep context keys for templating.
        ctx = dict(context)
        if effect.op == "set_conversation_id":
            self._conversation_id = str((effect.payload or {}).get("id") or "")
            ctx["conversation_id"] = self._conversation_id
        return ctx

    def observe_turn(
        self,
        *,
        context: dict[str, Any],
        user_text: str,
        pin: Any,
    ) -> TurnObservation:
        conv = (
            self._conversation_id
            or context.get("conversation_id")
            or context.get("conversationId")
            or ""
        )
        pin_payload: Any = None
        if pin is not None and hasattr(pin, "to_dict"):
            pin_payload = pin.to_dict()
        elif isinstance(pin, Mapping):
            pin_payload = dict(pin)
        body = {
            self.message_field: user_text,
            self.conversation_id_field: conv,
            "pin": pin_payload,
            "context": context,
        }
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=data,
            headers=self.headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
                payload = json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(
                f"HttpJsonAdapter HTTP {exc.code} from {self.endpoint}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"HttpJsonAdapter could not reach {self.endpoint}: {exc}"
            ) from exc

        if not isinstance(payload, Mapping):
            raise RuntimeError("HttpJsonAdapter: response JSON root must be an object")

        pins = _dig(payload, self.pins_path)
        if pins is None:
            pins = {}
        if not isinstance(pins, Mapping):
            raise RuntimeError(
                f"HttpJsonAdapter: pins at {self.pins_path!r} must be object"
            )
        extras = _dig(payload, self.extras_path)
        if extras is not None and not isinstance(extras, Mapping):
            extras = {"value": extras}
        owner = _dig(payload, self.owner_path)
        kind = _dig(payload, self.kind_path)
        outcome = _dig(payload, self.outcome_path)
        return TurnObservation(
            exclusive_owner=str(owner) if owner is not None else None,
            active_kind=str(kind) if kind is not None else None,
            pins=dict(pins),
            context=None,
            observed_outcome=str(outcome) if outcome is not None else None,
            extras=dict(extras) if isinstance(extras, Mapping) else {},
        )


__all__ = ["HttpJsonAdapter", "_dig"]
