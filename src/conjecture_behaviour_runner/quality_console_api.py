"""Quality Console API helpers for the portable local UI (port 8765).

Host monorepo (Bot0) provides law_seek + registry; portable package degrades
gracefully when those modules are unavailable.
"""
from __future__ import annotations

import json
import sys
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
        cwd / "regression_suite" / "conjecture_expansion" / "law_seek_harness.py",
        cwd / "regression_suite" / "architecture_audit" / "inventory_registry.yaml",
    )
    if markers[0].is_file() or markers[1].is_file() or markers[2].is_file():
        return cwd
    # Package lives at extract/conjecture-behaviour-runner/src/... → monorepo is parents[4]
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "docs" / "epics" / "failure-mode-registry.yaml").is_file():
            return parent
        if (parent / "regression_suite" / "conjecture_expansion").is_dir():
            return parent
        if (parent / "regression_suite" / "architecture_audit").is_dir():
            return parent
    return None


def _ensure_host_on_sys_path() -> Optional[Path]:
    """Put monorepo root on sys.path so host packages import when ui is installed editable.

    ``conjecture ui`` often runs the *extract* package from site-packages / extract src
    while the process cwd is the monorepo — without this, ``import regression_suite``
    fails even though the tree is present on disk.
    """
    root = _host_root()
    if root is None:
        return None
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    return root


def host_quality_available() -> dict[str, Any]:
    root = _ensure_host_on_sys_path()
    if root is None:
        return {
            "ok": False,
            "available": False,
            "error": "host_monorepo_not_found",
            "hint": (
                "Run `conjecture ui` from the Bot0 monorepo root, or ensure "
                "host quality modules are importable."
            ),
        }
    try:
        import regression_suite.conjecture_expansion.law_seek_harness  # noqa: F401
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

    from regression_suite.conjecture_expansion.law_seek_harness import (
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
            "python -m regression_suite.conjecture_expansion law_seek --quick"
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

    from regression_suite.conjecture_expansion.quality_console_snapshot import (
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


def get_architecture_audit(
    *,
    run: bool = False,
    subject: str = "bot0_dogfood",
    concept_id: Optional[str] = None,
) -> dict[str, Any]:
    """Architecture Audit (Offer 2) — inventory registry + dogfood concept runners.

    Does **not** require law_seek / Offer-1 quality stack — only host architecture_audit
    package (or degrades with a clear error).
    """
    root = _ensure_host_on_sys_path()
    try:
        from regression_suite.architecture_audit.registry import (
            ARTIFACT_DIR,
            inventory_summary,
            load_inventory_registry,
        )
        from regression_suite.architecture_audit.runner import (
            load_latest_report,
            run_architecture_audit,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "available": False,
            "error": "architecture_audit_import_failed",
            "detail": str(exc),
            "root": str(root) if root else None,
            "hint": (
                "Run `conjecture ui` from the monorepo root so host package "
                "architecture_audit is on sys.path. Offer 2 does not need law_seek."
            ),
        }

    reg = load_inventory_registry()
    summary = inventory_summary(reg)
    try:
        from regression_suite.architecture_audit.doctrine_visibility import (
            doctrine_visibility_bundle,
        )

        doctrine = doctrine_visibility_bundle()
    except Exception:  # noqa: BLE001
        doctrine = {"version": 0, "panels": []}

    if run:
        concept_ids = [concept_id] if concept_id else None
        report = run_architecture_audit(
            concept_ids=concept_ids,
            subject=subject or "bot0_dogfood",
            implemented_only=concept_id is None,
            write_artifact=True,
        )
        return {
            "ok": True,
            "available": True,
            "ran": True,
            "root": str(root) if root else None,
            "registry": reg,
            "summary": summary,
            "doctrine_visibility": doctrine,
            "report": report,
            "artifact": report.get("artifact"),
        }

    latest = load_latest_report()
    return {
        "ok": True,
        "available": True,
        "ran": False,
        "root": str(root) if root else None,
        "registry": reg,
        "summary": summary,
        "doctrine_visibility": doctrine,
        "report": latest,
        "artifact": str(ARTIFACT_DIR / "latest.json") if latest else None,
        "hint": (
            "POST /api/architecture-audit/run for dogfood. "
            "doctrine_visibility panels (memory L1–L6 relation) always load with inventory."
        ),
    }


def get_architecture_audit_depth_prompt() -> dict[str, Any]:
    """Back-compat: Architecture Audit Review prompt v1."""
    return get_architecture_audit_prompt(mode="audit_review", version=1)


def get_architecture_audit_prompt(
    *,
    mode: str = "audit_review",
    version: Optional[int] = None,
) -> dict[str, Any]:
    """Versioned Architecture Audit LLM prompts (console-visible).

    Live: audit_review v1. Planned: invent · compare · interrogate.
    """
    root = _ensure_host_on_sys_path()
    try:
        from regression_suite.architecture_audit.audit_prompts import (
            build_audit_prompt,
            list_prompts,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "available": False,
            "error": "audit_prompt_import_failed",
            "detail": str(exc),
            "root": str(root) if root else None,
            "catalog": [],
        }
    try:
        payload = build_audit_prompt(mode=mode, version=version)
        if isinstance(payload, dict) and "catalog" not in payload:
            payload["catalog"] = list_prompts()
        return payload
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "available": False,
            "error": "audit_prompt_build_failed",
            "detail": str(exc),
            "root": str(root) if root else None,
        }


__all__ = [
    "host_quality_available",
    "get_law_seek",
    "get_quality_snapshot",
    "get_laws",
    "law_seek_running",
    "request_law_seek_stop",
    "get_architecture_audit",
    "get_architecture_audit_depth_prompt",
    "get_architecture_audit_prompt",
]
