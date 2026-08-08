"""Portable host-product connection settings — **env only, no baked secrets**.

Extract rule
------------
Never hardcode product emails, tenant ids, public IPs, passwords, or API keys
in this package. Host monorepos set environment variables. Empty means
"not configured" — Admin/UI must show that honestly.

Canonical env (portable)
------------------------
``CONJECTURE_HOST_EMAIL``
``CONJECTURE_HOST_PASSWORD``
``CONJECTURE_HOST_BASE_URL``
``CONJECTURE_HOST_TIMEOUT_S``
``CONJECTURE_HOST_RUNNER``   module:callable for Host adapter evidence

Host monorepo aliases (Bot0 only — still env, never defaults to real accounts)
---------------------------------------------------------------------------
``CONJECTURE_BOT0_EMAIL`` / ``CONJECTURE_BOT0_PASSWORD`` / ``CONJECTURE_BOT0_BASE_URL``
are accepted as **aliases** so existing host shells keep working. They must not
appear as literal account defaults in package source.
"""
from __future__ import annotations

import os
from typing import Any


def _env(*names: str, default: str = "") -> str:
    for name in names:
        raw = (os.environ.get(name) or "").strip()
        if raw:
            return raw
    return default


def host_email() -> str:
    """Product test account email — empty if unset (never invent a demo email)."""
    return _env("CONJECTURE_HOST_EMAIL", "CONJECTURE_BOT0_EMAIL")


def host_password() -> str:
    """Product test account password — empty if unset. Never log the value."""
    return _env("CONJECTURE_HOST_PASSWORD", "CONJECTURE_BOT0_PASSWORD")


def host_base_url() -> str:
    """Product API base URL — empty if unset (host must set for E2E)."""
    return _env("CONJECTURE_HOST_BASE_URL", "CONJECTURE_BOT0_BASE_URL")


def host_timeout_s(default: float = 120.0) -> float:
    raw = _env("CONJECTURE_HOST_TIMEOUT_S", "CONJECTURE_BOT0_TIMEOUT_S")
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def host_password_set() -> bool:
    return bool(host_password())


def host_connection_status() -> dict[str, Any]:
    """JSON-safe Admin card: values only when set; no fabricated emails."""
    email = host_email()
    base = host_base_url()
    return {
        "email": email or None,
        "email_set": bool(email),
        "password_set": host_password_set(),
        "base_url": base or None,
        "base_url_set": bool(base),
        "timeout_s": host_timeout_s(),
        "env_keys": [
            "CONJECTURE_HOST_EMAIL",
            "CONJECTURE_HOST_PASSWORD",
            "CONJECTURE_HOST_BASE_URL",
            "CONJECTURE_HOST_TIMEOUT_S",
            "CONJECTURE_HOST_RUNNER",
            # aliases accepted by host monorepos
            "CONJECTURE_BOT0_EMAIL (alias)",
            "CONJECTURE_BOT0_PASSWORD (alias)",
            "CONJECTURE_BOT0_BASE_URL (alias)",
        ],
        "note": (
            "Host E2E identity is env-only — this package never ships demo emails "
            "or passwords. Set CONJECTURE_HOST_* (or host monorepo aliases) in your shell."
        ),
        "configured": bool(email and base and host_password_set()),
    }


__all__ = [
    "host_base_url",
    "host_connection_status",
    "host_email",
    "host_password",
    "host_password_set",
    "host_timeout_s",
]
