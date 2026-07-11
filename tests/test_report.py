"""JSON / JUnit report writers."""
from __future__ import annotations

from pathlib import Path

from conjecture_behaviour_runner import (
    ConjectureScript,
    DialogueTurn,
    InvariantSpec,
    LlmMode,
    NullControlPlaneAdapter,
    run_script,
)
from conjecture_behaviour_runner.report import (
    results_to_json_report,
    results_to_junit_xml,
    write_json_report,
    write_junit_report,
)


def _smoke_result():
    script = ConjectureScript(
        script_id="rep",
        description="r",
        conversation_id="c",
        turns=[
            DialogueTurn(
                user_text="x",
                invariants=[InvariantSpec(kind="always_true")],
            )
        ],
    )
    return run_script(
        script, adapter=NullControlPlaneAdapter(), llm_mode=LlmMode.STUB
    )


def test_json_report_shape(tmp_path: Path) -> None:
    r = _smoke_result()
    report = results_to_json_report([r])
    assert report["total"] == 1
    assert report["passed"] == 1
    out = tmp_path / "out.json"
    write_json_report(out, report)
    assert out.is_file()
    assert "rep" in out.read_text(encoding="utf-8")


def test_junit_report(tmp_path: Path) -> None:
    r = _smoke_result()
    xml = results_to_junit_xml([r])
    assert "testsuite" in xml
    assert "rep" in xml
    out = tmp_path / "out.xml"
    write_junit_report(out, [r])
    assert out.is_file()
