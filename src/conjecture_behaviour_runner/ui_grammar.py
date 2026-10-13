"""A small grammar for UI steps — locators, settle conditions, invariants.

Kept deliberately small (no selector DSL, no page objects) so a scenario file
stays readable and any UI driver can implement it:

  locator     testid:<id>[#n] · text:<text> · placeholder:<text> · role:<role>=<name>
              (#n picks the n-th match, 0-based)
  checks      visible:<locator> · hidden:<locator> · count:<locator>=<n> ·
              text:<locator>~<substring> · networkidle · delay:<ms> ·
              model_calls_at_most:<n>

``${NAME}`` in any string is replaced from the environment, so one scenario
runs against any stack whose seed holds the data it names. Pure functions;
the driver (Playwright, Cypress, …) is the host's.
"""
from __future__ import annotations

import os
import re
from typing import Any

__all__ = ["LOCATOR_KINDS", "CHECK_KINDS", "expand", "parse_check", "parse_locator"]

LOCATOR_KINDS = ("testid", "text", "placeholder", "role")
CHECK_KINDS = ("visible", "hidden", "count", "text", "networkidle", "delay", "model_calls_at_most", "llm_calls_at_most")

_VAR = re.compile(r"\$\{([A-Z0-9_]+)\}")


def expand(value: Any) -> Any:
    """Replace ``${NAME}`` from the environment; unknown names stay as written."""
    if isinstance(value, str):
        return _VAR.sub(lambda m: os.getenv(m.group(1), m.group(0)), value)
    if isinstance(value, dict):
        return {k: expand(v) for k, v in value.items()}
    if isinstance(value, list):
        return [expand(v) for v in value]
    return value


def parse_locator(spec: str) -> tuple[str, str, int]:
    """``testid:x#2`` → ("testid", "x", 2). Raises on an unknown kind."""
    kind, _, rest = str(spec).partition(":")
    kind = kind.strip()
    if kind not in LOCATOR_KINDS or not rest:
        raise ValueError(f"unknown locator {spec!r}")
    nth = 0
    m = re.match(r"^(.*)#(\d+)$", rest)
    if m:
        rest, nth = m.group(1), int(m.group(2))
    return kind, rest, nth


def parse_check(spec: str) -> tuple[str, str, str]:
    """A settle condition or invariant → (kind, locator-or-arg, expected)."""
    kind, _, rest = str(spec).partition(":")
    kind = kind.strip()
    if kind == "networkidle":
        return kind, "", ""
    if kind in ("delay", "model_calls_at_most", "llm_calls_at_most", "visible", "hidden"):
        return kind, rest.strip(), ""
    if kind == "count":
        loc, _, n = rest.rpartition("=")
        return kind, loc.strip(), n.strip()
    if kind == "text":
        loc, _, sub = rest.partition("~")
        return kind, loc.strip(), sub
    raise ValueError(f"unknown check {spec!r}")
