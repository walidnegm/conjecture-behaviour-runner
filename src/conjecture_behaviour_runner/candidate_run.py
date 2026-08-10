"""Run a candidate scenario → execution evidence (taxonomy-shaped).

Architecture is **file-based**:
  candidates/scenarios/*.yaml     — authored scenarios (may be generated)
  candidates/scenarios/evidence/  — run results (local; gitignore)

The local console is not a full host driver. Default adapter **holds geometry**
from the scenario pin (exclusive_surface stays owner) so invent/expand candidates
can produce structured evidence without Bot0. Hosts replace adapter with a real
control-plane Driver for path-faithful runs.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from conjecture_behaviour_runner.candidates_ui import get_candidate, resolve_candidates_dir
from conjecture_behaviour_runner.modes import LlmMode
from conjecture_behaviour_runner.protocol import TurnObservation
from conjecture_behaviour_runner.script import InvariantSpec


class GeometryHoldAdapter:
    """Stub Driver: after setup, exclusive_owner = pin exclusive_surface.

    If ``steal=True``, yields ownership to pin stealer / competing leaf so
    mode detection can show a FAIL (planted soft enforcement).
    """

    def __init__(self, *, steal: bool = False) -> None:
        self.steal = steal
        self._owner: Optional[str] = None
        self._pins: dict[str, str] = {}

    def apply_effect(self, context: dict[str, Any], effect: Any) -> dict[str, Any]:
        return dict(context)

    def observe_turn(
        self,
        *,
        context: dict[str, Any],
        user_text: str,
        pin: Any,
    ) -> TurnObservation:
        p: dict[str, Any] = {}
        if pin is not None and hasattr(pin, "to_dict"):
            p = pin.to_dict() or {}
        elif isinstance(pin, Mapping):
            p = dict(pin)
        extras = p.get("extras") if isinstance(p.get("extras"), dict) else {}
        surface = str(
            p.get("exclusive_surface")
            or extras.get("exclusive_surface")
            or self._owner
            or ""
        )
        stealer = str(
            p.get("stealer")
            or p.get("competing_leaf")
            or extras.get("stealer")
            or extras.get("competing_leaf")
            or p.get("read_kind")
            or ""
        )
        if surface in ("", "continue", "default", "none"):
            surface = self._owner or "armed_list_pick"
        if self._owner is None:
            self._owner = surface
        if not self.steal:
            owner = self._owner
            outcome = "continue_owned"
        else:
            owner = stealer or "stolen_owner"
            self._owner = owner
            outcome = "owner_steal"
        self._pins = {
            k: str(v) for k, v in {**extras, **p}.items()
            if k not in ("reason", "extras") and not isinstance(v, (dict, list))
        }
        return TurnObservation(
            exclusive_owner=owner,
            active_kind=owner,
            pins=dict(self._pins),
            context=dict(context),
            observed_outcome=outcome,
            extras={
                "user_text": user_text,
                "adapter": "GeometryHoldAdapter",
                "steal": self.steal,
                "surface": surface,
                "stealer": stealer,
            },
        )

    def check_invariant(
        self,
        *,
        observation: TurnObservation,
        context: Mapping[str, Any],
        spec: InvariantSpec,
    ) -> Optional[str]:
        if spec.kind == "always_true":
            return None
        if spec.kind == "exclusive_owner":
            exp = str(spec.expected or "")
            if "≈" in exp:
                exp = exp.split("≈", 1)[-1].strip()
            got = str(observation.exclusive_owner or "")
            if exp and got != exp:
                return f"exclusive_owner expected={exp!r} got={got!r}"
            return None
        if spec.kind == "active_kind":
            exp = str(spec.expected or "")
            got = str(observation.active_kind or "")
            if exp and got != exp:
                return f"active_kind expected={exp!r} got={got!r}"
            return None
        return None


def _evidence_dir(cdir: Path) -> Path:
    d = cdir / "evidence"
    d.mkdir(parents=True, exist_ok=True)
    return d


def build_what_actually_happened(
    *,
    scenario: Mapping[str, Any],
    run_result: Mapping[str, Any],
    adapter_name: str,
    steal: bool,
) -> dict[str, Any]:
    """Incident-shaped turn table for evidence (conv_1732aa88 report form).

    Structure (stable keys for console + host soak reports)::

        what_actually_happened:
          incident_id: …
          turns: [{index, role, what_happened}, …]
          ledger: …
          code_path: …
          root_cause: …
          verdict: PASS|FAIL

    Prefer authored scenario fields when present; else derive from trajectory
    steps + run observations.
    """
    sc = dict(scenario or {})
    pre = sc.get("what_actually_happened")
    if isinstance(pre, Mapping) and pre.get("turns"):
        out = dict(pre)
        out.setdefault("incident_id", sc.get("incident_id") or sc.get("scenario_id"))
        out["verdict"] = (
            "PASS" if run_result.get("passed") else "FAIL"
        )
        out["adapter"] = adapter_name
        out["planted_steal"] = bool(steal)
        return out

    turns_out: list[dict[str, Any]] = []
    # Authored narrative table (list of {role, what_happened})
    authored = sc.get("incident_turns") or sc.get("observed_turns")
    if isinstance(authored, list) and authored:
        for i, row in enumerate(authored):
            if not isinstance(row, Mapping):
                continue
            turns_out.append({
                "index": int(row.get("index", i)),
                "role": str(row.get("role") or "user"),
                "what_happened": str(
                    row.get("what_happened") or row.get("body") or row.get("text") or ""
                ),
            })
    else:
        # Trajectory steps as setup/user twists
        traj = sc.get("trajectory") if isinstance(sc.get("trajectory"), Mapping) else {}
        steps = list(sc.get("steps") or traj.get("steps") or [])
        for i, st in enumerate(steps):
            if not isinstance(st, Mapping):
                continue
            role = "user"
            setup = (
                st.get("role") == "setup"
                or st.get("setup_only")
                or str(st.get("maneuver") or "").startswith("establish")
            )
            text = str(
                st.get("user_behavior")
                or st.get("user_text")
                or (st.get("payload") or {}).get("user_text")
                or ""
            )
            if setup:
                turns_out.append({
                    "index": i,
                    "role": "setup",
                    "what_happened": text or "Establish start state",
                })
            else:
                turns_out.append({
                    "index": i,
                    "role": "user",
                    "what_happened": text or "continue",
                })
        # Observed assistant acts from run turns
        run_turns = list(
            run_result.get("turns") or run_result.get("turn_results") or []
        )
        base = len(turns_out)
        for j, rt in enumerate(run_turns):
            if not isinstance(rt, Mapping):
                continue
            obs = rt.get("observation") if isinstance(rt.get("observation"), Mapping) else {}
            ex = obs.get("extras") if isinstance(obs.get("extras"), Mapping) else {}
            owner = obs.get("exclusive_owner") or ""
            outcome = obs.get("observed_outcome") or rt.get("outcome") or ""
            sent = ex.get("user_text_sent") or ""
            what = (
                f"adapter={adapter_name}; owner={owner}; outcome={outcome}"
                + (f"; sent={sent!r}" if sent else "")
            )
            turns_out.append({
                "index": base + j,
                "role": "assistant/observation",
                "what_happened": what,
            })

    ledger = str(
        sc.get("ledger_note")
        or (sc.get("expected_invariant") or {}).get("prose")
        or ""
    )
    code_path = str(
        sc.get("code_path")
        or (sc.get("geometry") or {}).get("code_path")
        or ""
    )
    root = str(
        sc.get("root_cause")
        or "; ".join(
            str(x) for x in (sc.get("mode_detection") or sc.get("failure_oracle") or [])
        )
        or ""
    )
    return {
        "incident_id": sc.get("incident_id") or sc.get("scenario_id"),
        "failure_mode": sc.get("failure_mode") or (sc.get("geometry") or {}).get("mode"),
        "turns": turns_out,
        "ledger": ledger,
        "code_path": code_path,
        "root_cause": root,
        "verdict": "PASS" if run_result.get("passed") else "FAIL",
        "adapter": adapter_name,
        "planted_steal": bool(steal),
        "note": (
            "Turn table for incident soak / console report card. "
            "Prefer authored incident_turns when sealing a live conv."
        ),
    }


def build_taxonomy_evidence(
    *,
    scenario: dict[str, Any],
    run_result: dict[str, Any],
    adapter_name: str,
    steal: bool,
) -> dict[str, Any]:
    """Shape execution evidence using the working taxonomy + candidate split."""
    geo = scenario.get("geometry") or {}
    exp = scenario.get("expected_invariant") or {}
    detect = list(scenario.get("mode_detection") or scenario.get("failure_oracle") or [])
    wah = build_what_actually_happened(
        scenario=scenario,
        run_result=run_result,
        adapter_name=adapter_name,
        steal=steal,
    )
    return {
        "taxonomy": {
            "failure_mode": scenario.get("failure_mode") or geo.get("mode") or "",
            "incident": scenario.get("incident_id") or wah.get("incident_id"),
            "candidate_scenario": scenario.get("scenario_id"),
            "sealed_pattern": scenario.get("sealed_pattern"),
            "execution_evidence": True,
        },
        "candidate_split": {
            "user_trajectory": scenario.get("user_trajectory") or "",
            "scenario_geometry": geo,
            "failure_mode_mapping": scenario.get("failure_mode") or geo.get("mode") or "",
            "mode_detection": detect,
        },
        "scenario_purpose": scenario.get("scenario_purpose") or "",
        "expected_invariant": exp,
        "what_actually_happened": wah,
        "run": {
            "passed": run_result.get("passed"),
            "failures": run_result.get("failures") or [],
            "script_id": run_result.get("script_id"),
            "llm_mode": run_result.get("llm_mode"),
            "adapter": adapter_name,
            "planted_steal": steal,
            "turns": run_result.get("turns") or run_result.get("turn_results") or [],
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "File-based evidence under candidates/.../evidence/. "
            "Includes what_actually_happened turn table (incident report form). "
            "GeometryHoldAdapter is a console stub — replace with host Driver for "
            "path-faithful product runs."
        ),
    }


def run_candidate(
    scenario_id: str,
    *,
    candidates_dir: str | Path | None = None,
    steal: bool = False,
    write: bool = True,
) -> dict[str, Any]:
    """Compile candidate → run_script → taxonomy-shaped evidence (optional disk write)."""
    from conjecture_behaviour_runner.harness import run_script
    from conjecture_behaviour_runner.runner_log import error_contract, info

    info(
        "run_candidate.start",
        msg="geometry hold run",
        scenario_id=scenario_id,
        steal=steal,
        write=write,
        adapter="GeometryHoldAdapter",
    )
    payload = get_candidate(scenario_id, candidates_dir=candidates_dir)
    if not payload.get("ok"):
        return error_contract(
            code=str(payload.get("error") or "candidate_not_found"),
            message=str(payload.get("error") or "candidate not found"),
            stage="load_candidate",
            scenario_id=scenario_id,
            adapter="GeometryHoldAdapter",
            details=dict(payload) if isinstance(payload, dict) else None,
        )

    scenario = payload.get("scenario") or {}
    script_view = payload.get("script_view") or {}
    cdir = resolve_candidates_dir(candidates_dir)
    if cdir is None:
        return error_contract(
            code="no_candidates_dir",
            message="CONJECTURE_CANDIDATES_DIR not set / no candidates directory",
            stage="resolve_candidates_dir",
            scenario_id=scenario_id,
            adapter="GeometryHoldAdapter",
        )

    # Prefer compiled ConjectureScript object path via compile again
    script = None
    try:
        from conjecture_behaviour_runner.compile_scenario import (
            compile_scenario_to_script,
        )
        from conjecture_behaviour_runner.experimental.scenario_models import Scenario

        sc_obj = Scenario.model_validate(scenario)
        script = compile_scenario_to_script(
            sc_obj,
            profile_id="ci_stub_cognition",
            conversation_id=f"conv_{scenario_id}",
        )
    except Exception as exc:  # noqa: BLE001
        # Build minimal script from trajectory steps
        from conjecture_behaviour_runner.pins import CognitionPin
        from conjecture_behaviour_runner.script import ConjectureScript, DialogueTurn

        turns = []
        for st in (payload.get("trajectory") or {}).get("steps") or []:
            if st.get("setup_only") or st.get("role") == "setup":
                # skip pure setup text noise — still one seed turn if empty
                pin_raw = st.get("pin") or {}
                turns.append(
                    DialogueTurn(
                        user_text=st.get("user_text") or "setup",
                        pin=CognitionPin.from_dict(pin_raw) if pin_raw else CognitionPin(
                            task_intent="continue", reason="setup",
                        ),
                        invariants=[
                            InvariantSpec(kind=i.get("kind", "always_true"), expected=i.get("expected"))
                            for i in (st.get("invariants") or [])
                            if isinstance(i, dict)
                        ] or [InvariantSpec(kind="always_true")],
                    )
                )
                continue
            pin_raw = st.get("pin") or {}
            turns.append(
                DialogueTurn(
                    user_text=st.get("user_text") or st.get("user_behavior") or "continue",
                    pin=CognitionPin.from_dict(pin_raw) if pin_raw else CognitionPin(
                        task_intent="continue", reason="candidate",
                    ),
                    invariants=[
                        InvariantSpec(
                            kind=str(i.get("kind") or "always_true"),
                            expected=i.get("expected"),
                        )
                        for i in (st.get("invariants") or [])
                        if isinstance(i, dict)
                    ] or [
                        InvariantSpec(
                            kind="exclusive_owner",
                            expected=(scenario.get("geometry") or {}).get("surface") or "default",
                        )
                    ],
                )
            )
        if not turns:
            from conjecture_behaviour_runner.runner_log import error_contract

            return error_contract(
                code="compile_failed",
                message=f"compile_failed: {exc}",
                stage="compile_scenario",
                scenario_id=scenario_id,
                adapter="GeometryHoldAdapter",
                exc=exc if isinstance(exc, BaseException) else None,
            )
        script = ConjectureScript(
            script_id=scenario_id,
            description=scenario.get("scenario_purpose") or scenario_id,
            conversation_id=f"conv_{scenario_id}",
            turns=turns,
            tags=("candidate", "console"),
        )

    try:
        adapter = GeometryHoldAdapter(steal=steal)
        result = run_script(script, adapter=adapter, llm_mode=LlmMode.STUB)
        run_dict = result.to_dict() if hasattr(result, "to_dict") else {
            "passed": getattr(result, "passed", False),
            "failures": list(getattr(result, "failures", []) or []),
            "script_id": getattr(result, "script_id", scenario_id),
            "llm_mode": "stub",
            "turns": [],
        }

        evidence = build_taxonomy_evidence(
            scenario=scenario if isinstance(scenario, dict) else {},
            run_result=run_dict,
            adapter_name="GeometryHoldAdapter",
            steal=steal,
        )
        evidence["ok"] = True
        evidence["scenario_id"] = scenario_id
        evidence["compile_ok"] = script_view.get("ok") if isinstance(script_view, dict) else None
        # Findings author (LLM proposes · code validates) — tables + what went wrong
        try:
            from conjecture_behaviour_runner.findings_author import (
                attach_findings_to_evidence,
            )

            attach_findings_to_evidence(
                evidence,
                scenario=scenario if isinstance(scenario, dict) else {},
            )
        except Exception as fin_exc:  # noqa: BLE001
            from conjecture_behaviour_runner.runner_log import warning

            warning(
                "findings_attach_failed",
                msg=str(fin_exc)[:400],
                scenario_id=scenario_id,
            )
            evidence["findings_error"] = f"{type(fin_exc).__name__}: {fin_exc}"

        evidence_path = None
        if write:
            ed = _evidence_dir(cdir)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            tag = "steal" if steal else "healthy"
            evidence_path = ed / scenario_id / f"{ts}_{tag}.json"
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
            # latest pointer
            latest = ed / scenario_id / "latest.json"
            latest.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
            evidence["evidence_path"] = str(evidence_path)
            evidence["latest_path"] = str(latest)

        from conjecture_behaviour_runner.runner_log import info

        info(
            "run_candidate.done",
            msg="geometry hold finished",
            scenario_id=scenario_id,
            passed=bool((evidence.get("run") or {}).get("passed")),
            steal=steal,
            evidence_path=evidence.get("evidence_path"),
        )
        return evidence
    except Exception as exc:  # noqa: BLE001
        from conjecture_behaviour_runner.runner_log import error_contract

        return error_contract(
            code="run_candidate_failed",
            message=str(exc)[:800],
            stage="run_script",
            scenario_id=scenario_id,
            adapter="GeometryHoldAdapter",
            exc=exc,
        )


def list_evidence(
    scenario_id: str,
    *,
    candidates_dir: str | Path | None = None,
) -> dict[str, Any]:
    cdir = resolve_candidates_dir(candidates_dir)
    if cdir is None:
        return {"ok": False, "error": "no_candidates_dir", "runs": []}
    ed = cdir / "evidence" / scenario_id
    if not ed.is_dir():
        return {"ok": True, "scenario_id": scenario_id, "runs": [], "dir": str(ed)}
    runs = []
    for p in sorted(ed.glob("*.json"), reverse=True):
        if p.name == "latest.json":
            continue
        try:
            runs.append({"file": p.name, "path": str(p), **json.loads(p.read_text())})
        except Exception:  # noqa: BLE001
            runs.append({"file": p.name, "path": str(p), "error": "unreadable"})
    return {"ok": True, "scenario_id": scenario_id, "runs": runs[:50], "dir": str(ed)}


def resolve_host_runner() -> tuple[Any | None, dict[str, Any]]:
    """Resolve optional path-faithful host runner (product HTTP Driver).

    Discovery order:
      1. ``CONJECTURE_HOST_RUNNER`` = ``module.path:callable`` (returns evidence dict)
      2. Soft import ``regression_suite.conjecture_bot0_http_driver:run_candidate_host_http``
         (Bot0 monorepo convenience)

    Returns ``(callable | None, status_payload)``.
    """
    import importlib
    import os

    from conjecture_behaviour_runner.host_env import (
        host_base_url,
        host_email,
        host_password_set,
    )

    meta: dict[str, Any] = {
        "available": False,
        "source": None,
        "callable": None,
        # Never fabricate demo emails / product URLs in the portable package.
        "account": host_email() or None,
        "base_url": host_base_url() or None,
        "password_set": host_password_set(),
        "hint": (
            "Host E2E needs CONJECTURE_HOST_RUNNER=module:fn (or a host monorepo "
            "adapter), plus CONJECTURE_HOST_EMAIL / CONJECTURE_HOST_PASSWORD / "
            "CONJECTURE_HOST_BASE_URL (BOT0_* aliases accepted; no package defaults)."
        ),
    }
    specs: list[str] = []
    env = (os.environ.get("CONJECTURE_HOST_RUNNER") or "").strip()
    if env:
        specs.append(env)
    specs.append(
        "regression_suite.conjecture_bot0_http_driver:run_candidate_host_http"
    )
    seen: set[str] = set()
    for spec in specs:
        if spec in seen:
            continue
        seen.add(spec)
        if ":" not in spec:
            meta["error"] = f"invalid CONJECTURE_HOST_RUNNER (need module:attr): {spec}"
            continue
        mod_name, _, attr = spec.partition(":")
        try:
            mod = importlib.import_module(mod_name)
            fn = getattr(mod, attr, None)
            if callable(fn):
                meta["available"] = True
                meta["source"] = spec
                meta["callable"] = attr
                meta["error"] = None
                meta["hint"] = (
                    "Host Driver ready. Runs product APIs only (no harness SQL). "
                    f"Default account {meta['account']}."
                )
                return fn, meta
            meta["error"] = f"{spec} is not callable"
        except Exception as exc:  # noqa: BLE001
            meta["last_import_error"] = f"{type(exc).__name__}: {exc}"
            continue
    return None, meta


def host_runner_status() -> dict[str, Any]:
    """JSON-safe status for GET /api/host-runner (no callable)."""
    _, meta = resolve_host_runner()
    return {
        "ok": True,
        "available": bool(meta.get("available")),
        "source": meta.get("source"),
        "account": meta.get("account"),
        "base_url": meta.get("base_url"),
        "password_set": bool(meta.get("password_set")),
        "hint": meta.get("hint"),
        "error": meta.get("error") or meta.get("last_import_error"),
    }


def _result_row(scenario_id: str, evidence: Mapping[str, Any]) -> dict[str, Any]:
    """One batch result: scenario identity + verdict + expandable findings payload."""
    run = evidence.get("run") if isinstance(evidence.get("run"), Mapping) else {}
    run = dict(run or {})
    err = evidence.get("error")
    ok = evidence.get("ok") is not False and err is None
    passed = bool(run.get("passed")) if ok and "passed" in run else False
    if ok and evidence.get("product_path") and "passed" not in run:
        passed = bool(evidence.get("passed", False))
    tax = evidence.get("taxonomy") if isinstance(evidence.get("taxonomy"), Mapping) else {}
    tax = dict(tax or {})
    split = (
        evidence.get("candidate_split")
        if isinstance(evidence.get("candidate_split"), Mapping)
        else {}
    )
    split = dict(split or {})
    wah = (
        evidence.get("what_actually_happened")
        if isinstance(evidence.get("what_actually_happened"), Mapping)
        else {}
    )
    wah = dict(wah or {})
    findings = evidence.get("findings") if isinstance(evidence.get("findings"), Mapping) else {}
    findings = dict(findings or {})
    # Prefer findings turns when richer; keep evidence tables either way
    return {
        "scenario_id": scenario_id,
        "ok": ok,
        "passed": passed if ok else False,
        "error": err,
        "failures": list(run.get("failures") or evidence.get("failures") or []),
        "thread_id": run.get("thread_id") or evidence.get("thread_id"),
        "evidence_path": evidence.get("evidence_path"),
        "account": evidence.get("account") or run.get("email"),
        "adapter": run.get("adapter") or evidence.get("adapter"),
        "product_path": bool(evidence.get("product_path")),
        # Expandable report fields (console Run tests)
        "failure_mode": (
            tax.get("failure_mode")
            or split.get("failure_mode_mapping")
            or wah.get("failure_mode")
            or findings.get("failure_mode_slug")
            or ""
        ),
        "incident_id": tax.get("incident") or wah.get("incident_id") or "",
        "scenario_purpose": evidence.get("scenario_purpose") or "",
        "user_trajectory": split.get("user_trajectory") or "",
        "what_actually_happened": wah,
        "findings": findings,
        "verdict_label": (
            findings.get("verdict")
            or ("PASS" if (ok and passed) else ("ERROR" if not ok else "FAIL"))
        ),
        "headline": findings.get("headline") or "",
    }


def run_candidate_batch(
    *,
    selection: str = "ids",
    ids: list[str] | None = None,
    adapter: str = "geometry",
    steal: bool = False,
    candidates_dir: str | Path | None = None,
    write: bool = True,
    filters: Mapping[str, Any] | None = None,
    max_scenarios: int = 50,
) -> dict[str, Any]:
    """Run many candidates; return a report card for the console.

    ``selection``:
      - ``ids`` — use explicit ``ids`` list
      - ``all`` — all candidates matching optional ``filters`` (same as list API)

    ``adapter``:
      - ``geometry`` — GeometryHoldAdapter (stub; no product Act)
      - ``host`` — path-faithful host runner (Bot0 HTTP when available)
    """
    from conjecture_behaviour_runner.candidates_ui import list_candidates

    started = datetime.now(timezone.utc).isoformat()
    adapter_key = (adapter or "geometry").strip().lower()
    if adapter_key in ("host_http", "bot0", "product", "e2e"):
        adapter_key = "host"
    if adapter_key not in ("geometry", "host"):
        return {
            "ok": False,
            "error": f"unknown_adapter:{adapter_key}",
            "summary": {"total": 0, "passed": 0, "failed": 0, "errors": 0},
            "results": [],
        }

    host_fn = None
    host_meta: dict[str, Any] = {}
    if adapter_key == "host":
        host_fn, host_meta = resolve_host_runner()
        if host_fn is None:
            return {
                "ok": False,
                "error": "host_runner_unavailable",
                "host": host_runner_status(),
                "summary": {"total": 0, "passed": 0, "failed": 0, "errors": 0},
                "results": [],
                "started_at": started,
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }
        if not host_meta.get("password_set") and "conjecture_bot0" in str(
            host_meta.get("source") or ""
        ):
            # Soft warn — runner may still raise; surface in report
            pass

    sel = (selection or "ids").strip().lower()
    scenario_ids: list[str] = []
    if sel == "all":
        filt = dict(filters or {})
        listing = list_candidates(
            candidates_dir=candidates_dir,
            seal=filt.get("seal") or None,
            priority=filt.get("priority") or None,
            source=filt.get("source") or None,
            q=filt.get("q") or None,
            limit=int(filt.get("limit") or max_scenarios or 50),
        )
        scenario_ids = [
            str(r.get("scenario_id"))
            for r in (listing.get("scenarios") or [])
            if r.get("scenario_id")
        ]
    else:
        scenario_ids = [str(x).strip() for x in (ids or []) if str(x).strip()]

    # de-dupe preserve order
    seen: set[str] = set()
    ordered: list[str] = []
    for sid in scenario_ids:
        if sid not in seen:
            seen.add(sid)
            ordered.append(sid)
    ordered = ordered[: max(1, min(int(max_scenarios or 50), 200))]

    from conjecture_behaviour_runner.runner_log import error_contract, info, warning

    info(
        "run_batch.start",
        msg=f"adapter={adapter_key} n={len(ordered)}",
        adapter=adapter_key,
        selection=sel,
        count=len(ordered),
    )
    results: list[dict[str, Any]] = []
    for sid in ordered:
        try:
            info(
                "run_batch.scenario",
                msg="start",
                scenario_id=sid,
                adapter=adapter_key,
            )
            if adapter_key == "host":
                assert host_fn is not None
                evidence = host_fn(sid, candidates_dir=candidates_dir, write=write)
            else:
                evidence = run_candidate(
                    sid,
                    candidates_dir=candidates_dir,
                    steal=steal,
                    write=write,
                )
            if not isinstance(evidence, Mapping):
                evidence = error_contract(
                    code="runner_returned_non_dict",
                    message="runner returned non-dict evidence",
                    stage="run_batch",
                    scenario_id=sid,
                    adapter=adapter_key,
                )
            row = _result_row(sid, evidence)
            results.append(row)
            info(
                "run_batch.scenario_done",
                msg="ok" if row.get("ok") is not False else "error",
                scenario_id=sid,
                passed=row.get("passed"),
                ok=row.get("ok"),
                error=row.get("error"),
                thread_id=row.get("thread_id"),
            )
        except Exception as exc:  # noqa: BLE001
            warning(
                "run_batch.scenario_exc",
                msg=str(exc)[:400],
                scenario_id=sid,
                adapter=adapter_key,
            )
            err_payload = error_contract(
                code="run_batch_scenario_failed",
                message=f"{type(exc).__name__}: {exc}",
                stage="run_batch",
                scenario_id=sid,
                adapter="HostAdapter" if adapter_key == "host" else "GeometryHoldAdapter",
                exc=exc,
            )
            results.append(
                {
                    "scenario_id": sid,
                    "ok": False,
                    "passed": False,
                    "error": err_payload.get("message"),
                    "error_code": err_payload.get("error_code"),
                    "stage": "run_batch",
                    "traceback": err_payload.get("traceback"),
                    "failures": [],
                    "thread_id": None,
                    "evidence_path": None,
                    "account": host_meta.get("account") if adapter_key == "host" else None,
                    "adapter": "HostAdapter" if adapter_key == "host" else "GeometryHoldAdapter",
                    "product_path": adapter_key == "host",
                    "failure_mode": "",
                    "incident_id": "",
                    "scenario_purpose": "",
                    "user_trajectory": "",
                    "what_actually_happened": {},
                    "findings": {
                        "verdict": "ERROR",
                        "headline": f"Run error: {type(exc).__name__}",
                        "what_went_wrong": str(exc)[:2000],
                        "source": "runtime",
                    },
                    "verdict_label": "ERROR",
                    "headline": f"Run error: {type(exc).__name__}",
                }
            )

    n_pass = sum(1 for r in results if r.get("passed"))
    n_err = sum(1 for r in results if not r.get("ok"))
    n_fail = sum(1 for r in results if r.get("ok") and not r.get("passed"))
    finished = datetime.now(timezone.utc).isoformat()
    return {
        "ok": True,
        "adapter": adapter_key,
        "selection": sel,
        "steal": bool(steal) if adapter_key == "geometry" else False,
        "host": host_runner_status() if adapter_key == "host" else None,
        "account": (host_meta.get("account") if adapter_key == "host" else None),
        "started_at": started,
        "finished_at": finished,
        "summary": {
            "total": len(results),
            "passed": n_pass,
            "failed": n_fail,
            "errors": n_err,
        },
        "results": results,
        "note": (
            "Host runs use product chat APIs (new conversation threads under the "
            "configured account). Geometry runs use GeometryHoldAdapter only."
            if adapter_key == "host"
            else "Geometry hold is a console stub — not live product Act."
        ),
    }


__all__ = [
    "GeometryHoldAdapter",
    "build_taxonomy_evidence",
    "build_what_actually_happened",
    "host_runner_status",
    "list_evidence",
    "resolve_host_runner",
    "run_candidate",
    "run_candidate_batch",
]
