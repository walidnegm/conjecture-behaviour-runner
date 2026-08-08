"""Lightweight Conjecture runner logging + error contract.

Portable — no product secrets. Emits structured lines to stderr and an
optional ring buffer the console can poll for debug.

Env
---
``CONJECTURE_LOG_LEVEL``  DEBUG | INFO | WARNING | ERROR  (default INFO)
``CONJECTURE_LOG_JSON``   1 → one JSON object per line
"""
from __future__ import annotations

import json
import os
import sys
import threading
import traceback
from collections import deque
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

_LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}
_lock = threading.Lock()
_ring: deque[dict[str, Any]] = deque(maxlen=200)


def _level_num(name: str) -> int:
    return _LEVELS.get((name or "INFO").upper(), 20)


def _configured_level() -> int:
    return _level_num((os.environ.get("CONJECTURE_LOG_LEVEL") or "INFO").strip())


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(
    level: str,
    event: str,
    *,
    msg: str = "",
    **fields: Any,
) -> dict[str, Any]:
    """Emit a structured log event; return the record (also stored in ring)."""
    rec: dict[str, Any] = {
        "ts": _iso(),
        "level": level.upper(),
        "event": event,
        "msg": msg or event,
    }
    for k, v in fields.items():
        if v is None:
            continue
        # Never log secrets
        kl = k.lower()
        if any(s in kl for s in ("password", "api_key", "apikey", "token", "secret")):
            rec[k] = "***"
        else:
            try:
                json.dumps(v)
                rec[k] = v
            except (TypeError, ValueError):
                rec[k] = str(v)[:500]

    with _lock:
        _ring.append(rec)

    if _level_num(level) < _configured_level():
        return rec

    if (os.environ.get("CONJECTURE_LOG_JSON") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        line = json.dumps(rec, ensure_ascii=False)
    else:
        extra = " ".join(
            f"{k}={rec[k]!r}"
            for k in rec
            if k not in ("ts", "level", "event", "msg")
        )
        line = f"[conjecture {rec['level']}] {rec['event']}: {rec['msg']}"
        if extra:
            line = f"{line} | {extra}"
    print(line, file=sys.stderr, flush=True)
    return rec


def debug(event: str, msg: str = "", **fields: Any) -> dict[str, Any]:
    return log("DEBUG", event, msg=msg, **fields)


def info(event: str, msg: str = "", **fields: Any) -> dict[str, Any]:
    return log("INFO", event, msg=msg, **fields)


def warning(event: str, msg: str = "", **fields: Any) -> dict[str, Any]:
    return log("WARNING", event, msg=msg, **fields)


def error(event: str, msg: str = "", **fields: Any) -> dict[str, Any]:
    return log("ERROR", event, msg=msg, **fields)


def recent_logs(*, limit: int = 50, level: str | None = None) -> list[dict[str, Any]]:
    """Return newest-first ring buffer entries (for console Admin / debug)."""
    lim = max(1, min(int(limit or 50), 200))
    min_lv = _level_num(level) if level else 0
    with _lock:
        items = list(_ring)
    out = [r for r in items if _level_num(str(r.get("level") or "INFO")) >= min_lv]
    return list(reversed(out[-lim:]))


def error_contract(
    *,
    code: str,
    message: str,
    stage: str = "",
    scenario_id: str = "",
    adapter: str = "",
    exc: BaseException | None = None,
    details: Mapping[str, Any] | None = None,
    retryable: bool = False,
) -> dict[str, Any]:
    """Stable error payload for API/UI (path-faithful debug without stack spam)."""
    err: dict[str, Any] = {
        "ok": False,
        "error": code,
        "error_code": code,
        "message": message,
        "stage": stage or None,
        "scenario_id": scenario_id or None,
        "adapter": adapter or None,
        "retryable": bool(retryable),
        "ts": _iso(),
    }
    if details:
        err["details"] = dict(details)
    if exc is not None:
        err["exc_type"] = type(exc).__name__
        err["exc_message"] = str(exc)[:800]
        err["traceback"] = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )[-4000:]
    log(
        "ERROR",
        code,
        msg=message,
        stage=stage,
        scenario_id=scenario_id,
        adapter=adapter,
        exc_type=err.get("exc_type"),
        retryable=retryable,
    )
    return err


def wrap_ok(payload: Mapping[str, Any], *, event: str = "ok") -> dict[str, Any]:
    out = dict(payload)
    out.setdefault("ok", True)
    debug(event, msg=event, scenario_id=out.get("scenario_id"))
    return out


__all__ = [
    "debug",
    "error",
    "error_contract",
    "info",
    "log",
    "recent_logs",
    "warning",
    "wrap_ok",
]
