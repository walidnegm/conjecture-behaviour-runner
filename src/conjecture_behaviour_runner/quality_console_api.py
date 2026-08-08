"""Quality Console API helpers for the portable local UI (port 8765).

Host monorepo (Bot0) provides law_seek + registry; portable package degrades
gracefully when those modules are unavailable.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Optional

# Coverage-battery cancel: Stop button sets the event; run_law_seek checks
# between phases. One battery at a time on this process.
_seek_cancel = threading.Event()
_seek_lock = threading.Lock()
_seek_active = False


def request_law_seek_stop() -> dict[str, Any]:
    """Signal an in-flight Coverage battery to stop after the current phase."""
    _seek_cancel.set()
    return {
        "ok": True,
        "stop_requested": True,
        "active": _seek_active,
        "hint": "Cancels between law_seek phases; long ratchet/script phase may finish first.",
    }


def law_seek_running() -> bool:
    return _seek_active


def _host_root() -> Optional[Path]:
    """Best-effort monorepo root when running inside Bot0."""
    # CWD often is monorepo root when `conjecture ui` is launched from Bot0.
    cwd = Path.cwd().resolve()
    markers = (
        cwd / "docs" / "epics" / "failure-mode-registry.yaml",
        cwd / "conjecture_host" / "conjecture_expansion" / "law_seek_harness.py",
    )
    if all(m.is_file() for m in markers[:1]) or markers[1].is_file():
        return cwd
    # Package lives at extract/conjecture-behaviour-runner/src/... → monorepo is parents[4]
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "docs" / "epics" / "failure-mode-registry.yaml").is_file():
            return parent
        if (parent / "conjecture_host" / "conjecture_expansion").is_dir():
            return parent
    return None


def host_quality_available() -> dict[str, Any]:
    root = _host_root()
    if root is None:
        return {
            "ok": False,
            "available": False,
            "error": "host_monorepo_not_found",
            "hint": (
                "Run `conjecture ui` from the Bot0 monorepo root, or ensure "
                "conjecture_host.expansion is importable."
            ),
        }
    try:
        import conjecture_host.expansion.law_seek_harness  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "available": False,
            "error": "law_seek_import_failed",
            "detail": str(exc),
            "root": str(root),
        }
    return {"ok": True, "available": True, "root": str(root)}


def get_law_seek(
    *,
    run: bool = False,
    live: bool = False,
    quick: bool = True,
    skip_scripts: bool = False,
) -> dict[str, Any]:
    """Return latest law_seek report or run the harness."""
    avail = host_quality_available()
    if not avail.get("available"):
        return avail

    from conjecture_host.expansion.law_seek_harness import (
        ARTIFACT_DIR,
        format_law_seek_markdown,
        run_law_seek,
    )

    if run:
        global _seek_active
        with _seek_lock:
            if _seek_active:
                return {
                    "ok": False,
                    "available": True,
                    "ran": False,
                    "error": "seek_already_running",
                    "hint": "Use Stop, then start again.",
                }
            _seek_active = True
            _seek_cancel.clear()
        try:
            report = run_law_seek(
                live=live,
                quick=quick,
                skip_scripts=skip_scripts,
                write_artifact=True,
                cancel_check=_seek_cancel.is_set,
            )
            payload = report.to_dict()
            return {
                "ok": True,
                "available": True,
                "ran": True,
                "passed": payload.get("passed"),
                "cancelled": bool(payload.get("cancelled")),
                "report": payload,
                "markdown": format_law_seek_markdown(report),
                "artifact": "latest.json",
                "artifact_dir": str(ARTIFACT_DIR),
            }
        finally:
            with _seek_lock:
                _seek_active = False
                _seek_cancel.clear()

    latest = ARTIFACT_DIR / "latest.json"
    if latest.is_file():
        data = json.loads(latest.read_text(encoding="utf-8"))
        md_path = ARTIFACT_DIR / "latest.md"
        md = md_path.read_text(encoding="utf-8") if md_path.is_file() else ""
        return {
            "ok": True,
            "available": True,
            "ran": False,
            "passed": bool(data.get("passed")),
            "report": data,
            "markdown": md,
            "artifact": "latest.json",
            "artifact_dir": str(ARTIFACT_DIR),
        }
    return {
        "ok": False,
        "available": True,
        "ran": False,
        "error": "no_law_seek_artifact",
        "hint": (
            "POST /api/law-seek/run with {\"quick\": true} or CLI: "
            "python -m conjecture_host.expansion law_seek --quick"
        ),
        "artifact_dir": str(ARTIFACT_DIR),
    }


def get_quality_snapshot(
    *,
    rebuild: bool = False,
    run_seek: bool = False,
    live: bool = False,
    quick: bool = True,
) -> dict[str, Any]:
    """Return QualityConsoleSnapshot (prefer cached; rebuild on demand)."""
    avail = host_quality_available()
    if not avail.get("available"):
        return avail

    from conjecture_host.expansion.quality_console_snapshot import (
        SNAPSHOT_DIR,
        build_quality_console_snapshot,
        load_latest_snapshot,
    )

    if not rebuild and not run_seek:
        cached = load_latest_snapshot()
        if cached is not None:
            return {
                "ok": True,
                "available": True,
                "rebuilt": False,
                "snapshot": cached,
                "artifact": str(SNAPSHOT_DIR / "latest.json"),
            }
        # No cache: build from latest law_seek without re-running battery
        snap = build_quality_console_snapshot(
            run_seek=False,
            write_artifact=True,
        )
        return {
            "ok": True,
            "available": True,
            "rebuilt": True,
            "snapshot": snap,
            "artifact": snap.get("artifact"),
        }

    snap = build_quality_console_snapshot(
        run_seek=run_seek,
        live=live,
        quick=quick,
        write_artifact=True,
    )
    return {
        "ok": True,
        "available": True,
        "rebuilt": True,
        "ran_seek": run_seek,
        "snapshot": snap,
        "artifact": snap.get("artifact"),
    }


def get_laws(*, registry_id: Optional[str] = None) -> dict[str, Any]:
    """Registry mode board for Laws tab (from snapshot / live build)."""
    payload = get_quality_snapshot(rebuild=False, run_seek=False)
    if not payload.get("ok"):
        return payload
    snap = payload.get("snapshot") or {}
    laws = list(snap.get("laws") or [])
    if registry_id:
        laws = [r for r in laws if r.get("registry_id") == registry_id]
        if not laws:
            return {
                "ok": False,
                "available": True,
                "error": "mode_not_found",
                "registry_id": registry_id,
            }
        return {
            "ok": True,
            "available": True,
            "mode": laws[0],
            "summary": snap.get("summary"),
        }
    return {
        "ok": True,
        "available": True,
        "laws": laws,
        "summary": snap.get("summary"),
        "chrome": (snap.get("nav") or {}).get("chrome"),
        "stack": snap.get("stack"),
    }


__all__ = [
    "host_quality_available",
    "get_law_seek",
    "get_quality_snapshot",
    "get_laws",
    "law_seek_running",
    "request_law_seek_stop",
]
