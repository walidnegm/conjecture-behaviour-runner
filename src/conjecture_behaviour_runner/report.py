"""Run reports — JSON and JUnit XML."""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Sequence

from conjecture_behaviour_runner.script import RunResult


def results_to_json_report(
    results: Sequence[RunResult],
    *,
    suite_name: str = "conjecture",
) -> dict[str, Any]:
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    return {
        "suite": suite_name,
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "results": [r.to_dict() for r in results],
    }


def write_json_report(path: str | Path, report: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(report, indent=2), encoding="utf-8")


def results_to_junit_xml(
    results: Sequence[RunResult],
    *,
    suite_name: str = "conjecture",
) -> str:
    testsuite = ET.Element(
        "testsuite",
        name=suite_name,
        tests=str(len(results)),
        failures=str(sum(1 for r in results if not r.passed)),
        errors="0",
    )
    for r in results:
        case = ET.SubElement(
            testsuite,
            "testcase",
            classname="conjecture",
            name=r.script_id,
        )
        if not r.passed:
            fail = ET.SubElement(case, "failure", message=f"{len(r.failures)} failure(s)")
            fail.text = "\n".join(r.failures)
    return ET.tostring(testsuite, encoding="unicode")


def write_junit_report(path: str | Path, results: Sequence[RunResult]) -> None:
    Path(path).write_text(results_to_junit_xml(results), encoding="utf-8")
