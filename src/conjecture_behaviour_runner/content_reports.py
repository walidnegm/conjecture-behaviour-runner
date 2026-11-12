"""Content-evaluation reports on disk — read by the console's **Content** view.

A host's content-eval runner writes one JSON report per run into a directory
(``CONJECTURE_CONTENT_REPORTS_DIR``, default ``~/.cache/conjecture/content-reports``).
The console lists them and shows one; it never runs an evaluation itself, because a
judged run spends model calls and its budget belongs on the command line.

Report shape (keys the view reads; extra keys are kept and ignored)::

    {
      "suite": "glossary", "stages": ["retrieve", "select", "answer"],
      "ran_at": "...", "seconds": 47.0, "model_calls": 17,
      "budget": {"max_llm_calls": 25, "stopped": null},
      "pins": {...},                         # what the scores depend on
      "rates": summarize(...),               # top1, acceptable_hit, forbidden_selection, ...
      "by_stage": {"retrieve": {"held": 1, "failed": []}, ...},
      "judged_means": {"faithfulness": 1.0, ...},
      "passed": 0, "cases": 1,
      "results": [{"case", "passed", "failures", "selected", "via",
                   "retrieved", "judged": {metric: {score, reason}}, "answer"}]
    }
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

__all__ = ["DEFAULT_REPORTS_DIR", "get_report", "list_reports", "reports_dir"]

DEFAULT_REPORTS_DIR = "~/.cache/conjecture/content-reports"


def reports_dir() -> Path:
    return Path(os.path.expanduser(os.getenv("CONJECTURE_CONTENT_REPORTS_DIR") or DEFAULT_REPORTS_DIR))


def _safe(name: str) -> Optional[Path]:
    """A report file in the reports directory — a bare ``*.json`` name, never a path."""
    if not name or "/" in name or "\\" in name or name.startswith(".") or not name.endswith(".json"):
        return None
    p = reports_dir() / name
    return p if p.is_file() else None


def list_reports(limit: int = 50) -> dict[str, Any]:
    root = reports_dir()
    items: list[dict[str, Any]] = []
    files = sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True) if root.is_dir() else []
    for p in files[: max(1, limit)]:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — a malformed file is listed as such, never fatal
            items.append({"file": p.name, "error": "unreadable"})
            continue
        items.append({
            "file": p.name,
            "suite": d.get("suite"),
            "ran_at": d.get("ran_at"),
            "stages": d.get("stages") or [],
            "passed": d.get("passed"),
            "cases": d.get("cases"),
            "model_calls": d.get("model_calls"),
            "rates": d.get("rates") or {},
            "judged_means": d.get("judged_means") or {},
        })
    return {"dir": str(root), "count": len(items), "items": items}


def get_report(name: str) -> Optional[dict[str, Any]]:
    p = _safe(name)
    if p is None:
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    d["file"] = p.name
    return d
