"""Local UI server — story + prove-bugs + candidate Scenarios API (stdlib HTTP)."""
from __future__ import annotations

import json
import os
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from conjecture_behaviour_runner.ui_server import _make_handler


def test_ui_story_and_prove_bugs() -> None:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _make_handler())
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/story") as resp:
            story = json.load(resp)
        assert "plot" in story
        assert len(story.get("turns") or []) >= 1

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/prove-bugs", method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            report = json.load(resp)
        assert report.get("helpful") is True
        assert report.get("clean_passes") is True
    finally:
        httpd.shutdown()


def test_ui_candidates_api(tmp_path: Path, monkeypatch) -> None:
    """Candidate Scenario list/detail when CONJECTURE_CANDIDATES_DIR is set."""
    # Minimal manifest + one Scenario YAML
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "role": "Scenario precursor to Script",
                "scenarios": [
                    {
                        "scenario_id": "demo_candidate",
                        "path_id": "scx.demo",
                        "seal_status": "open",
                        "priority": "high",
                        "source": "residual_heuristic",
                        "file": "demo_candidate.yaml",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "demo_candidate.yaml").write_text(
        "scenario_id: demo_candidate\n"
        "scenario_class: candidate_soak_precursor\n"
        "goal_state: [owner_holds]\n"
        "execution_profiles:\n"
        "  - id: ci\n"
        "    device: desktop\n"
        "    network: low_latency\n"
        "steps:\n"
        "  - id: t0\n"
        "    actor: user\n"
        "    control_point: chat_input\n"
        "    maneuver: continue_mid_flight\n"
        "    payload:\n"
        "      user_text: continue\n"
        "      pin: {task_intent: continue}\n"
        "    wait:\n"
        "      type: stream_wait\n"
        "      settle_condition: agent_turn_complete\n"
        "      timeout_ms: 1000\n"
        "terminal_states:\n"
        "  expected: [continue_owned]\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CONJECTURE_CANDIDATES_DIR", str(tmp_path))

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _make_handler())
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/candidates?seal=open"
        ) as resp:
            listing = json.load(resp)
        assert listing.get("ok") is True
        assert listing.get("count") == 1
        assert listing["scenarios"][0]["scenario_id"] == "demo_candidate"

        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/candidates/demo_candidate"
        ) as resp:
            detail = json.load(resp)
        assert detail.get("ok") is True
        assert "user_text" in (detail.get("yaml") or "")
        assert detail.get("scenario", {}).get("scenario_id") == "demo_candidate"
    finally:
        httpd.shutdown()
        monkeypatch.delenv("CONJECTURE_CANDIDATES_DIR", raising=False)
