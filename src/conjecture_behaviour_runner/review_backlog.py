"""Session-agent review backlog — product bugs vs conjecture law catches.

Why
---
A host run may **PASS** CAQ invariants (or fail only on rate limits) while the
product flow still fails (wrong leaf, intent ignored, hollow delivery). Generic
OpenAI findings authors lack monorepo context. The **session coding agent**
(optional brand via ``CONJECTURE_SESSION_AGENT_LABEL``) reads conversation
ids against the codebase and classifies:

* ``conjecture_caught`` — law filter worked as designed (PASS/FAIL is correct)
* ``product_bug`` — flow broken; not (only) a CAQ invariant miss
* ``rate_limit`` / ``infra`` — environment, not product intent
* ``inconclusive`` — need more evidence

Invent/authoring may still use ChatGPT/Claude. Reviewer defaults to **session**.

Store (host)
------------
``CONJECTURE_BACKLOG_DIR`` or ``<candidates_dir>/../backlog`` or
``conjecture_host/expansion/backlog``.

Each item is one JSON file under ``items/`` + ``index.json`` summary.

Session handoff
---------------
After enqueue, write ``HANDOFF.md`` with open item ids. In the monorepo session
the user says: *review conjecture backlog* — agent loads items, fetches
``conversation_id`` / product evidence, writes ``analysis`` + classification
via ``update_backlog_item`` (or edits JSON). Console **Backlog** tab shows them.

After findings are developed and the user says **fix**, the agent implements
seals then calls ``close_with_patch`` (or batch) so open ``backlog_fix`` items
become **closed** with the **patch documented on the closed item**.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

# Classification set (code-owned enum — agent fills, code validates)
CLASSIFICATIONS = frozenset({
    "needs_review",
    "conjecture_caught",
    "product_bug",
    "rate_limit",
    "infra",
    "inconclusive",
    "wont_fix",
    "fixed",
})

STATUSES = frozenset({
    "needs_review",
    "in_review",
    "backlog_fix",
    "closed",
})

_SAFE = re.compile(r"^[A-Za-z0-9._-]{1,180}$")


def resolve_backlog_dir(explicit: str | Path | None = None) -> Path:
    if explicit is not None:
        p = Path(explicit).expanduser()
        p.mkdir(parents=True, exist_ok=True)
        (p / "items").mkdir(parents=True, exist_ok=True)
        return p
    env = (os.environ.get("CONJECTURE_BACKLOG_DIR") or "").strip()
    if env:
        p = Path(env).expanduser()
        p.mkdir(parents=True, exist_ok=True)
        (p / "items").mkdir(parents=True, exist_ok=True)
        return p
    # Prefer monorepo host path when present
    cwd = Path.cwd().resolve()
    for base in [cwd, *cwd.parents]:
        host = base / "conjecture_host" / "conjecture_expansion" / "backlog"
        if host.parent.is_dir() or (base / "conjecture_host").is_dir():
            host.mkdir(parents=True, exist_ok=True)
            (host / "items").mkdir(parents=True, exist_ok=True)
            return host
        if base.parent == base:
            break
    # Fallback next to candidates
    try:
        from conjecture_behaviour_runner.candidates_ui import resolve_candidates_dir

        cdir = resolve_candidates_dir()
        if cdir is not None:
            p = cdir.parent / "backlog"
            p.mkdir(parents=True, exist_ok=True)
            (p / "items").mkdir(parents=True, exist_ok=True)
            return p
    except Exception:  # noqa: BLE001
        pass
    p = Path.cwd() / "conjecture_backlog"
    p.mkdir(parents=True, exist_ok=True)
    (p / "items").mkdir(parents=True, exist_ok=True)
    return p


def findings_reviewer_mode() -> str:
    """session (default) | openai | deterministic."""
    raw = (os.environ.get("CONJECTURE_FINDINGS_REVIEWER") or "session").strip().lower()
    if raw in ("openai", "llm", "invent"):
        return "openai"
    if raw in ("deterministic", "det", "code"):
        return "deterministic"
    return "session"


def session_agent_label() -> str:
    """Display name for the monorepo session reviewer (portable).

    Default is neutral ``session coding agent``. Hosts may brand locally::

        CONJECTURE_SESSION_AGENT_LABEL=Grok

    Extract package never requires a vendor name.
    """
    raw = (os.environ.get("CONJECTURE_SESSION_AGENT_LABEL") or "").strip()
    return raw or "session coding agent"


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _item_path(backlog_dir: Path, item_id: str) -> Path:
    if not _SAFE.match(item_id):
        raise ValueError(f"invalid backlog item_id: {item_id!r}")
    return backlog_dir / "items" / f"{item_id}.json"


def enqueue_review(
    *,
    scenario_id: str,
    evidence: Mapping[str, Any] | None = None,
    batch_result_row: Mapping[str, Any] | None = None,
    adapter: str = "",
    reason: str = "post_run",
    backlog_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Create a backlog item for session-agent review. Idempotent-ish per run."""
    bdir = resolve_backlog_dir(backlog_dir)
    ev = dict(evidence or {})
    row = dict(batch_result_row or {})
    run = ev.get("run") if isinstance(ev.get("run"), Mapping) else {}
    run = dict(run or {})
    findings = ev.get("findings") if isinstance(ev.get("findings"), Mapping) else {}
    findings = dict(findings or row.get("findings") or {})

    thread_id = (
        row.get("thread_id")
        or run.get("thread_id")
        or ev.get("thread_id")
        or (run.get("extras") or {}).get("thread_id")
        if isinstance(run.get("extras"), Mapping)
        else None
    )
    # Also dig observation extras
    if not thread_id:
        for t in run.get("turns") or []:
            if not isinstance(t, Mapping):
                continue
            obs = t.get("observation") if isinstance(t.get("observation"), Mapping) else {}
            ex = obs.get("extras") if isinstance(obs.get("extras"), Mapping) else {}
            if ex.get("thread_id"):
                thread_id = ex.get("thread_id")
                break

    ok = row.get("ok", ev.get("ok", True))
    passed = row.get("passed")
    if passed is None:
        passed = run.get("passed")
    err = row.get("error") or ev.get("error")

    tax = ev.get("taxonomy") if isinstance(ev.get("taxonomy"), Mapping) else {}
    tax = dict(tax or {})
    split = (
        ev.get("candidate_split")
        if isinstance(ev.get("candidate_split"), Mapping)
        else {}
    )
    split = dict(split or {})
    wah = row.get("what_actually_happened") or ev.get("what_actually_happened") or {}
    if not isinstance(wah, Mapping):
        wah = {}
    wah = dict(wah)
    failures = list(
        row.get("failures") or run.get("failures") or ev.get("failures") or []
    )
    # Compact turn observations for the report card (host/geometry)
    run_turns: list[dict[str, Any]] = []
    for i, t in enumerate(run.get("turns") or []):
        if not isinstance(t, Mapping):
            continue
        obs = t.get("observation") if isinstance(t.get("observation"), Mapping) else {}
        run_turns.append(
            {
                "index": t.get("index", i),
                "user_text": (t.get("user_text") or t.get("text") or "")[:400],
                "owner": obs.get("owner") or obs.get("exclusive_owner"),
                "outcome": obs.get("outcome") or obs.get("task_intent"),
                "agent_type": obs.get("agent_type"),
                "active_kind": (
                    obs.get("active_kind")
                    or (
                        (obs.get("pins") or {}).get("kind")
                        if isinstance(obs.get("pins"), Mapping)
                        else None
                    )
                ),
                "failures": list(t.get("failures") or []),
            }
        )
        if len(run_turns) >= 40:
            break

    failure_mode = (
        row.get("failure_mode")
        or tax.get("failure_mode")
        or split.get("failure_mode_mapping")
        or wah.get("failure_mode")
        or findings.get("failure_mode_slug")
        or ""
    )

    item_id = f"{_ts()}_{re.sub(r'[^A-Za-z0-9._-]+', '_', scenario_id)[:80]}"
    item: dict[str, Any] = {
        "id": item_id,
        "created_at": _iso(),
        "updated_at": _iso(),
        "status": "needs_review",
        "classification": "needs_review",
        "reason": reason,
        "scenario_id": scenario_id,
        "failure_mode": failure_mode,
        "incident_id": (
            row.get("incident_id")
            or tax.get("incident")
            or wah.get("incident_id")
            or ""
        ),
        "scenario_purpose": (
            row.get("scenario_purpose")
            or ev.get("scenario_purpose")
            or split.get("scenario_purpose")
            or ""
        ),
        "user_trajectory": row.get("user_trajectory") or split.get("user_trajectory") or "",
        "adapter": adapter or row.get("adapter") or run.get("adapter") or "",
        "product_path": bool(row.get("product_path") or ev.get("product_path")),
        "run_ok": ok is not False,
        "run_passed": bool(passed) if passed is not None else None,
        "run_error": err,
        "run_failures": failures,
        "run_turns": run_turns,
        "thread_id": thread_id,
        "conversation_id": thread_id,  # Bot0: conversation_id == thread_id
        "account": row.get("account") or ev.get("account") or run.get("email"),
        "evidence_path": row.get("evidence_path") or ev.get("evidence_path"),
        "taxonomy": tax,
        "candidate_split": split,
        "headline": findings.get("headline") or row.get("headline") or "",
        "findings_skeleton": findings,  # code-owned tables; agent expands
        "what_actually_happened": wah,
        "analysis": None,  # filled by session agent — prose + tables
        "suggested_fixes": list(findings.get("suggested_fixes") or [])[:20]
        if isinstance(findings.get("suggested_fixes"), list)
        else [],
        "reviewer": "session_agent",  # not openai by default
        "related_item_ids": [],
        "fix_notes": "",
        # Filled by close_with_patch after session "fix" command
        "patch": None,
        "closed_at": None,
        "review_checklist": [
            "Load conversation_id transcript + route_data / control events",
            "Layer trace: claim → router → referential/decide → leaf",
            "Classify conjecture_caught | product_bug | rate_limit | infra",
            "Fill findings tables + suggested_fixes",
            "On fix: close_with_patch and document patch on closed item",
        ],
    }
    path = _item_path(bdir, item_id)
    path.write_text(json.dumps(item, indent=2) + "\n", encoding="utf-8")
    _rebuild_index(bdir)
    _write_handoff(bdir)
    return item


def list_backlog(
    *,
    status: str | None = None,
    classification: str | None = None,
    limit: int = 100,
    backlog_dir: str | Path | None = None,
) -> dict[str, Any]:
    bdir = resolve_backlog_dir(backlog_dir)
    items_dir = bdir / "items"
    rows: list[dict[str, Any]] = []
    if items_dir.is_dir():
        for p in sorted(items_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            if not isinstance(data, dict):
                continue
            if status and data.get("status") != status:
                continue
            if classification and data.get("classification") != classification:
                continue
            rows.append(data)
            if len(rows) >= max(1, min(limit, 500)):
                break
    by_status: dict[str, int] = {}
    by_class: dict[str, int] = {}
    for r in rows:
        st = str(r.get("status") or "unknown")
        by_status[st] = by_status.get(st, 0) + 1
        cl = str(r.get("classification") or "unknown")
        by_class[cl] = by_class.get(cl, 0) + 1
    return {
        "ok": True,
        "dir": str(bdir),
        "count": len(rows),
        "by_status": by_status,
        "by_classification": by_class,
        "items": rows,
        "handoff_path": str(bdir / "HANDOFF.md"),
        "note": (
            f"Reviewer = {session_agent_label()}. Invent LLM may stay OpenAI. "
            "In the monorepo session say: review conjecture backlog"
        ),
        "session_agent_label": session_agent_label(),
    }


def get_backlog_item(
    item_id: str,
    *,
    backlog_dir: str | Path | None = None,
) -> dict[str, Any]:
    bdir = resolve_backlog_dir(backlog_dir)
    path = _item_path(bdir, item_id)
    if not path.is_file():
        return {"ok": False, "error": "not_found", "id": item_id}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "id": item_id}
    return {"ok": True, "item": data, "path": str(path)}


def update_backlog_item(
    item_id: str,
    *,
    classification: str | None = None,
    status: str | None = None,
    analysis: Mapping[str, Any] | str | None = None,
    suggested_fixes: list[Mapping[str, Any]] | None = None,
    fix_notes: str | None = None,
    related_item_ids: list[str] | None = None,
    findings: Mapping[str, Any] | None = None,
    backlog_dir: str | Path | None = None,
    reviewer: str | None = None,
) -> dict[str, Any]:
    """Session agent writes classification + analysis + fixes after reading conv_id."""
    bdir = resolve_backlog_dir(backlog_dir)
    path = _item_path(bdir, item_id)
    if not path.is_file():
        return {"ok": False, "error": "not_found", "id": item_id}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "id": item_id}
    if not isinstance(data, dict):
        return {"ok": False, "error": "invalid_item"}

    if classification is not None:
        cl = classification.strip().lower()
        if cl not in CLASSIFICATIONS:
            return {
                "ok": False,
                "error": f"invalid_classification:{cl}",
                "allowed": sorted(CLASSIFICATIONS),
            }
        data["classification"] = cl
        # Map classification → default status
        if status is None:
            if cl in ("product_bug",):
                data["status"] = "backlog_fix"
            elif cl in ("conjecture_caught", "wont_fix", "fixed"):
                data["status"] = "closed"
            elif cl in ("rate_limit", "infra", "inconclusive"):
                data["status"] = "closed" if cl != "inconclusive" else "needs_review"
            else:
                data["status"] = "needs_review"
    if status is not None:
        st = status.strip().lower()
        if st not in STATUSES:
            return {
                "ok": False,
                "error": f"invalid_status:{st}",
                "allowed": sorted(STATUSES),
            }
        data["status"] = st
    if analysis is not None:
        if isinstance(analysis, Mapping):
            data["analysis"] = dict(analysis)
        else:
            data["analysis"] = {
                "prose": str(analysis),
                "reviewed_at": _iso(),
            }
        if isinstance(data.get("analysis"), dict):
            data["analysis"].setdefault("reviewed_at", _iso())
    if suggested_fixes is not None:
        data["suggested_fixes"] = [
            dict(fx) for fx in suggested_fixes if isinstance(fx, Mapping)
        ][:20]
        # Mirror onto analysis for single-blob consumers
        if isinstance(data.get("analysis"), dict):
            data["analysis"]["suggested_fixes"] = data["suggested_fixes"]
    if fix_notes is not None:
        data["fix_notes"] = str(fix_notes)
    if related_item_ids is not None:
        data["related_item_ids"] = [str(x) for x in related_item_ids]
    if findings is not None:
        data["findings_skeleton"] = dict(findings)
        # Promote full agent findings
        data["findings"] = dict(findings)
    if reviewer:
        data["reviewer"] = reviewer
    data["updated_at"] = _iso()
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    _rebuild_index(bdir)
    _write_handoff(bdir)
    return {"ok": True, "item": data, "path": str(path)}


def _normalize_patch(
    patch: Mapping[str, Any] | str | None,
    *,
    fix_notes: str | None = None,
    closed_by: str = "session_agent",
) -> dict[str, Any]:
    """Structured patch record stored on the closed backlog item."""
    now = _iso()
    if isinstance(patch, Mapping):
        rec = dict(patch)
    elif isinstance(patch, str) and patch.strip():
        rec = {"summary": patch.strip()}
    else:
        rec = {}
    summary = str(
        rec.get("summary") or rec.get("prose") or fix_notes or ""
    ).strip()
    files_raw = rec.get("files") or rec.get("paths") or []
    files: list[str] = []
    if isinstance(files_raw, (list, tuple)):
        files = [str(f) for f in files_raw if str(f).strip()][:40]
    elif isinstance(files_raw, str) and files_raw.strip():
        files = [files_raw.strip()]
    commits_raw = rec.get("commits") or rec.get("commit") or []
    commits: list[str] = []
    if isinstance(commits_raw, (list, tuple)):
        commits = [str(c) for c in commits_raw if str(c).strip()][:20]
    elif isinstance(commits_raw, str) and commits_raw.strip():
        commits = [commits_raw.strip()]
    tests_raw = rec.get("tests") or rec.get("ratchets") or []
    tests: list[str] = []
    if isinstance(tests_raw, (list, tuple)):
        tests = [str(t) for t in tests_raw if str(t).strip()][:20]
    elif isinstance(tests_raw, str) and tests_raw.strip():
        tests = [tests_raw.strip()]
    return {
        "summary": summary,
        "files": files,
        "commits": commits,
        "tests": tests,
        "seal": str(rec.get("seal") or rec.get("seal_recommendation") or "").strip(),
        "notes": str(rec.get("notes") or fix_notes or "").strip(),
        "closed_at": now,
        "closed_by": str(rec.get("closed_by") or closed_by or "session_agent"),
        "command": "fix",
    }


def close_with_patch(
    item_id: str,
    *,
    patch: Mapping[str, Any] | str | None = None,
    fix_notes: str | None = None,
    related_item_ids: list[str] | None = None,
    findings: Mapping[str, Any] | None = None,
    analysis: Mapping[str, Any] | str | None = None,
    backlog_dir: str | Path | None = None,
    reviewer: str = "session_agent",
) -> dict[str, Any]:
    """Close one open backlog item and document the implemented patch on it.

    Session protocol after findings are developed::

        user: fix
        agent: implements seals → close_with_patch(item_id, patch={...})

    Resulting item: ``status=closed``, ``classification=fixed``, ``patch`` filled.
    """
    bdir = resolve_backlog_dir(backlog_dir)
    path = _item_path(bdir, item_id)
    if not path.is_file():
        return {"ok": False, "error": "not_found", "id": item_id}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "id": item_id}
    if not isinstance(data, dict):
        return {"ok": False, "error": "invalid_item", "id": item_id}

    rec = _normalize_patch(patch, fix_notes=fix_notes, closed_by=reviewer)
    if not rec["summary"] and not rec["files"] and not rec["notes"]:
        return {
            "ok": False,
            "error": "patch_required",
            "hint": (
                "Provide patch.summary (and preferably files/commits/tests) "
                "so the closed item documents what shipped."
            ),
            "id": item_id,
        }

    data["status"] = "closed"
    data["classification"] = "fixed"
    data["patch"] = rec
    data["closed_at"] = rec["closed_at"]
    data["reviewer"] = reviewer
    note = fix_notes if fix_notes is not None else rec.get("notes") or rec.get("summary")
    if note:
        data["fix_notes"] = str(note)
    if related_item_ids is not None:
        data["related_item_ids"] = [str(x) for x in related_item_ids]
    if findings is not None:
        data["findings"] = dict(findings)
        data["findings_skeleton"] = dict(findings)
    if analysis is not None:
        if isinstance(analysis, Mapping):
            data["analysis"] = dict(analysis)
        else:
            data["analysis"] = {"prose": str(analysis), "reviewed_at": _iso()}
        if isinstance(data.get("analysis"), dict):
            data["analysis"].setdefault("reviewed_at", _iso())
            data["analysis"]["patch"] = rec
    elif isinstance(data.get("analysis"), dict):
        data["analysis"]["patch"] = rec
    data["updated_at"] = _iso()
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    _rebuild_index(bdir)
    _write_handoff(bdir)
    return {"ok": True, "item": data, "path": str(path), "closed": True}


def close_open_with_patch(
    *,
    patch: Mapping[str, Any] | str,
    item_ids: list[str] | None = None,
    status_filter: tuple[str, ...] = ("backlog_fix",),
    classification_filter: tuple[str, ...] | None = None,
    fix_notes: str | None = None,
    backlog_dir: str | Path | None = None,
    reviewer: str = "session_agent",
    limit: int = 50,
) -> dict[str, Any]:
    """Close open fix-queue items and document the same patch on each closed item.

    Default: every item with status ``backlog_fix`` (findings developed,
    ready for the session ``fix`` command). Unreviewed ``needs_review`` items
    are **not** auto-closed — pass ``item_ids`` for an explicit subset.
    """
    bdir = resolve_backlog_dir(backlog_dir)
    listing = list_backlog(limit=500, backlog_dir=bdir)
    targets: list[str] = []
    if item_ids:
        targets = [str(i) for i in item_ids if str(i).strip()]
    else:
        for r in listing.get("items") or []:
            if not isinstance(r, Mapping):
                continue
            st = str(r.get("status") or "")
            cl = str(r.get("classification") or "")
            if st not in status_filter:
                continue
            if classification_filter is not None and cl not in classification_filter:
                continue
            iid = r.get("id")
            if iid:
                targets.append(str(iid))
            if len(targets) >= max(1, min(limit, 100)):
                break

    closed: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    related = list(targets)
    for iid in targets:
        res = close_with_patch(
            iid,
            patch=patch,
            fix_notes=fix_notes,
            related_item_ids=related,
            backlog_dir=bdir,
            reviewer=reviewer,
        )
        if res.get("ok"):
            closed.append(
                {
                    "id": iid,
                    "scenario_id": (res.get("item") or {}).get("scenario_id"),
                    "path": res.get("path"),
                }
            )
        else:
            errors.append({"id": iid, "error": res.get("error"), "hint": res.get("hint")})

    _rebuild_index(bdir)
    _write_handoff(bdir)
    return {
        "ok": not errors or bool(closed),
        "closed_count": len(closed),
        "closed": closed,
        "errors": errors,
        "command": "fix",
        "note": (
            "Open items closed; patch documented on each closed item. "
            "Re-run scenarios to prove seals."
        ),
    }


def _rebuild_index(bdir: Path) -> None:
    listing = list_backlog(limit=500, backlog_dir=bdir)
    slim = [
        {
            "id": r.get("id"),
            "scenario_id": r.get("scenario_id"),
            "status": r.get("status"),
            "classification": r.get("classification"),
            "conversation_id": r.get("conversation_id"),
            "run_passed": r.get("run_passed"),
            "created_at": r.get("created_at"),
        }
        for r in listing.get("items") or []
    ]
    (bdir / "index.json").write_text(
        json.dumps(
            {
                "updated_at": _iso(),
                "count": len(slim),
                "by_status": listing.get("by_status"),
                "by_classification": listing.get("by_classification"),
                "items": slim,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_handoff(bdir: Path) -> None:
    needs = list_backlog(status="needs_review", limit=50, backlog_dir=bdir)
    fix_q = list_backlog(status="backlog_fix", limit=50, backlog_dir=bdir)
    label = session_agent_label()
    lines = [
        "# Conjecture review handoff (session agent)",
        "",
        f"Invent/author LLM may stay OpenAI/Claude. **Findings reviewer = {label}.**",
        f"(Set `CONJECTURE_SESSION_AGENT_LABEL` to brand; default is session coding agent.)",
        "",
        "## Commands",
        "",
        "```",
        "review conjecture backlog   # develop findings + classify",
        "fix                        # implement seals, close open items, document patch",
        "```",
        "",
        "### review conjecture backlog",
        "",
        "For each open item the agent should:",
        "1. Load item JSON under `items/`",
        "2. If `conversation_id` set — read product transcript (local Postgres or staging admin API)",
        "3. Map against monorepo control-plane / leaf code (path-faithful)",
        "4. Classify: `conjecture_caught` | `product_bug` | `rate_limit` | `infra` | `inconclusive`",
        "5. Write full findings tables + **suggested_fixes** (files, seal, ratchet)",
        "6. `product_bug` → status `backlog_fix` (do not ignore)",
        "",
        "### fix",
        "",
        "After findings are developed (`backlog_fix` / `product_bug`):",
        "1. Implement seals from `suggested_fixes` (contract + ratchet — not phrase laundry)",
        "2. Call `close_with_patch` / `close_open_with_patch` (or POST `/api/backlog/{id}/close`)",
        "3. Open items become **closed**; **`patch` is documented on each closed item**",
        "   (summary, files, commits, tests/ratchets, closed_at)",
        "",
        "Protocol: `extract/conjecture-behaviour-runner/.../prompts/session_reviewer.md`",
        "Process: `docs/conjecture-multi-agent-pipeline.md`",
        "",
        f"Updated: {_iso()}",
        f"Session agent label: {label}",
        f"Open needs_review: {needs.get('count', 0)}",
        f"Open backlog_fix: {fix_q.get('count', 0)}",
        "",
        "### needs_review",
        "",
    ]
    for r in needs.get("items") or []:
        lines.append(
            f"- `{r.get('id')}` · scenario=`{r.get('scenario_id')}` · "
            f"conv=`{r.get('conversation_id') or '—'}` · "
            f"passed={r.get('run_passed')} · err={str(r.get('run_error') or '')[:80]}"
        )
    if not (needs.get("items") or []):
        lines.append("- (none)")
    lines.extend(["", "### backlog_fix (ready for `fix`)", ""])
    for r in fix_q.get("items") or []:
        lines.append(
            f"- `{r.get('id')}` · scenario=`{r.get('scenario_id')}` · "
            f"conv=`{r.get('conversation_id') or '—'}` · "
            f"class=`{r.get('classification')}`"
        )
    if not (fix_q.get("items") or []):
        lines.append("- (none)")
    lines.append("")
    (bdir / "HANDOFF.md").write_text("\n".join(lines), encoding="utf-8")


def attach_session_review_placeholder(
    evidence: dict[str, Any],
    *,
    scenario_id: str,
    enqueue: bool = True,
) -> dict[str, Any]:
    """Mark findings as pending session review; optionally enqueue backlog item."""
    fin = evidence.get("findings") if isinstance(evidence.get("findings"), dict) else {}
    fin = dict(fin or {})
    fin["source"] = "session_reviewer_pending"
    fin["reviewer"] = "session_agent"
    fin["note"] = (
        (fin.get("note") or "")
        + f" Full findings: {session_agent_label()} — open Backlog tab or say "
        "'review conjecture backlog' in the coding session."
    ).strip()
    evidence["findings"] = fin
    if enqueue:
        try:
            item = enqueue_review(
                scenario_id=scenario_id,
                evidence=evidence,
                adapter=str((evidence.get("run") or {}).get("adapter") or ""),
                reason="post_run_session_review",
            )
            evidence["backlog_item_id"] = item.get("id")
            evidence["backlog_path"] = str(
                resolve_backlog_dir() / "items" / f"{item.get('id')}.json"
            )
        except Exception as exc:  # noqa: BLE001
            evidence["backlog_error"] = f"{type(exc).__name__}: {exc}"
    return evidence


__all__ = [
    "CLASSIFICATIONS",
    "STATUSES",
    "attach_session_review_placeholder",
    "close_open_with_patch",
    "close_with_patch",
    "enqueue_review",
    "findings_reviewer_mode",
    "get_backlog_item",
    "list_backlog",
    "resolve_backlog_dir",
    "session_agent_label",
    "update_backlog_item",
]
