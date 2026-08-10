"""Portable host limits catalog + SPI merge."""
from __future__ import annotations

import json
from pathlib import Path

from conjecture_behaviour_runner.host_limits import (
    PORTABLE_LIMIT_KEYS,
    portable_limits_catalog,
    resolve_host_limits_catalog,
)


def test_portable_catalog_has_stable_keys() -> None:
    cat = portable_limits_catalog()
    assert cat["source"] == "portable"
    keys = [r["key"] for r in cat["rows"]]
    assert list(PORTABLE_LIMIT_KEYS) == keys
    # No product param names in portable details
    blob = json.dumps(cat)
    assert "bot0_chat_max" not in blob
    assert "llm_request_max_per_hour" not in blob
    assert "admin@" not in blob


def test_merge_via_json_env(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "limits.json"
    path.write_text(
        json.dumps(
            {
                "host_profile": "acme",
                "title": "Acme limits",  # ignored unless ALLOW_BRANDING
                "rows": [
                    {
                        "key": "llm_hour",
                        "host_knob": "ACME_LLM_HOUR",
                        "default": "100",
                        "detail": "Acme hourly LLM",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("CONJECTURE_HOST_LIMITS_JSON", str(path))
    monkeypatch.delenv("CONJECTURE_HOST_LIMITS_PROVIDER", raising=False)
    monkeypatch.delenv("CONJECTURE_HOST_LIMITS_ALLOW_BRANDING", raising=False)
    cat = resolve_host_limits_catalog(host={})
    # Title stays portable — SPI fills knobs only
    assert "empty shells" in cat["title"].lower() or "abuse" in cat["title"].lower()
    assert cat["title"] != "Acme limits"
    assert cat["host_profile"] == "acme"
    hour = next(r for r in cat["rows"] if r["key"] == "llm_hour")
    assert hour["host_knob"] == "ACME_LLM_HOUR"
    assert hour["default"] == "100"
    assert {r["key"] for r in cat["rows"]} >= set(PORTABLE_LIMIT_KEYS)


def test_host_spi_does_not_brand_title_without_flag(monkeypatch) -> None:
    """Monorepo driver knobs must not rename the portable Admin card."""
    monkeypatch.delenv("CONJECTURE_HOST_LIMITS_JSON", raising=False)
    monkeypatch.delenv("CONJECTURE_HOST_LIMITS_PROVIDER", raising=False)
    monkeypatch.delenv("CONJECTURE_HOST_LIMITS_ALLOW_BRANDING", raising=False)
    cat = resolve_host_limits_catalog(
        host={
            "available": True,
            "source": "regression_suite.conjecture_bot0_http_driver:run",
        }
    )
    assert "Bot0 monorepo" not in cat["title"]
    assert "Bot0 monorepo" not in (cat.get("lead") or "")
    # If monorepo SPI is importable, knobs should appear
    if "runner:" in str(cat.get("source") or ""):
        assert any(r.get("host_knob") for r in cat["rows"])
