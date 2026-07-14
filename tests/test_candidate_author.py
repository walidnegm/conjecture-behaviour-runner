"""Portable candidate author + example templates."""
from __future__ import annotations

from pathlib import Path

import pytest

from conjecture_behaviour_runner.candidate_author import (
    HostVocabulary,
    author_candidates,
    blocks_foreign_leaf,
    candidate_to_scenario_dict,
    load_example_template_bundle,
    write_candidate_scenarios,
)

try:
    import yaml  # noqa: F401
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


def test_blocks_foreign_leaf_portable() -> None:
    vocab = HostVocabulary(
        sole_continue_kinds=frozenset({"invoice_intake"}),
        kinds_suppress_surface=frozenset({"invoice_intake"}),
        foreign_capability_leaves=frozenset({"assessment_start"}),
        foreign_library_leaves=frozenset({"list_records"}),
        kind_to_owner={"invoice_intake": "invoice_intake"},
    )
    assert blocks_foreign_leaf(
        vocab, active_kind="invoice_intake", leaf="assessment_start",
        task_intent="continue",
    )
    assert not blocks_foreign_leaf(
        vocab, active_kind="invoice_intake", leaf="assessment_start",
        task_intent="new_task",
    )
    assert blocks_foreign_leaf(
        vocab, active_kind="invoice_intake", leaf="list_records",
        task_intent="continue",
    )
    assert not blocks_foreign_leaf(
        vocab, active_kind="invoice_intake", leaf="list_records",
        task_intent="detour",
    )


def test_example_template_authors_and_writes(tmp_path: Path) -> None:
    if yaml is None:
        pytest.skip("PyYAML not installed — pip install conjecture-behaviour-runner[scenarios]")
    bundle = load_example_template_bundle()
    assert bundle["vocabulary"] is not None
    paths = author_candidates(
        vocabulary=bundle["vocabulary"],
        matrix_cells=bundle["matrix_cells"],
        residuals=bundle["residuals"],
    )
    assert len(paths) >= 3
    # Placeholder kind appears in cross-product
    ids = {p.path_id for p in paths}
    assert any("YOUR_INTAKE_KIND" in i for i in ids)
    report = write_candidate_scenarios(paths, tmp_path)
    assert (tmp_path / "manifest.json").is_file()
    assert (tmp_path / "INDEX.md").is_file()
    assert len(report) == len(paths)
    doc = candidate_to_scenario_dict(paths[0])
    assert doc["scenario_class"] == "candidate_soak_precursor"
    assert doc["steps"]


def test_cli_candidates_author_example(tmp_path: Path) -> None:
    if yaml is None:
        pytest.skip("PyYAML not installed — pip install conjecture-behaviour-runner[scenarios]")
    from conjecture_behaviour_runner.cli import main

    out = tmp_path / "scen"
    rc = main([
        "candidates", "author", "--example", "--out", str(out), "--limit", "5",
    ])
    assert rc == 0
    assert list(out.glob("*.yaml"))
