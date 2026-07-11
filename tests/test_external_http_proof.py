"""True external portability: SUT has zero Conjecture imports."""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "proofs" / "external_http_app" / "app.py"
PROOF = ROOT / "proofs" / "run_external_http_proof.py"


def test_external_app_has_no_conjecture_imports() -> None:
    tree = ast.parse(APP.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "conjecture" not in alias.name, alias.name
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "conjecture" not in node.module, node.module


def test_external_http_proof_prove_bugs() -> None:
    import os

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    proc = subprocess.run(
        [sys.executable, str(PROOF), "--prove-bugs"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=90,
        env=env,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "External portability OK" in proc.stdout
    assert "pinned cognition" in proc.stdout
