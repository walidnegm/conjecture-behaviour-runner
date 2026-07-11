#!/usr/bin/env python3
"""Portability proof: external SUT ↛ Conjecture package; HTTP only.

  independent app (proofs/external_http_app/)
          ↓ HTTP
  HttpJsonAdapter
          ↓
  portable golden (sole-continue)
          ↓
  Conjecture verifier

Does **not** import MiniChatApp or anything from the SUT package graph beyond HTTP.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Optional

# Conjecture client only — never import proofs.external_http_app as a library.
from conjecture_behaviour_runner import LlmMode, run_script
from conjecture_behaviour_runner.contrib.http_json import HttpJsonAdapter
from conjecture_behaviour_runner.path_faithful import sole_continue_script

ROOT = Path(__file__).resolve().parent
APP = ROOT / "external_http_app" / "app.py"


def _wait(port: int, timeout: float = 5.0) -> None:
    url = f"http://127.0.0.1:{port}/health"
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.3) as r:
                if r.status == 200:
                    return
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(0.05)
    raise RuntimeError(f"external app not healthy: {last}")


def _spawn(port: int, bug: Optional[str]) -> subprocess.Popen:
    cmd = [sys.executable, str(APP), "--host", "127.0.0.1", "--port", str(port)]
    if bug:
        cmd.extend(["--bug", bug])
    return subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def _run(endpoint: str):
    adapter = HttpJsonAdapter(
        endpoint=endpoint,
        owner_path="debug.owner",
        kind_path="debug.kind",
        pins_path="debug.pins",
        outcome_path="debug.outcome",
        extras_path="debug.extras",
    )
    # STUB = pinned cognition on the golden (not freeze-store replay).
    return run_script(
        sole_continue_script(),
        adapter=adapter,
        llm_mode=LlmMode.STUB,
    )


def prove_bugs() -> dict:
    # Distinct ports from conjecture ui (8765) and legacy http_debug (8766)
    ports = {
        None: 18990,
        "owner_steal": 18991,
        "drop_pin": 18992,
        "illegal_restart": 18993,
    }
    procs: list[subprocess.Popen] = []
    try:
        for bug, port in ports.items():
            procs.append(_spawn(port, bug))
            _wait(port)

        clean = _run(f"http://127.0.0.1:{ports[None]}/chat")
        steal = _run(f"http://127.0.0.1:{ports['owner_steal']}/chat")
        drop = _run(f"http://127.0.0.1:{ports['drop_pin']}/chat")
        restart = _run(f"http://127.0.0.1:{ports['illegal_restart']}/chat")

        report = {
            "proof": "external_http_app",
            "sut_imports_conjecture": False,
            "transport": "http_json",
            "cognition_mode": "stub_pinned",  # not freeze-store
            "clean_passes": clean.passed,
            "owner_steal_caught": not steal.passed,
            "drop_pin_caught": not drop.passed,
            "illegal_restart_caught": not restart.passed,
            "failures_sample": {
                "owner_steal": steal.failures[:3],
                "drop_pin": drop.failures[:3],
                "illegal_restart": restart.failures[:3],
            },
        }
        report["helpful"] = (
            report["clean_passes"]
            and report["owner_steal_caught"]
            and report["drop_pin_caught"]
            and report["illegal_restart_caught"]
        )
        return report
    finally:
        for p in procs:
            p.terminate()
            try:
                p.wait(timeout=2)
            except subprocess.TimeoutExpired:
                p.kill()


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="External HTTP portability proof")
    p.add_argument("--endpoint", default=None, help="Existing SUT /chat URL")
    p.add_argument(
        "--prove-bugs",
        action="store_true",
        help="Spawn external apps (clean + bugs) and verify red bar",
    )
    args = p.parse_args(argv)

    if args.prove_bugs or not args.endpoint:
        report = prove_bugs()
        print(json.dumps(report, indent=2))
        if report["helpful"]:
            print(
                "\nExternal portability OK: SUT has no Conjecture import; "
                "contracts held under pinned cognition (STUB); "
                "owner_steal / drop_pin / illegal_restart FAIL over HTTP."
            )
            return 0
        print("External proof unexpected", file=sys.stderr)
        return 1

    result = _run(args.endpoint)
    print(
        json.dumps(
            {
                "passed": result.passed,
                "failures": result.failures,
                "cognition_mode": "stub_pinned",
            },
            indent=2,
        )
    )
    if result.passed:
        print("contracts held under pinned cognition (LlmMode.STUB)")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
