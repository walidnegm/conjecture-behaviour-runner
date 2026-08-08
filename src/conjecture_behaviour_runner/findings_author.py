"""LLM **proposes** structured CAQ findings; code **validates** schema.

After a candidate run (geometry stub or host Driver), this module turns
raw evidence into the same analytical report shape used in live soaks:

* what should have happened
* what actually happened (turn table)
* expected vs observed
* what went wrong / root cause / code path
* seal recommendation

Split (AGENTS-shaped)
---------------------
* **LLM:** narrative + structured hypotheses under constrained JSON.
* **Code:** verdict coercion from ``run.passed`` / failures; schema clamp;
  preserve evidence turn table when model invents empty rows; write into
  evidence under ``findings``.

Reviewer modes (``CONJECTURE_FINDINGS_REVIEWER``)
-------------------------------------------------
* **session** (default) — code fills deterministic tables; enqueue backlog for
  the **session coding agent** (optional brand ``CONJECTURE_SESSION_AGENT_LABEL``)
  who has monorepo context + conversation ids. Invent/author may still use
  OpenAI/Claude.
* **openai** — portable OpenAI-compatible findings LLM (``CONJECTURE_FINDINGS_LLM_*``
  / invent LLM). No product host LLM factory.
* **deterministic** — tables only, no enqueue.

Env
---
CONJECTURE_FINDINGS_REVIEWER       session | openai | deterministic (default session)
CONJECTURE_FINDINGS_LLM=1          (openai mode) enable if LLM configured
CONJECTURE_FINDINGS_LLM_BASE_URL   optional; else invent LLM base
CONJECTURE_FINDINGS_LLM_MODEL
CONJECTURE_FINDINGS_LLM_API_KEY
CONJECTURE_FINDINGS_PROMPT_PATH    optional override of findings_author.md
CONJECTURE_BACKLOG_DIR             review backlog root
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

VERDICTS = frozenset({"PASS", "FAIL", "INCONCLUSIVE"})

KNOWN_FAILURE_SLUGS: frozenset[str] = frozenset({
    "missing_sole_continue",
    "delivery_order_gap",
    "packaging_too_wide",
    "missing_state_leaf",
    "pin_without_open",
    "hollow_async_advance",
    "true_glossary_detour",
    "compound_primary_secondary",
    "draft_improve_to_ir",
    "wrong_delivery_leaf",
    "owner_steal",
    "pin_drop",
    "illegal_restart",
    "hollow_open",
    "hollow_advance",
    "compound_act_loss",
    "fall_through_fabrication",
    "packaging_steal",
    "named_item_misresolve",
    "soft_name_misresolve",
    "ambient_pin_hijack",
    "cold_start_collapse",
})


@dataclass
class FindingsReport:
    """Code-owned findings payload (JSON-serializable)."""

    headline: str = ""
    verdict: str = "INCONCLUSIVE"
    what_should_have_happened: list[dict[str, Any]] = field(default_factory=list)
    what_actually_happened: list[dict[str, Any]] = field(default_factory=list)
    expected_vs_observed: list[dict[str, Any]] = field(default_factory=list)
    what_went_wrong: str = ""
    root_cause_hypothesis: str = ""
    code_path_hypothesis: str = ""
    failure_mode_slug: str = ""
    seal_recommendation: str = ""
    suggested_fixes: list[dict[str, Any]] = field(default_factory=list)
    classification: str = ""  # conjecture_caught | product_bug | …
    confidence: float = 0.0
    source: str = "deterministic"  # llm | deterministic | hybrid | session_reviewer_pending
    ok: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def findings_enabled() -> bool:
    """Whether after-run findings authoring should run.

    Session mode always runs (deterministic + backlog). OpenAI mode when LLM
    configured unless ``CONJECTURE_FINDINGS_LLM=0``.
    """
    from conjecture_behaviour_runner.review_backlog import findings_reviewer_mode

    mode = findings_reviewer_mode()
    if mode in ("session", "deterministic"):
        return True
    flag = (os.environ.get("CONJECTURE_FINDINGS_LLM") or "").strip().lower()
    if flag in ("0", "false", "no", "off"):
        return False
    if flag in ("1", "true", "yes", "on"):
        return True
    return _findings_llm_configured()


def _findings_llm_configured() -> bool:
    base = (
        (os.environ.get("CONJECTURE_FINDINGS_LLM_BASE_URL") or "").strip()
        or (os.environ.get("CONJECTURE_INVENT_LLM_BASE_URL") or "").strip()
    )
    model = (
        (os.environ.get("CONJECTURE_FINDINGS_LLM_MODEL") or "").strip()
        or (os.environ.get("CONJECTURE_INVENT_LLM_MODEL") or "").strip()
    )
    key = (
        (os.environ.get("CONJECTURE_FINDINGS_LLM_API_KEY") or "").strip()
        or (os.environ.get("CONJECTURE_INVENT_LLM_API_KEY") or "").strip()
        or (os.environ.get("OPENAI_API_KEY") or "").strip()
    )
    return bool(base and model and key)


def _load_prompt_template() -> str:
    override = (os.environ.get("CONJECTURE_FINDINGS_PROMPT_PATH") or "").strip()
    if override:
        p = Path(override).expanduser()
        if p.is_file():
            return p.read_text(encoding="utf-8")
    here = Path(__file__).resolve().parent / "prompts" / "findings_author.md"
    if here.is_file():
        return here.read_text(encoding="utf-8")
    return (
        "Analyze scenario + evidence. Return JSON with headline, verdict, "
        "what_should_have_happened, what_actually_happened, expected_vs_observed, "
        "what_went_wrong, root_cause_hypothesis, code_path_hypothesis, "
        "failure_mode_slug, seal_recommendation, confidence.\n\n"
        "Scenario:\n{scenario_json}\n\nEvidence:\n{evidence_json}\n\n"
        "Slugs:\n{failure_slugs}\n"
    )


def _extract_json(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _turn_rows(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for i, row in enumerate(raw):
        if not isinstance(row, Mapping):
            continue
        out.append({
            "index": int(row.get("index", i)),
            "role": str(row.get("role") or "user")[:40],
            "what_happened": str(
                row.get("what_happened") or row.get("body") or row.get("text") or ""
            )[:2000],
        })
    return out


def _evo_rows(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for row in raw:
        if not isinstance(row, Mapping):
            continue
        out.append({
            "aspect": str(row.get("aspect") or "")[:120],
            "expected": str(row.get("expected") or "")[:500],
            "observed": str(row.get("observed") or "")[:500],
            "match": bool(row.get("match")),
        })
    return out


def _coerce_verdict(
    proposed: str,
    *,
    run_passed: bool | None,
    failures: Sequence[str],
) -> str:
    v = (proposed or "").strip().upper()
    if v not in VERDICTS:
        v = "INCONCLUSIVE"
    # Code owns hard truth from harness when decisive
    if failures or run_passed is False:
        return "FAIL"
    if run_passed is True and not failures and v == "INCONCLUSIVE":
        return "PASS"
    if run_passed is True and v == "FAIL":
        # Model pessimism — keep FAIL only if they listed mismatches; else PASS
        return "PASS"
    return v


def build_deterministic_findings(
    *,
    scenario: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> FindingsReport:
    """Code-only findings when LLM is off or fails — still fills the tables."""
    sc = dict(scenario or {})
    ev = dict(evidence or {})
    run = ev.get("run") if isinstance(ev.get("run"), Mapping) else {}
    run = dict(run or {})
    wah = ev.get("what_actually_happened") if isinstance(
        ev.get("what_actually_happened"), Mapping
    ) else {}
    wah = dict(wah or {})
    passed = run.get("passed")
    failures = [str(f) for f in (run.get("failures") or [])]
    slug = str(
        sc.get("failure_mode")
        or (sc.get("geometry") or {}).get("mode")
        or wah.get("failure_mode")
        or ""
    )
    exp = sc.get("expected_invariant") if isinstance(sc.get("expected_invariant"), Mapping) else {}
    must_hold = list(exp.get("machine") or [])
    if not must_hold and isinstance(sc.get("must_hold"), list):
        must_hold = [str(x) for x in sc["must_hold"]]

    should_rows: list[dict[str, Any]] = []
    purpose = str(sc.get("scenario_purpose") or sc.get("user_trajectory") or "").strip()
    if purpose:
        should_rows.append({
            "index": 0,
            "role": "system",
            "what_happened": f"Law / purpose: {purpose[:800]}",
        })
    for i, m in enumerate(must_hold[:12]):
        should_rows.append({
            "index": i + 1,
            "role": "system",
            "what_happened": f"Must hold: {m}",
        })
    if exp.get("prose"):
        should_rows.append({
            "index": len(should_rows),
            "role": "system",
            "what_happened": f"Expected: {str(exp.get('prose'))[:800]}",
        })

    actual = _turn_rows(wah.get("turns"))
    if not actual:
        actual = _turn_rows(sc.get("incident_turns"))

    evo: list[dict[str, Any]] = []
    if must_hold:
        evo.append({
            "aspect": "must_hold",
            "expected": "; ".join(str(x) for x in must_hold[:6]),
            "observed": (
                "PASS" if passed else (
                    "; ".join(failures[:6]) if failures else "FAIL (no detail)"
                )
            ),
            "match": bool(passed) and not failures,
        })
    owner_exp = ""
    for m in must_hold:
        if "owner" in str(m).lower() or "exclusive" in str(m).lower():
            owner_exp = str(m)
            break
    if owner_exp:
        # Best-effort from last observation
        last_owner = ""
        for t in reversed(actual):
            wh = t.get("what_happened") or ""
            if "owner=" in wh:
                last_owner = wh
                break
        evo.append({
            "aspect": "exclusive_owner",
            "expected": owner_exp,
            "observed": last_owner or "(not observed)",
            "match": bool(passed),
        })

    if passed and not failures:
        verdict = "PASS"
        headline = f"PASS — {sc.get('scenario_id') or 'candidate'} held expected law"
        wrong = ""
        root = wah.get("root_cause") or ""
        code_path = wah.get("code_path") or ""
        seal = ""
    else:
        verdict = "FAIL"
        headline = (
            f"FAIL — {sc.get('scenario_id') or 'candidate'}"
            + (f" · {slug}" if slug else "")
        )
        wrong = (
            "; ".join(failures)
            or str(wah.get("root_cause") or "")
            or "Run failed without structured failure list"
        )
        root = str(wah.get("root_cause") or "unknown — see mode_detection / failures")
        code_path = str(wah.get("code_path") or "")
        seal = (
            "Seal at earliest wrong layer (exclusive owner / referential / "
            "delivery leaf); add STEAL row + path-faithful ratchet — not phrase laundry."
        )

    return FindingsReport(
        headline=headline,
        verdict=verdict,
        what_should_have_happened=should_rows,
        what_actually_happened=actual,
        expected_vs_observed=evo,
        what_went_wrong=str(wrong)[:2000],
        root_cause_hypothesis=str(root)[:2000],
        code_path_hypothesis=str(code_path)[:2000],
        failure_mode_slug=slug if verdict == "FAIL" else (slug if slug else ""),
        seal_recommendation=seal[:2000],
        confidence=0.55 if verdict != "INCONCLUSIVE" else 0.3,
        source="deterministic",
        ok=True,
    )


def validate_findings_payload(
    raw: Mapping[str, Any],
    *,
    scenario: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> FindingsReport:
    """Clamp LLM JSON into FindingsReport; merge with evidence tables."""
    det = build_deterministic_findings(scenario=scenario, evidence=evidence)
    run = evidence.get("run") if isinstance(evidence.get("run"), Mapping) else {}
    run = dict(run or {})
    failures = [str(f) for f in (run.get("failures") or [])]
    passed = run.get("passed") if "passed" in run else None

    verdict = _coerce_verdict(
        str(raw.get("verdict") or ""),
        run_passed=passed if isinstance(passed, bool) else None,
        failures=failures,
    )
    should = _turn_rows(raw.get("what_should_have_happened")) or det.what_should_have_happened
    actual = _turn_rows(raw.get("what_actually_happened")) or det.what_actually_happened
    evo = _evo_rows(raw.get("expected_vs_observed")) or det.expected_vs_observed

    slug = str(raw.get("failure_mode_slug") or "").strip()
    if slug and slug not in KNOWN_FAILURE_SLUGS:
        # allow scenario's own slug even if not in portable set
        sc_slug = str(
            scenario.get("failure_mode")
            or (scenario.get("geometry") or {}).get("mode")
            or ""
        ).strip()
        if slug != sc_slug:
            slug = sc_slug or det.failure_mode_slug
    if not slug:
        slug = det.failure_mode_slug if verdict == "FAIL" else ""

    try:
        conf = float(raw.get("confidence") or 0.0)
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))

    fixes_raw = raw.get("suggested_fixes")
    fixes: list[dict[str, Any]] = []
    if isinstance(fixes_raw, list):
        for fx in fixes_raw[:12]:
            if not isinstance(fx, Mapping):
                continue
            fixes.append({
                "priority": str(fx.get("priority") or "P1")[:8],
                "title": str(fx.get("title") or "")[:200],
                "layer": str(fx.get("layer") or "")[:64],
                "files": [str(f)[:200] for f in (fx.get("files") or [])[:12]],
                "action": str(fx.get("action") or "")[:2000],
                "ratchet": str(fx.get("ratchet") or "")[:300],
            })
    classification = str(raw.get("classification") or "").strip().lower()[:40]

    return FindingsReport(
        headline=str(raw.get("headline") or det.headline)[:400],
        verdict=verdict,
        what_should_have_happened=should,
        what_actually_happened=actual,
        expected_vs_observed=evo,
        what_went_wrong=str(raw.get("what_went_wrong") or det.what_went_wrong)[:2000],
        root_cause_hypothesis=str(
            raw.get("root_cause_hypothesis") or det.root_cause_hypothesis
        )[:2000],
        code_path_hypothesis=str(
            raw.get("code_path_hypothesis") or det.code_path_hypothesis
        )[:2000],
        failure_mode_slug=slug[:80],
        seal_recommendation=str(
            raw.get("seal_recommendation") or det.seal_recommendation
        )[:2000],
        suggested_fixes=fixes,
        classification=classification,
        confidence=conf or det.confidence,
        source="hybrid",
        ok=True,
    )


def _env_llm_complete(prompt: str) -> str:
    """OpenAI-compatible chat completion using findings or invent env."""
    from conjecture_behaviour_runner.candidate_author.invent_config import (
        InventConfig,
        env_llm_complete,
        load_invent_config,
    )

    inv = load_invent_config()
    base = (
        (os.environ.get("CONJECTURE_FINDINGS_LLM_BASE_URL") or "").strip()
        or (inv.llm_base_url or "")
        or ""
    )
    model = (
        (os.environ.get("CONJECTURE_FINDINGS_LLM_MODEL") or "").strip()
        or (inv.llm_model or "")
        or ""
    )
    key = (
        (os.environ.get("CONJECTURE_FINDINGS_LLM_API_KEY") or "").strip()
        or (inv.llm_api_key or "")
        or (os.environ.get("OPENAI_API_KEY") or "").strip()
        or ""
    )
    try:
        timeout = float(
            os.environ.get("CONJECTURE_FINDINGS_LLM_TIMEOUT_S")
            or inv.llm_timeout_s
            or 60
        )
    except (TypeError, ValueError):
        timeout = 60.0
    cfg = InventConfig(
        max_proposals=inv.max_proposals,
        max_scenarios=inv.max_scenarios,
        prompt_path=inv.prompt_path,
        llm_base_url=base.rstrip("/") if base else None,
        llm_model=model or None,
        llm_api_key=key or None,
        llm_timeout_s=timeout,
    )
    return env_llm_complete(prompt, cfg=cfg)


def author_findings(
    *,
    scenario: Mapping[str, Any],
    evidence: Mapping[str, Any],
    llm_complete: Optional[Callable[[str], str]] = None,
    use_llm: bool | None = None,
) -> FindingsReport:
    """Produce findings for one scenario + evidence package.

    ``use_llm``: None → ``findings_enabled()``; False → deterministic only.
    """
    want_llm = findings_enabled() if use_llm is None else bool(use_llm)
    if not want_llm and llm_complete is None:
        return build_deterministic_findings(scenario=scenario, evidence=evidence)

    completer = llm_complete
    if completer is None:
        if not _findings_llm_configured():
            return build_deterministic_findings(scenario=scenario, evidence=evidence)
        completer = _env_llm_complete

    # Slim payloads for the model
    sc_slim = {
        k: scenario.get(k)
        for k in (
            "scenario_id",
            "incident_id",
            "failure_mode",
            "scenario_purpose",
            "user_trajectory",
            "geometry",
            "expected_invariant",
            "mode_detection",
            "failure_oracle",
            "must_hold",
            "must_not",
            "ledger_note",
            "code_path",
            "root_cause",
            "incident_turns",
            "proof_pointer",
        )
        if scenario.get(k) is not None
    }
    ev_slim = {
        "scenario_id": evidence.get("scenario_id"),
        "taxonomy": evidence.get("taxonomy"),
        "candidate_split": evidence.get("candidate_split"),
        "what_actually_happened": evidence.get("what_actually_happened"),
        "run": {
            "passed": (evidence.get("run") or {}).get("passed")
            if isinstance(evidence.get("run"), Mapping)
            else None,
            "failures": (evidence.get("run") or {}).get("failures")
            if isinstance(evidence.get("run"), Mapping)
            else [],
            "adapter": (evidence.get("run") or {}).get("adapter")
            if isinstance(evidence.get("run"), Mapping)
            else None,
            "turns": (
                (evidence.get("run") or {}).get("turns") or []
            )[:12]
            if isinstance(evidence.get("run"), Mapping)
            else [],
        },
        "note": evidence.get("note"),
        "product_path": evidence.get("product_path"),
        "account": evidence.get("account"),
    }
    # Use replace (not str.format) — prompt body contains JSON example braces.
    prompt = (
        _load_prompt_template()
        .replace(
            "{scenario_json}",
            json.dumps(sc_slim, indent=2, default=str)[:12000],
        )
        .replace(
            "{evidence_json}",
            json.dumps(ev_slim, indent=2, default=str)[:16000],
        )
        .replace(
            "{failure_slugs}",
            ", ".join(sorted(KNOWN_FAILURE_SLUGS)),
        )
    )
    try:
        raw_text = completer(prompt)
    except Exception as exc:  # noqa: BLE001
        det = build_deterministic_findings(scenario=scenario, evidence=evidence)
        det.source = "deterministic"
        det.error = f"llm_failed: {type(exc).__name__}: {exc}"
        det.ok = True  # still return usable deterministic findings
        return det

    parsed = _extract_json(raw_text or "")
    if not parsed:
        det = build_deterministic_findings(scenario=scenario, evidence=evidence)
        det.error = "llm_json_parse_failed"
        det.source = "deterministic"
        return det

    report = validate_findings_payload(parsed, scenario=scenario, evidence=evidence)
    report.source = "llm"
    return report


def attach_findings_to_evidence(
    evidence: dict[str, Any],
    *,
    scenario: Mapping[str, Any] | None = None,
    llm_complete: Optional[Callable[[str], str]] = None,
    use_llm: bool | None = None,
    enqueue_backlog: bool | None = None,
) -> dict[str, Any]:
    """Mutate/return evidence with ``findings`` key populated.

    Default reviewer = **session** (session-agent handoff). OpenAI only when
    ``CONJECTURE_FINDINGS_REVIEWER=openai`` or ``use_llm=True`` explicitly.
    """
    from conjecture_behaviour_runner.review_backlog import (
        attach_session_review_placeholder,
        findings_reviewer_mode,
    )

    sc = scenario if isinstance(scenario, Mapping) else {}
    if not sc and isinstance(evidence.get("scenario"), Mapping):
        sc = evidence["scenario"]  # type: ignore[assignment]
    # Reconstruct minimal scenario from evidence taxonomy if needed
    if not sc:
        tax = evidence.get("taxonomy") if isinstance(evidence.get("taxonomy"), Mapping) else {}
        split = evidence.get("candidate_split") if isinstance(
            evidence.get("candidate_split"), Mapping
        ) else {}
        sc = {
            "scenario_id": evidence.get("scenario_id") or tax.get("candidate_scenario"),
            "incident_id": tax.get("incident"),
            "failure_mode": tax.get("failure_mode") or split.get("failure_mode_mapping"),
            "user_trajectory": split.get("user_trajectory"),
            "geometry": split.get("scenario_geometry"),
            "mode_detection": split.get("mode_detection"),
            "scenario_purpose": evidence.get("scenario_purpose"),
            "expected_invariant": evidence.get("expected_invariant"),
        }

    mode = findings_reviewer_mode()
    # Explicit use_llm=True forces openai path; use_llm=False forces deterministic only
    if use_llm is True:
        mode = "openai"
    elif use_llm is False:
        mode = "deterministic"

    if mode == "openai":
        report = author_findings(
            scenario=sc,
            evidence=evidence,
            llm_complete=llm_complete,
            use_llm=True,
        )
    else:
        # session | deterministic — code-owned skeleton (no OpenAI review)
        report = author_findings(
            scenario=sc,
            evidence=evidence,
            llm_complete=None,
            use_llm=False,
        )
        if mode == "session":
            report.source = "session_reviewer_pending"

    evidence["findings"] = report.to_dict()
    if mode == "session":
        evidence["findings"]["reviewer"] = "session_agent"
        evidence["findings"]["source"] = "session_reviewer_pending"
        from conjecture_behaviour_runner.review_backlog import session_agent_label

        evidence["findings"]["note"] = (
            f"Pending {session_agent_label()} review — monorepo + conversation id. "
            "Open Backlog tab or say: review conjecture backlog"
        )

    # Enrich what_actually_happened narrative from findings when richer
    wah = evidence.get("what_actually_happened")
    if isinstance(wah, dict) and report.what_actually_happened:
        if len(report.what_actually_happened) >= len(wah.get("turns") or []):
            wah = dict(wah)
            wah["turns"] = report.what_actually_happened
            if report.root_cause_hypothesis and not wah.get("root_cause"):
                wah["root_cause"] = report.root_cause_hypothesis
            if report.code_path_hypothesis and not wah.get("code_path"):
                wah["code_path"] = report.code_path_hypothesis
            evidence["what_actually_happened"] = wah

    # Enqueue for session agent (default on for session mode)
    do_enqueue = enqueue_backlog
    if do_enqueue is None:
        do_enqueue = mode == "session"
    if do_enqueue:
        sid = str(
            sc.get("scenario_id")
            or evidence.get("scenario_id")
            or "unknown"
        )
        attach_session_review_placeholder(
            evidence,
            scenario_id=sid,
            enqueue=True,
        )
    return evidence


__all__ = [
    "FindingsReport",
    "KNOWN_FAILURE_SLUGS",
    "attach_findings_to_evidence",
    "author_findings",
    "build_deterministic_findings",
    "findings_enabled",
    "validate_findings_payload",
]
