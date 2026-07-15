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
    return {
        "taxonomy": {
            "failure_mode": scenario.get("failure_mode") or geo.get("mode") or "",
            "incident": None,
            "candidate_scenario": scenario.get("scenario_id"),
            "sealed_pattern": None,
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

    payload = get_candidate(scenario_id, candidates_dir=candidates_dir)
    if not payload.get("ok"):
        return payload

    scenario = payload.get("scenario") or {}
    script_view = payload.get("script_view") or {}
    cdir = resolve_candidates_dir(candidates_dir)
    if cdir is None:
        return {"ok": False, "error": "no_candidates_dir"}

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
            return {
                "ok": False,
                "error": f"compile_failed: {exc}",
                "scenario_id": scenario_id,
            }
        script = ConjectureScript(
            script_id=scenario_id,
            description=scenario.get("scenario_purpose") or scenario_id,
            conversation_id=f"conv_{scenario_id}",
            turns=turns,
            tags=("candidate", "console"),
        )

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

    return evidence


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


__all__ = [
    "GeometryHoldAdapter",
    "build_taxonomy_evidence",
    "list_evidence",
    "run_candidate",
]
