"""Run portable parameterized templates with TemplateStreamAdapter.

No product host required — proves template shape + standard invariants.

::

    python examples/parameterized_templates.py
"""
from __future__ import annotations

from conjecture_behaviour_runner import LlmMode, run_script
from conjecture_behaviour_runner.templates import (
    TemplateStreamAdapter,
    demo_scripts,
    reorient_keeps_owner_script,
    sole_continue_script,
)


def main() -> int:
    adapter = TemplateStreamAdapter()
    scripts = list(demo_scripts())
    # Second vocabulary — same law, different kind strings.
    scripts.append(
        sole_continue_script(
            kind="invoice_intake",
            exclusive_owner="invoice_intake",
            pin_key="invoice_id",
            pin_value="inv_99",
            script_id="template_invoice_sole_continue",
        )
    )
    scripts.append(
        reorient_keeps_owner_script(
            kind="invoice_intake",
            exclusive_owner="invoice_intake",
            pin_key="invoice_id",
            pin_value="inv_99",
            script_id="template_invoice_reorient_keeps_owner",
        )
    )

    all_passed = True
    for script in scripts:
        result = run_script(script, adapter=adapter, llm_mode=LlmMode.STUB)
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {script.script_id} — {script.description}")
        if not result.passed:
            all_passed = False
            for failure in result.failures:
                print(f"        {failure}")

    print(
        f"\n{len(scripts)} template runs, "
        f"{'all passed' if all_passed else 'FAILURES above'}"
    )
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
