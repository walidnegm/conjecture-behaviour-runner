"""Portable transport proof: HttpJsonAdapter over real loopback HTTP."""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from conjecture_behaviour_runner import LlmMode, run_script
from conjecture_behaviour_runner.contrib.http_json import HttpJsonAdapter
from conjecture_behaviour_runner.path_faithful import sole_continue_script

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _spawn(port: int, bug: str | None = None) -> subprocess.Popen:
    cmd = [
        sys.executable,
        str(EXAMPLES / "http_debug_app.py"),
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    if bug:
        cmd.extend(["--bug", bug])
    return subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


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
    raise RuntimeError(f"server not up: {last}")


def test_http_json_healthy_and_planted_bugs() -> None:
    ports = (18880, 18881, 18882, 18883)
    bugs = (None, "owner_steal", "drop_pin", "illegal_restart")
    procs = []
    try:
        for port, bug in zip(ports, bugs):
            procs.append(_spawn(port, bug))
            _wait(port)

        def run(port: int):
            adapter = HttpJsonAdapter(
                endpoint=f"http://127.0.0.1:{port}/chat",
                owner_path="debug.owner",
                kind_path="debug.kind",
                pins_path="debug.pins",
                outcome_path="debug.outcome",
                extras_path="debug.extras",
            )
            return run_script(
                sole_continue_script(),
                adapter=adapter,
                llm_mode=LlmMode.STUB,
            )

        clean = run(ports[0])
        dual = run(ports[1])
        drop = run(ports[2])
        restart = run(ports[3])

        assert clean.passed, clean.failures
        assert not dual.passed
        assert not drop.passed
        assert not restart.passed
    finally:
        for p in procs:
            p.terminate()
            try:
                p.wait(timeout=2)
            except subprocess.TimeoutExpired:
                p.kill()


def test_http_e2e_script_prove() -> None:
    """examples/http_e2e.py --self-host --prove-bugs exits 0."""
    import os

    root = EXAMPLES.parent
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src") + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    proc = subprocess.run(
        [sys.executable, str(EXAMPLES / "http_e2e.py"), "--self-host", "--prove-bugs"],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=90,
        env=env,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "helpful" in proc.stdout
