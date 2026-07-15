"""Emit CandidatePath as Conjecture Scenario YAML (precursor to Script).

Human-first order (author + console):

  user trajectory → initial state → expected invariant → twists
  (setup vs user behavior) → failure oracle → geometry encoding

Internal fields (exclusive_surface, typed_act, stealer, pins) encode the trajectory
*after* the behavior is clear — not as the primary story.
"""
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
# Conjecture Scenario (CANDIDATE — portable candidate_author)
#
# Human-first: user trajectory → state → twist → must-hold → failure oracle
# Geometry (surface / act / stealer) encodes the path after the behavior is clear.
# Scenario = description language · Script = play-back form (compile when freezes ready)
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
    return str(
        st.get("active_task.kind")
        or st.get("kind")
        or st.get("exclusive_surface")
        or st.get("exclusive_owner")
        or ""
    ).strip()


def _is_setup_turn(turn: str) -> bool:
    t = (turn or "").strip().lower()
    return t.startswith("(setup)") or t.startswith("setup:")


def _user_text(turn: str) -> str:
    t = (turn or "").strip()
    for prefix in (
        "(setup) ",
        "(probe) ",
        "(setup)",
        "(probe)",
        "setup: ",
        "Setup: ",
    ):
        if t.lower().startswith(prefix.lower()):
            return t[len(prefix) :].strip()
    return t or "continue"


def _geometry_from_path(path: CandidatePath) -> dict[str, str]:
    st = dict(path.start_state or {})
    pin = dict(path.pin_hints or {})
    # invent.exclusive.{surface}.{act}.{stealer}
    parts = [p for p in (path.path_id or "").split(".") if p]
    surface = str(st.get("exclusive_surface") or "")
    act = str(st.get("typed_act") or "")
    stealer = str(st.get("competing_leaf") or st.get("stealer") or pin.get("read_kind") or "")
    if len(parts) >= 5 and parts[0] == "invent" and parts[1] == "exclusive":
        surface = surface or parts[2]
        act = act or parts[3]
        stealer = stealer or parts[4]
    return {
        "surface": surface,
        "act": act,
        "stealer": stealer,
        "mode": (path.failure_class or "").strip(),
        "source": path.source,
    }


def _user_trajectory_prose(path: CandidatePath, geo: dict[str, str]) -> str:
    """End-user story first; mechanics stay secondary."""
    surface = geo.get("surface") or "an exclusive finite-choice surface"
    stealer = geo.get("stealer") or "a competing leaf"
    act = geo.get("act") or "free text"
    if path.source == "invention" and surface and stealer:
        return (
            f"The user is midway through a bounded interaction owned by `{surface}`. "
            f"Instead of completing that interaction in the normal control, they send "
            f"free-chat text that could also be interpreted as a `{stealer}` action "
            f"(typed act: `{act}`). "
            f"The system must keep `{surface}` authoritative — bind the reply to the "
            f"active surface or re-prompt — and must not silently transfer ownership "
            f"to `{stealer}`."
        )
    title = (path.title or "").strip()
    if title:
        return (
            f"Trajectory under test: {title}. "
            f"User path must preserve the exclusive owner and active record "
            f"required by failure mode `{path.failure_class}`."
        )
    return (
        f"Multi-turn trajectory that stresses failure mode `{path.failure_class}`. "
        "Preserve exclusive owner and active record; refuse silent handoff to a stealer."
    )


def _scenario_purpose(path: CandidatePath, geo: dict[str, str]) -> str:
    surface = geo.get("surface") or "exclusive surface"
    stealer = geo.get("stealer") or "competing action"
    mode = path.failure_class or "authority_failure"
    if path.source == "invention":
        return (
            f"Verify free-text that resembles a competing action does not take ownership "
            f"away from active exclusive surface `{surface}` (mode `{mode}`, stealer "
            f"`{stealer}`)."
        )
    return (
        f"Stress failure mode `{mode}`: system must hold exclusive owner / pin through "
        f"the authored trajectory (source={path.source})."
    )


def _failure_oracle(path: CandidatePath, geo: dict[str, str]) -> list[str]:
    stealer = geo.get("stealer") or "competing_leaf"
    surface = geo.get("surface") or "exclusive_surface"
    mode = path.failure_class or "owner_steal"
    base = [
        f"`{stealer}` becomes the authoritative owner",
        f"active exclusive surface `{surface}` is dropped or silently disarmed",
        "user message is processed as a new greenfield / foreign request",
        "reply appears valid but no longer advances or protects the active interaction",
    ]
    for m in path.must_not:
        if m and m not in base:
            base.append(str(m))
    return [
        f"Failure mode `{mode}` is instantiated if any of the following occurs:",
        *base,
    ]


def candidate_to_scenario_dict(
    path: CandidatePath,
    *,
    exclusive_owner: str | None = None,
) -> dict[str, Any]:
    kind = _kind_from_start(path)
    geo = _geometry_from_path(path)
    owner = (
        exclusive_owner
        or geo.get("surface")
        or kind
        or "default"
    )
    pin = dict(path.pin_hints or {})
    if "task_intent" not in pin:
        pin["task_intent"] = "continue"
    # Encode geometry into pin for drivers without polluting user_text
    for k, v in (
        ("exclusive_surface", geo.get("surface")),
        ("typed_act", geo.get("act")),
        ("stealer", geo.get("stealer")),
    ):
        if v and k not in pin:
            pin[k] = v

    turns = list(path.turns) if path.turns else ("continue",)
    if len(turns) == 1:
        turns = (
            f"(setup) Establish exclusive ownership for {owner}",
            turns[0],
        )

    invs: list[dict[str, Any]] = []
    if owner and owner != "default":
        invs.append({"kind": "exclusive_owner", "expected": owner})
    if kind and kind not in ("none", "any", owner):
        invs.append({"kind": "active_kind", "expected": kind})

    steps: list[dict[str, Any]] = []
    for i, turn in enumerate(turns):
        setup = i == 0 or _is_setup_turn(turn)
        step_id = "establish_active_interaction" if setup else f"user_twist_{i}"
        if setup:
            maneuver = "test_setup_precondition"
            role = "setup"
            user_behavior = (
                "Test harness establishes the active exclusive interaction "
                "(not end-user chat)."
            )
            competing = ""
        else:
            maneuver = "user_free_chat_under_exclusive_surface"
            role = "user_twist"
            user_behavior = _user_text(turn)
            competing = (
                f"Text may also resemble input that `{geo.get('stealer') or 'stealer'}` "
                "could treat as a new request."
                if geo.get("stealer")
                else ""
            )
        payload: dict[str, Any] = {
            "user_text": _user_text(turn) if not setup else f"[setup] arm {owner}",
            "pin": dict(pin),
            "allowed_outcomes": ["continue_owned", "owner_held", "reprompt_exclusive"],
            "invariants": list(invs),
        }
        if setup:
            payload["setup_only"] = True
        steps.append({
            "id": step_id,
            "actor": "system" if setup else "user",
            "role": role,
            "control_point": "test_harness" if setup else "chat_input",
            "maneuver": maneuver,
            "entry_surface": "/assistant",
            "user_behavior": user_behavior,
            "competing_interpretation": competing,
            "payload": payload,
            "preconditions": (
                [f"{k}={v}" for k, v in (path.start_state or {}).items()]
                if setup
                else [f"exclusive_owner={owner}", "armed=true"]
            ),
            "blocked_conditions": list(path.must_not) if not setup else [],
            "postconditions": list(path.must_hold) or [f"exclusive_owner≈{owner}"],
            "wait": {
                "type": "stream_wait",
                "settle_condition": "agent_turn_complete",
                "timeout_ms": 15000,
                "poll_interval_ms": 500,
            },
            "nondeterminism": {
                "type": "agentic",
                "allowed_outcomes": ["continue_owned", "owner_held", "reprompt_exclusive"],
                "required_invariants": list(path.must_hold) or [f"exclusive_owner≈{owner}"],
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

    goal = list(path.must_hold) if path.must_hold else [f"exclusive_owner≈{owner}"]
    initial_human = [
        f"An exclusive finite-choice surface is open (`{geo.get('surface') or owner}`).",
        f"`{owner}` owns the interaction and is waiting for a selection / reply.",
        "Free-text chat remains available.",
    ]
    if geo.get("stealer"):
        initial_human.append(
            f"`{geo['stealer']}` is capable of interpreting the same text as a new request."
        )

    return {
        "scenario_id": scenario_id_for(path),
        "scenario_class": "candidate_soak_precursor",
        # --- Human-first narrative (console + review) ---
        "failure_mode": path.failure_class,
        "scenario_purpose": _scenario_purpose(path, geo),
        "user_trajectory": _user_trajectory_prose(path, geo),
        "expected_invariant": {
            "prose": (
                f"While the exclusive surface remains armed, exclusive_owner ≈ {owner}. "
                "Reply must bind to the active interaction or re-prompt; must not activate "
                f"the competing leaf `{geo.get('stealer') or '—'}`."
            ),
            "checks": invs,
            "must_hold": list(path.must_hold) or [f"exclusive_owner≈{owner}"],
            "must_not": list(path.must_not),
        },
        "failure_oracle": _failure_oracle(path, geo),
        "geometry": geo,
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
        "initial_state": {
            "human": initial_human,
            "machine": [
                f"{k}={v}" for k, v in (path.start_state or {}).items()
            ] or [f"exclusive_owner={owner}"],
        },
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
                    "state": path.failure_class or "owner_steal",
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
        f"# failure_mode: {path.failure_class}\n"
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
        "Human-first trajectories → geometry encoding. Promote red soaks to goldens.",
        "",
        "| scenario_id | mode | seal | priority | path_id |",
        "|---|---|---|---|---|",
    ]
    from datetime import datetime, timezone

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
            "failure_class": path.failure_class,
            "title": path.title,
            "ok": True,
        })
        index.append(
            f"| `{sid}` | `{path.failure_class}` | {path.seal_status} | "
            f"{path.priority} | `{path.path_id}` |"
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
                "failure_class": r.get("failure_class") or "",
                "file": f"{r['scenario_id']}.yaml",
            }
            for r in report
        ],
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
    )
    by_src: dict[str, int] = {}
    invent_rows = []
    for r in report:
        src = str(r.get("source") or "")
        by_src[src] = by_src.get(src, 0) + 1
        if src == "invention":
            invent_rows.append({
                "scenario_id": r["scenario_id"],
                "path_id": r["path_id"],
                "failure_class": r.get("failure_class") or "",
                "title": r.get("title") or "",
                "seal_status": r.get("seal_status"),
                "file": f"{r['scenario_id']}.yaml",
            })
    run_doc = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "conjecture_behaviour_runner.candidate_author",
        "total": len(report),
        "by_source": by_src,
        "invention_count": len(invent_rows),
        "invention_scenarios": invent_rows,
        "note": (
            "Invention = geometry invent (not sole×foreign expansion). "
            "Each row is a candidate scenario/trajectory; failure_class is the taxonomy id."
        ),
    }
    (out_dir / "last_author_run.json").write_text(
        json.dumps(run_doc, indent=2) + "\n", encoding="utf-8",
    )
    if invent_rows:
        (out_dir / "invent_run.json").write_text(
            json.dumps(
                {
                    **run_doc,
                    "kind": "invention_only",
                    "scenarios": invent_rows,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return report


__all__ = [
    "candidate_to_scenario_dict",
    "scenario_id_for",
    "scenario_to_yaml",
    "write_candidate_scenarios",
]
