"""Run the control-plane golden scripts against the REAL CCP contract.

Unlike ``minimal_script.py`` (null adapter, proves nothing), this binds to the
Conversation Control Plane and verifies sole-continue ownership, detour
supersede, and pin-over-ambient identity across turns.

Requires the companion package importable::

    pip install conjecture-behaviour-runner[control-plane]

Run::

    python examples/control_plane_goldens.py
"""
from __future__ import annotations

from conjecture_behaviour_runner import LlmMode, run_script


def main() -> int:
    try:
        from conjecture_behaviour_runner.contrib.control_plane import (
            ControlPlaneStreamAdapter,
            control_plane_golden_scripts,
        )

        adapter = ControlPlaneStreamAdapter()
    except ImportError as exc:
        print(f"SKIP: {exc}")
        return 0

    scripts = control_plane_golden_scripts()
    all_passed = True
    for script in scripts:
        result = run_script(script, adapter=adapter, llm_mode=LlmMode.STUB)
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {script.script_id} — {script.description}")
        if not result.passed:
            all_passed = False
            for failure in result.failures:
                print(f"        {failure}")

    print(f"\n{len(scripts)} goldens, {'all passed' if all_passed else 'FAILURES above'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
