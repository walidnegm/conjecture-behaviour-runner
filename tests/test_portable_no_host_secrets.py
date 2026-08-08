"""Ratchet: portable package must not ship host emails, passwords, or tenant ids."""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "conjecture_behaviour_runner"

# Literals that must never appear as *defaults* in portable source.
# (Product brand "Bot0" in docs is OK; real account emails are not.)
FORBIDDEN_SUBSTRINGS = (
    "admin@aicorp.com",
    "admin@bot0.ai",
    "@aicorp.com",
    "B!t0admin",
    "bot0admin",
    "STAGING_DB_PASSWORD",
    "bot0-staging-bastion",
    "52.72.134.0",
)


def _iter_text_files():
    for p in SRC.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix not in {".py", ".md", ".txt", ".yml", ".yaml", ".toml"}:
            continue
        if "__pycache__" in p.parts:
            continue
        yield p


def test_no_forbidden_host_literals_in_package_src() -> None:
    hits: list[str] = []
    for path in _iter_text_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for bad in FORBIDDEN_SUBSTRINGS:
            if bad in text:
                rel = path.relative_to(ROOT)
                hits.append(f"{rel}: contains {bad!r}")
    assert not hits, "Portable package leaked host-only secrets/defaults:\n" + "\n".join(
        hits
    )


def test_host_env_has_no_email_default() -> None:
    import os

    from conjecture_behaviour_runner.host_env import (
        host_base_url,
        host_connection_status,
        host_email,
        host_password,
    )

    # Clear host env so we prove package defaults are empty
    for k in list(os.environ):
        if k.startswith("CONJECTURE_HOST_") or k.startswith("CONJECTURE_BOT0_"):
            if k.endswith(("_EMAIL", "_PASSWORD", "_BASE_URL")):
                os.environ.pop(k, None)

    assert host_email() == ""
    assert host_password() == ""
    assert host_base_url() == ""
    st = host_connection_status()
    assert st["email"] is None
    assert st["email_set"] is False
    assert st["configured"] is False
    assert "admin@" not in (st.get("note") or "")


def test_host_env_reads_portable_and_alias() -> None:
    import os

    from conjecture_behaviour_runner.host_env import host_email

    os.environ["CONJECTURE_HOST_EMAIL"] = "tester@example.com"
    os.environ.pop("CONJECTURE_BOT0_EMAIL", None)
    assert host_email() == "tester@example.com"
    os.environ.pop("CONJECTURE_HOST_EMAIL", None)
    os.environ["CONJECTURE_BOT0_EMAIL"] = "alias@example.com"
    assert host_email() == "alias@example.com"
    os.environ.pop("CONJECTURE_BOT0_EMAIL", None)
