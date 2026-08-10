"""Safe admin / environment visibility for the local Conjecture console.

Never returns secret values — only whether they are set, and non-secret
config (base URLs, models, account email, candidates dir, host driver).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping


def _mask_secret(value: str | None) -> dict[str, Any]:
    raw = (value or "").strip()
    if not raw:
        return {"set": False, "preview": None, "length": 0}
    # last 4 only when long enough
    tail = raw[-4:] if len(raw) >= 8 else "****"
    return {"set": True, "preview": f"…{tail}", "length": len(raw)}


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def console_admin_status() -> dict[str, Any]:
    """JSON for GET /api/admin/status — environment + host account visibility."""
    from conjecture_behaviour_runner.candidate_author.invent_config import (
        load_invent_config,
    )
    from conjecture_behaviour_runner.candidate_run import host_runner_status
    from conjecture_behaviour_runner.candidates_ui import resolve_candidates_dir
    from conjecture_behaviour_runner.host_env import host_connection_status

    invent = load_invent_config()
    cdir = resolve_candidates_dir()
    host = host_runner_status()
    account = host_connection_status()

    invent_key = invent.llm_api_key or _env("OPENAI_API_KEY")
    # Display-only resolution for optional openai findings path (may fall back to invent)
    findings_base = _env("CONJECTURE_FINDINGS_LLM_BASE_URL") or invent.llm_base_url or ""
    findings_model = _env("CONJECTURE_FINDINGS_LLM_MODEL") or invent.llm_model or ""
    findings_key = (
        _env("CONJECTURE_FINDINGS_LLM_API_KEY")
        or invent_key
        or ""
    )

    # Portable harness title prefixes only — host monorepo may extend via driver
    title_prefixes: list[str] = ["cbr-", "conjecture-e2e", "conjecture"]
    try:
        from regression_suite.conjecture_bot0_http_driver import (  # type: ignore
            CONJECTURE_TITLE_PREFIXES,
        )

        title_prefixes = list(CONJECTURE_TITLE_PREFIXES)
    except Exception:  # noqa: BLE001
        pass

    return {
        "ok": True,
        "account": account,
        "host_driver": host,
        "candidates": {
            "dir": str(cdir) if cdir else None,
            "env": _env("CONJECTURE_CANDIDATES_DIR") or None,
            "resolved": bool(cdir),
        },
        "invent_llm": {
            "configured": invent.llm_configured,
            "base_url": invent.llm_base_url,
            "model": invent.llm_model,
            "api_key": _mask_secret(invent_key),
            "timeout_s": invent.llm_timeout_s,
            "max_proposals": invent.max_proposals,
            "max_scenarios": invent.max_scenarios,
            "prompt_path": invent.prompt_path
            or str(
                Path(__file__).resolve().parent
                / "candidate_author"
                / "prompts"
                / "geometry_propose.md"
            ),
            "env_keys": [
                "CONJECTURE_INVENT_LLM_BASE_URL",
                "CONJECTURE_INVENT_LLM_MODEL",
                "CONJECTURE_INVENT_LLM_API_KEY",
                "OPENAI_API_KEY (fallback)",
            ],
        },
        "findings_reviewer": _findings_reviewer_status(),
        "findings_llm": _findings_llm_status(
            invent_base=invent.llm_base_url or "",
            invent_model=invent.llm_model or "",
            invent_key=invent_key or "",
            findings_base=findings_base,
            findings_model=findings_model,
            findings_key=findings_key,
        ),
        "cleanup": {
            "title_prefixes": title_prefixes,
            "api": "POST /api/cleanup-conversations",
            "product_action": "DELETE /api/conversations/{id} (archive)",
            "account": account.get("email"),
            "account_set": bool(account.get("email_set")),
        },
        # Portable abuse-control notes (+ optional host profile overlay).
        # Extract package must stay product-agnostic; Bot0 param names only
        # when host profile is bot0.
        "host_abuse_controls": _host_abuse_controls_status(host),
        # Back-compat alias for older console JS
        "product_limits_note": _product_limits_note_compat(host),
        "console": {
            "cwd": str(Path.cwd()),
            "python": os.environ.get("VIRTUAL_ENV") or None,
        },
        "warnings": _warnings(invent.llm_configured, host, invent_key),
    }


def _findings_reviewer_status() -> dict[str, Any]:
    """Primary post-run path — default is session agent + Backlog handoff."""
    from conjecture_behaviour_runner.review_backlog import (
        findings_reviewer_mode,
        resolve_backlog_dir,
    )

    mode = findings_reviewer_mode()
    from conjecture_behaviour_runner.review_backlog import session_agent_label

    label = session_agent_label()
    notes = {
        "session": (
            f"Active: {label} reviews each run (monorepo + conversation ids). "
            "Code writes a thin findings skeleton, then enqueues Backlog. "
            "Commands: review conjecture backlog → fix."
        ),
        "openai": (
            "Active: remote findings LLM "
            "(CONJECTURE_FINDINGS_LLM_* or invent-compatible endpoint)."
        ),
        "deterministic": (
            "Active: code-owned tables only — no session handoff, no remote findings LLM."
        ),
    }
    delivery = {
        "session": "session handoff (Verdict queue / backlog)",
        "openai": "remote findings LLM",
        "deterministic": "code tables only",
    }
    return {
        "mode": mode,
        "default": "session",
        "active": True,
        "session_agent_label": label,
        "delivery": delivery.get(mode, delivery["session"]),
        "uses_openai_findings": mode == "openai",  # API compat; UI no longer leads with this
        "uses_backlog_handoff": mode == "session",
        "command_review": "review conjecture backlog",
        "command_fix": "fix",
        "note": notes.get(mode, notes["session"]),
        "backlog_dir": str(resolve_backlog_dir()),
        "env": "CONJECTURE_FINDINGS_REVIEWER (default: session)",
        "env_label": "CONJECTURE_SESSION_AGENT_LABEL (optional display name)",
        "modes_available": "session · deterministic · openai (optional remote)",
    }


def _findings_llm_status(
    *,
    invent_base: str,
    invent_model: str,
    invent_key: str,
    findings_base: str,
    findings_model: str,
    findings_key: str,
) -> dict[str, Any]:
    """Optional OpenAI findings path — only active when mode=openai."""
    from conjecture_behaviour_runner.findings_author import (
        _findings_llm_configured,
        findings_enabled,
    )
    from conjecture_behaviour_runner.review_backlog import findings_reviewer_mode

    mode = findings_reviewer_mode()
    # Resolve effective endpoints the openai path would use (invent fallback)
    base = findings_base or invent_base or ""
    model = findings_model or invent_model or ""
    key = findings_key or invent_key or ""
    # Prefer env-aware check; also treat invent-resolved triple as configured
    env_ok = _findings_llm_configured()
    resolved_ok = bool(base and model and key)
    configured = env_ok or resolved_ok
    in_use = mode == "openai"

    return {
        # "enabled" historically meant findings_enabled() (always true in session).
        # That misled Admin into "Findings LLM on". Now: openai path active only.
        "enabled": in_use,
        "in_use": in_use,
        "mode_required": "openai",
        "current_reviewer_mode": mode,
        "configured": configured,
        "base_url": base or "—",
        "model": model or "—",
        "api_key": _mask_secret(key),
        "falls_back_to_invent": not bool(_env("CONJECTURE_FINDINGS_LLM_BASE_URL")),
        "env_flag": _env("CONJECTURE_FINDINGS_LLM") or "(only when mode=openai)",
        "env_keys": [
            "CONJECTURE_FINDINGS_LLM",
            "CONJECTURE_FINDINGS_LLM_BASE_URL",
            "CONJECTURE_FINDINGS_LLM_MODEL",
            "CONJECTURE_FINDINGS_LLM_API_KEY",
        ],
        "prompt_path": _env("CONJECTURE_FINDINGS_PROMPT_PATH")
        or str(
            Path(__file__).resolve().parent / "prompts" / "findings_author.md"
        ),
        "note": (
            "Idle — session mode is the active reviewer. "
            "This card only applies when CONJECTURE_FINDINGS_REVIEWER=openai. "
            "Invent LLM (scenario invent) is separate and may still be configured."
            if not in_use
            else (
                "In use for post-run findings tables. "
                + ("Ready." if configured else "Incomplete — set base + model + API key.")
            )
        ),
        # Keep for callers that still check findings_enabled() semantics
        "post_run_skeleton_enabled": findings_enabled(),
    }


def _host_abuse_controls_status(
    host: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Admin card: portable categories ⊕ optional host SPI fill-in.

    See :mod:`conjecture_behaviour_runner.host_limits`.
    """
    from conjecture_behaviour_runner.host_limits import resolve_host_limits_catalog

    return resolve_host_limits_catalog(host)


def _product_limits_note_compat(
    host: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Flat key→detail map for older UI; prefer host_abuse_controls.rows."""
    ctrl = _host_abuse_controls_status(host)
    flat: dict[str, str] = {
        "title": str(ctrl.get("title") or ""),
        "lead": str(ctrl.get("lead") or ""),
        "tune_hint": str(ctrl.get("tune_hint") or ""),
        "host_profile": str(ctrl.get("host_profile") or "generic"),
        "source": str(ctrl.get("source") or "portable"),
    }
    for row in ctrl.get("rows") or []:
        if isinstance(row, Mapping) and row.get("key"):
            k = str(row["key"])
            detail = str(row.get("detail") or "")
            knob = row.get("host_knob")
            if knob and knob not in detail:
                detail = f"{knob}: {detail}" if detail else str(knob)
            flat[k] = detail
            # legacy aliases some UIs used
            if k == "chat":
                flat["bot0_chat"] = detail
            if k == "thread_create":
                flat["conversation_create"] = detail
    return flat


def _warnings(
    invent_ok: bool,
    host: dict[str, Any],
    invent_key: str | None,
) -> list[str]:
    out: list[str] = []
    if not invent_ok:
        out.append(
            "Invent LLM not fully configured — geometry invent proposals need "
            "CONJECTURE_INVENT_LLM_BASE_URL + MODEL + API_KEY."
        )
    if not host.get("available"):
        out.append(
            "Host HTTP driver not available — set CONJECTURE_HOST_RUNNER=module:callable "
            "or install a host monorepo adapter."
        )
    elif not host.get("password_set"):
        out.append(
            "CONJECTURE_HOST_PASSWORD (or CONJECTURE_BOT0_PASSWORD alias) is not set — "
            "host runs / cleanup will fail."
        )
    if host.get("available") and not host.get("account"):
        out.append(
            "CONJECTURE_HOST_EMAIL is not set — host E2E has no product account identity."
        )
    if host.get("available") and not host.get("base_url"):
        out.append(
            "CONJECTURE_HOST_BASE_URL is not set — host E2E has no product API base."
        )
    if invent_key and invent_key.startswith("sk-") is False and len(invent_key) < 8:
        out.append("Invent API key looks unusually short.")
    try:
        from conjecture_behaviour_runner.findings_author import _findings_llm_configured
        from conjecture_behaviour_runner.review_backlog import findings_reviewer_mode

        if findings_reviewer_mode() == "openai" and not _findings_llm_configured():
            out.append(
                "Findings reviewer mode is openai but Findings LLM is incomplete — "
                "set CONJECTURE_FINDINGS_LLM_* or invent LLM fallback."
            )
    except Exception:  # noqa: BLE001
        pass
    return out


__all__ = ["console_admin_status"]
