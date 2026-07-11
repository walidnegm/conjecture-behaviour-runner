#!/usr/bin/env python3
"""End-to-end: HttpJsonAdapter against a real HTTP process (not in-process mini-app).

Proves Conjecture is not CCP-only: any app that POSTs back owner/pins JSON works.

Usage::

  # terminal A
  python examples/http_debug_app.py --port 8766

  # terminal B
  python examples/http_e2e.py --endpoint http://127.0.0.1:8766/chat
  python examples/http_e2e.py --endpoint http://127.0.0.1:8766/chat --prove-bugs

Or self-contained (spawns host on ephemeral port)::

  python examples/http_e2e.py --self-host --prove-bugs
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

from conjecture_behaviour_runner import LlmMode, run_script
from conjecture_behaviour_runner.contrib.http_json import HttpJsonAdapter
from conjecture_behaviour_runner.path_faithful import sole_continue_script


def _wait_health(base: str, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    url = base.rstrip("/").rsplit("/chat", 1)[0] + "/health"
    last: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as resp:
                if resp.status == 200:
                    return
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(0.05)
    raise RuntimeError(f"host not healthy at {url}: {last}")


def run_against(endpoint: str, *, bug: Optional[str] = None) -> dict:
    # bug only applies when using self-host; external host sets --bug on server
    _ = bug
    adapter = HttpJsonAdapter(
        endpoint=endpoint,
        owner_path="debug.owner",
        kind_path="debug.kind",
        pins_path="debug.pins",
        outcome_path="debug.outcome",
        extras_path="debug.extras",
    )
    result = run_script(
        sole_continue_script(),
        adapter=adapter,
        llm_mode=LlmMode.STUB,
    )
    return {
        "passed": result.passed,
        "failures": list(result.failures),
        "script_id": result.script_id,
        "endpoint": endpoint,
        "turn_results": result.turn_results,
    }


def prove_over_http(endpoint_template_port: int | None = None) -> dict:
    """Spawn three hosts with planted bugs + one clean; assert red bar over HTTP."""
    here = Path(__file__).resolve().parent
    app = here / "http_debug_app.py"
    procs: list[subprocess.Popen] = []
    results: dict[str, dict] = {}

    def spawn(port: int, bug: Optional[str]) -> str:
        cmd = [
            sys.executable,
            str(app),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ]
        if bug:
            cmd.extend(["--bug", bug])
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        procs.append(proc)
        endpoint = f"http://127.0.0.1:{port}/chat"
        _wait_health(endpoint)
        return endpoint

    try:
        # Use high ports to avoid clashing with conjecture ui (8765)
        base = 18770
        clean_ep = spawn(base, None)
        dual_ep = spawn(base + 1, "dual_owner")
        drop_ep = spawn(base + 2, "drop_pin")
        restart_ep = spawn(base + 3, "illegal_restart")

        clean = run_against(clean_ep)
        dual = run_against(dual_ep)
        drop = run_against(drop_ep)
        restart = run_against(restart_ep)

        report = {
            "clean_passes": clean["passed"],
            "dual_owner_caught": not dual["passed"],
            "drop_pin_caught": not drop["passed"],
            "illegal_restart_caught": not restart["passed"],
            "transport": "http_json",
            "details": {
                "clean": clean,
                "dual_owner": dual,
                "drop_pin": drop,
                "illegal_restart": restart,
            },
        }
        report["helpful"] = (
            report["clean_passes"]
            and report["dual_owner_caught"]
            and report["drop_pin_caught"]
            and report["illegal_restart_caught"]
        )
        return report
    finally:
        for proc in procs:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="HttpJsonAdapter e2e")
    p.add_argument(
        "--endpoint",
        default=None,
        help="Existing host POST URL (default: self-host if --self-host)",
    )
    p.add_argument(
        "--self-host",
        action="store_true",
        help="Spawn http_debug_app on ephemeral ports",
    )
    p.add_argument(
        "--prove-bugs",
        action="store_true",
        help="Clean PASS + three planted bugs FAIL over HTTP",
    )
    args = p.parse_args(argv)

    if args.prove_bugs or args.self_host or not args.endpoint:
        report = prove_over_http()
        print(json.dumps({k: v for k, v in report.items() if k != "details"}, indent=2))
        if report.get("helpful"):
            print(
                "HTTP path helpful: portable Driver works off in-process mini-app."
            )
            return 0
        print("HTTP prove-bugs unexpected", file=sys.stderr)
        return 1

    out = run_against(args.endpoint)
    print(json.dumps(out, indent=2, default=str))
    return 0 if out["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
