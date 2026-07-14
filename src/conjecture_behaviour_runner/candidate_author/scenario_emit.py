"""Emit CandidatePath as Conjecture Scenario YAML (precursor to Script)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Sequence

from conjecture_behaviour_runner.candidate_author.models import CandidatePath


def _require_yaml():
    """PyYAML is optional (``[scenarios]`` extra); only needed when dumping YAML."""
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "YAML scenario emit requires PyYAML — "
            "pip install conjecture-behaviour-runner[scenarios]"
        ) from exc
    return yaml

_HEADER = """\
# Conjecture Scenario (CANDIDATE — authored by portable candidate_author)
#
# Scenario  = describe twists + envelopes (precursor)
# Script    = play-back form (compile_scenario_to_script when freezes ready)
#
# Host vocabulary only in payload.pin / invariants — not a Conjecture catalog.
#
"""


def scenario_id_for(path: CandidatePath) -> str:
    raw = (path.path_id or "candidate").strip().lower()
    raw = raw.replace(".", "_").replace("-", "_")
    raw = re.sub(r"[^a-z0-9_]+", "_", raw)
    raw = re.sub(r"_+", "_", raw).strip("_")
    return raw[:120] or "candidate"


def _kind_from_start(path: CandidatePath) -> str:
    st = path.start_state or {}
    return str(st.get("active_task.kind") or st.get("kind") or "").strip()


def _user_text(turn: str) -> str:
    t = (turn or "").strip()
    for prefix in ("(setup) ", "(probe) ", "(setup)", "(probe)"):
        if t.lower().startswith(prefix.lower()):
            return t[len(prefix) :].strip()
    return t or "continue"


def candidate_to_scenario_dict(
    path: CandidatePath,
    *,
    exclusive_owner: str | None = None,
) -> dict[str, Any]:
    kind = _kind_from_start(path)
    owner = exclusive_owner or kind or "default"
    pin = dict(path.pin_hints or {})
    if "task_intent" not in pin:
        pin["task_intent"] = "continue"

    turns = list(path.turns) if path.turns else ("continue",)
    if len(turns) == 1:
        turns = (
            f"(setup) Reach sole-continue state for kind={kind or 'unknown'}",
            turns[0],
        )

    invs: list[dict[str, Any]] = []
    if kind and kind not in ("none", "any"):
        invs.append({"kind": "active_kind", "expected": kind})
    if owner and owner != "default":
        invs.append({"kind": "exclusive_owner", "expected": owner})

    steps: list[dict[str, Any]] = []
    for i, turn in enumerate(turns):
        step_id = "establish_start" if i == 0 else f"twist_{i}"
        maneuver = "establish_start_state" if i == 0 else "continue_mid_flight"
        if i > 0 and pin.get("read_kind"):
            maneuver = "probe_foreign_surface"
        payload: dict[str, Any] = {
            "user_text": _user_text(turn),
            "pin": dict(pin),
            "allowed_outcomes": ["continue_owned", "owner_held"],
            "invariants": invs if i > 0 else (
                [{"kind": "active_kind", "expected": kind}]
                if kind and kind not in ("none", "")
                else []
            ),
        }
        steps.append({
            "id": step_id,
            "actor": "user",
            "control_point": "chat_input",
            "maneuver": maneuver,
            "entry_surface": "/assistant",
            "payload": payload,
            "preconditions": [
                f"{k}={v}" for k, v in (path.start_state or {}).items()
            ] if i == 0 else [f"active_task.kind={kind}" if kind else "mid_flight"],
            "blocked_conditions": list(path.must_not) if i > 0 else ["already_foreign_owner"],
            "postconditions": list(path.must_hold) or ["exclusive_owner_holds"],
            "wait": {
                "type": "stream_wait",
                "settle_condition": "agent_turn_complete",
                "timeout_ms": 15000,
                "poll_interval_ms": 500,
            },
            "nondeterminism": {
                "type": "agentic",
                "allowed_outcomes": ["continue_owned", "owner_held"],
                "required_invariants": list(path.must_hold) or ["exclusive_owner_holds"],
            },
            "evidence": [
                {
                    "type": "api_contract",
                    "path": path.proof_pointer or "candidate_author",
                    "assertion": path.failure_class,
                    "confidence": "medium",
                },
            ],
        })

    goal = list(path.must_hold) if path.must_hold else ["exclusive_owner_holds"]
    return {
        "scenario_id": scenario_id_for(path),
        "scenario_class": "candidate_soak_precursor",
        "scope": {
            "in_scope": [
                path.title,
                f"failure_class={path.failure_class}",
                f"source={path.source}",
                f"seal_status={path.seal_status}",
                f"priority={path.priority}",
            ],
            "out_of_scope": [
                "free live model quality scoring",
                "product routing via utterance laundry lists",
            ],
            "expected_refusal": list(path.must_not) or [
                "exclusive_owner steal mid sole-continue",
            ],
        },
        "goal_state": goal,
        "initial_state": [
            f"{k}={v}" for k, v in (path.start_state or {}).items()
        ] or ["idle_or_seeded_mid_flight"],
        "execution_profiles": [
            {
                "id": "ci_stub_cognition",
                "device": "desktop",
                "viewport": {"width": 1440, "height": 900},
                "network": "low_latency",
                "input_mode": "chat_text",
                "sla": {"action_timeout_ms": 5000, "stream_timeout_ms": 15000},
                "feature_flags": {
                    "cognition": "stub",
                    "path_id": path.path_id,
                },
            },
            {
                "id": "human_soak",
                "device": "desktop",
                "network": "low_latency",
                "input_mode": "chat_text",
                "sla": {"action_timeout_ms": 120000, "stream_timeout_ms": 120000},
                "feature_flags": {"cognition": "live", "path_id": path.path_id},
            },
        ],
        "steps": steps,
        "terminal_states": {
            "expected": ["continue_owned_with_stable_owner", "sole_continue_held"],
            "tolerated_degraded": ["continue_owned_after_single_retry"],
            "failure": [
                {
                    "state": "owner_steal",
                    "required_graceful_handling": [
                        "fail_closed_to_verifier",
                        "surface_owner_mismatch_in_report",
                    ],
                },
                {
                    "state": "foreign_greenfield_start",
                    "required_graceful_handling": [
                        "fail_closed_to_verifier",
                        "do_not_treat_pretty_reply_as_pass",
                    ],
                },
            ],
        },
    }


def scenario_to_yaml(
    path: CandidatePath,
    *,
    exclusive_owner: str | None = None,
) -> str:
    yaml = _require_yaml()
    doc = candidate_to_scenario_dict(path, exclusive_owner=exclusive_owner)
    body = yaml.safe_dump(
        doc, sort_keys=False, default_flow_style=False, allow_unicode=True, width=100,
    )
    meta = (
        f"# path_id: {path.path_id}\n"
        f"# seal_status: {path.seal_status}\n"
        f"# priority: {path.priority}\n"
        f"# proof: {path.proof_pointer or '—'}\n"
        "#\n"
    )
    return _HEADER + meta + body


def write_candidate_scenarios(
    paths: Sequence[CandidatePath],
    out_dir: Path | str,
    *,
    owner_for_kind: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    owner_for_kind = owner_for_kind or {}
    index = [
        "# Candidate Conjecture Scenarios (portable author)",
        "",
        "Precursor to Scripts. Generated — promote red soaks to goldens.",
        "",
        "| scenario_id | seal | priority | path_id |",
        "|---|---|---|---|",
    ]
    report: list[dict[str, Any]] = []
    for path in paths:
        kind = _kind_from_start(path)
        owner = owner_for_kind.get(kind) or kind or None
        sid = scenario_id_for(path)
        fpath = out_dir / f"{sid}.yaml"
        fpath.write_text(
            scenario_to_yaml(path, exclusive_owner=owner),
            encoding="utf-8",
        )
        report.append({
            "path_id": path.path_id,
            "scenario_id": sid,
            "file": str(fpath),
            "seal_status": path.seal_status,
            "priority": path.priority,
            "source": path.source,
            "ok": True,
        })
        index.append(
            f"| `{sid}` | {path.seal_status} | {path.priority} | `{path.path_id}` |"
        )
    (out_dir / "INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    manifest = {
        "generator": "conjecture_behaviour_runner.candidate_author",
        "role": "Scenario precursor to Script",
        "scenarios": [
            {
                "scenario_id": r["scenario_id"],
                "path_id": r["path_id"],
                "seal_status": r["seal_status"],
                "priority": r["priority"],
                "source": r["source"],
                "file": f"{r['scenario_id']}.yaml",
            }
            for r in report
        ],
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
    )
    return report


__all__ = [
    "candidate_to_scenario_dict",
    "scenario_id_for",
    "scenario_to_yaml",
    "write_candidate_scenarios",
]
