"""Portable pipeline stage tracker (discovery + generic contract)."""
from __future__ import annotations

from conjecture_behaviour_runner.pipeline_tracker import (
    AUTHORING_LADDER_STAGES,
    DISCOVERY_LADDER_STAGES,
    discovery_lifecycle_payload,
    format_lifecycle_table,
    lifecycle_payload,
    render_discovery_lifecycle_diagram,
    render_lifecycle_diagram,
)


def test_discovery_ladder_order_and_states() -> None:
    views = discovery_lifecycle_payload("scenario")
    keys = [v.key for v in views]
    assert keys == ["vocab", "invent", "expand", "scenario", "script", "sealed"]
    by = {v.key: v.state for v in views}
    assert by["vocab"] == "complete"
    assert by["invent"] == "complete"
    assert by["expand"] == "complete"
    assert by["scenario"] == "current"
    assert by["script"] == "upcoming"
    assert by["sealed"] == "upcoming"


def test_unknown_current_falls_back_to_first() -> None:
    views = lifecycle_payload(DISCOVERY_LADDER_STAGES, "not_a_stage")
    assert views[0].state == "current"
    assert all(v.state == "upcoming" for v in views[1:])


def test_render_diagram_marks_current_and_complete() -> None:
    line = render_discovery_lifecycle_diagram("expand")
    assert "Discovery path" in line
    assert "~~Host vocab~~" in line
    assert "~~Invent~~" in line
    assert "**Expand**" in line
    assert "Scenario" in line and "~~Scenario~~" not in line


def test_authoring_ladder_same_contract() -> None:
    views = lifecycle_payload(AUTHORING_LADDER_STAGES, "draft_ir")
    assert [v.key for v in views] == ["prose", "draft_ir", "staffed_ir", "save"]
    assert views[1].state == "current"
    line = render_lifecycle_diagram(AUTHORING_LADDER_STAGES, "staffed_ir", title="Where we are")
    assert "**Staffed IR**" in line
    assert "~~Prose~~" in line


def test_format_table_has_headers() -> None:
    md = format_lifecycle_table(DISCOVERY_LADDER_STAGES, "invent")
    assert "| Stage |" in md
    assert "Invent" in md
    assert "● now" in md
