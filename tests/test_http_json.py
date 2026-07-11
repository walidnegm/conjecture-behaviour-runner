"""HttpJsonAdapter dig helper + construction (no network)."""
from __future__ import annotations

import pytest

from conjecture_behaviour_runner.contrib.http_json import HttpJsonAdapter, _dig


def test_dig_nested() -> None:
    data = {"debug": {"owner": "cost_out", "pins": {"workflow_id": "wf_1"}}}
    assert _dig(data, "debug.owner") == "cost_out"
    assert _dig(data, "debug.pins.workflow_id") == "wf_1"
    assert _dig(data, "missing.path") is None


def test_adapter_rejects_bad_endpoint() -> None:
    with pytest.raises(ValueError):
        HttpJsonAdapter(endpoint="not-a-url")
