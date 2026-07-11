"""Script discovery."""
from __future__ import annotations

from pathlib import Path

from conjecture_behaviour_runner.discover import discover_scripts

ROOT = Path(__file__).resolve().parents[1]


def test_discover_examples_json() -> None:
    pairs = discover_scripts([str(ROOT / "examples")])
    ids = {s.script_id for _, s in pairs}
    assert "trajectory_e2e_sole_continue" in ids or "sole_continue_owns_the_turn" in ids
    assert len(pairs) >= 1


def test_discover_script_id_prefix() -> None:
    pairs = discover_scripts(
        [str(ROOT / "examples")],
        script_id_prefix="sole_continue",
    )
    for _, s in pairs:
        assert s.script_id.startswith("sole_continue") or "sole" in s.script_id
