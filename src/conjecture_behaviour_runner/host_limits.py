"""Portable host **product abuse / rate-limit** catalog for Admin + ops notes.

Why this exists
---------------
Conjecture does **not** own product rate limits. Host chat/login/LLM caps live
in the product (gateway, sim params, Redis, …). The console needs a card that:

1. Always explains the **portable failure classes** (login storm, LLM hour, …)
2. Lets a **host SPI** fill product-specific knobs (param names, defaults)
3. Never bakes one product's emails / param keys into extract defaults

SPI discovery (first match wins)
-------------------------------
1. ``CONJECTURE_HOST_LIMITS_PROVIDER`` = ``module.path:callable``
   returning a dict shaped like :func:`portable_limits_catalog`
2. Soft attribute on the resolved host runner module:
   ``product_limits_catalog()``
3. Optional JSON file: ``CONJECTURE_HOST_LIMITS_JSON`` path
4. Else portable skeleton only (``source=portable``)

Row shape (each entry in ``rows``)
---------------------------------
``key`` (stable id) · ``label`` · ``detail`` (human) · optional
``host_knob`` (product param/env name) · ``default`` · ``notes``
"""
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping, Optional


# Stable portable keys — hosts should map their knobs onto these when possible.
PORTABLE_LIMIT_KEYS: tuple[str, ...] = (
    "login",
    "chat",
    "llm_burst",
    "llm_hour",
    "thread_create",
    "empty_shells",
)


def portable_limits_catalog() -> dict[str, Any]:
    """Product-agnostic skeleton — always safe to ship in extract."""
    rows = [
        {
            "key": "login",
            "label": "Auth / login",
            "detail": (
                "Host session-mint or login rate limits. "
                "Reuse tokens across scenarios to avoid login storms."
            ),
            "host_knob": None,
            "default": None,
        },
        {
            "key": "chat",
            "label": "Chat / turn API",
            "detail": (
                "Per-user product chat or agent-turn windows. "
                "Multi-turn host scripts consume this bucket."
            ),
            "host_knob": None,
            "default": None,
        },
        {
            "key": "llm_burst",
            "label": "LLM burst window",
            "detail": (
                "Short-window cap on LLM-backed product endpoints (burst protection)."
            ),
            "host_knob": None,
            "default": None,
        },
        {
            "key": "llm_hour",
            "label": "LLM hourly window",
            "detail": (
                "Longer-window LLM storm protection — large host batches usually "
                "hit this first (429 → classify as rate_limit, not product_bug)."
            ),
            "host_knob": None,
            "default": None,
        },
        {
            "key": "thread_create",
            "label": "Conversation / thread create",
            "detail": (
                "Caps on minting new product threads. One thread per scenario "
                "is isolation-friendly but burns create quota."
            ),
            "host_knob": None,
            "default": None,
        },
        {
            "key": "empty_shells",
            "label": "Empty shells",
            "detail": (
                "Thread created but chat never landed (429 / infra) → "
                "zero-message shells. Prefer login reuse + harness title cleanup."
            ),
            "host_knob": None,
            "default": None,
        },
    ]
    return {
        "scope": "portable",
        "source": "portable",
        "host_profile": "generic",
        "title": "Host product abuse controls (why empty shells / 429s)",
        "lead": (
            "Host adapter runs hit the *product's* own rate limits — Conjecture "
            "does not own those caps. Populate product knobs via host SPI "
            "(CONJECTURE_HOST_LIMITS_PROVIDER or host.product_limits_catalog). "
            "GeometryHoldAdapter never calls product chat/login."
        ),
        "rows": rows,
        "tune_hint": (
            "Raise limits only in the environment under test. "
            "Do not bake soak-only ceilings into package defaults."
        ),
        "spi": {
            "provider_env": "CONJECTURE_HOST_LIMITS_PROVIDER=module:callable",
            "json_env": "CONJECTURE_HOST_LIMITS_JSON=/path/to/limits.json",
            "runner_attr": "product_limits_catalog",
            "row_keys": list(PORTABLE_LIMIT_KEYS),
        },
    }


def _merge_host_rows(
    base: dict[str, Any],
    overlay: Mapping[str, Any],
    *,
    source: str,
) -> dict[str, Any]:
    """Overlay host **knobs** onto portable skeleton by ``key``.

    Title + lead stay **portable** (extract-owned). Host SPI only fills
    ``host_knob`` / ``default`` / row ``detail`` / optional ``tune_hint``.
    That keeps Admin free of product brand in the card chrome.
    """
    out = dict(base)
    out["source"] = source
    # Optional host metadata (not product brand in title)
    if overlay.get("host_profile"):
        out["host_profile"] = overlay["host_profile"]
    if overlay.get("tune_hint"):
        out["tune_hint"] = overlay["tune_hint"]
    if overlay.get("scope"):
        out["scope"] = overlay["scope"]
    # Never take host title/lead into extract UI chrome unless explicit allow
    allow_brand = (
        (os.environ.get("CONJECTURE_HOST_LIMITS_ALLOW_BRANDING") or "")
        .strip()
        .lower()
        in ("1", "true", "yes", "on")
    )
    if allow_brand:
        for field in ("title", "lead"):
            if overlay.get(field):
                out[field] = overlay[field]

    by_key: dict[str, dict[str, Any]] = {}
    for row in out.get("rows") or []:
        if isinstance(row, Mapping) and row.get("key"):
            by_key[str(row["key"])] = dict(row)

    for row in overlay.get("rows") or []:
        if not isinstance(row, Mapping) or not row.get("key"):
            continue
        k = str(row["key"])
        merged = dict(by_key.get(k) or {"key": k})
        # Prefer portable label; host may refine label lightly
        for f in ("label", "detail", "host_knob", "default", "notes"):
            if row.get(f) is not None:
                merged[f] = row[f]
        if row.get("host_knob") and not row.get("detail"):
            default = row.get("default")
            merged["detail"] = (
                f"{row['host_knob']}"
                + (f" (default {default})" if default is not None else "")
            )
        by_key[k] = merged

    ordered: list[dict[str, Any]] = []
    seen: set[str] = set()
    for k in PORTABLE_LIMIT_KEYS:
        if k in by_key:
            ordered.append(by_key[k])
            seen.add(k)
    for k, row in by_key.items():
        if k not in seen:
            ordered.append(row)
    out["rows"] = ordered
    # When SPI filled any knobs, note that in lead (still product-agnostic)
    if any(r.get("host_knob") for r in ordered):
        out["lead"] = (
            "Portable failure classes below. Product-specific knobs "
            f"(source={source}) are filled by host SPI — Conjecture does not "
            "own those caps. GeometryHoldAdapter never calls product chat/login."
        )
    return out


def _load_callable(spec: str) -> Callable[[], Mapping[str, Any]]:
    mod_name, _, attr = spec.partition(":")
    if not mod_name or not attr:
        raise ValueError(f"invalid provider spec (need module:attr): {spec!r}")
    mod = importlib.import_module(mod_name)
    fn = getattr(mod, attr)
    if not callable(fn):
        raise TypeError(f"{spec} is not callable")
    return fn  # type: ignore[return-value]


def _try_provider_env() -> Optional[dict[str, Any]]:
    spec = (os.environ.get("CONJECTURE_HOST_LIMITS_PROVIDER") or "").strip()
    if not spec:
        return None
    try:
        fn = _load_callable(spec)
        raw = fn()
        if isinstance(raw, Mapping):
            return _merge_host_rows(
                portable_limits_catalog(), raw, source=f"provider:{spec}"
            )
    except Exception as exc:  # noqa: BLE001
        cat = portable_limits_catalog()
        cat["source"] = "portable"
        cat["provider_error"] = f"{type(exc).__name__}: {exc}"
        return cat
    return None


def _try_json_env() -> Optional[dict[str, Any]]:
    path = (os.environ.get("CONJECTURE_HOST_LIMITS_JSON") or "").strip()
    if not path:
        return None
    try:
        data = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
        if isinstance(data, Mapping):
            return _merge_host_rows(
                portable_limits_catalog(), data, source=f"json:{path}"
            )
    except Exception as exc:  # noqa: BLE001
        cat = portable_limits_catalog()
        cat["provider_error"] = f"{type(exc).__name__}: {exc}"
        return cat
    return None


def _try_host_runner_attr(host: Mapping[str, Any] | None) -> Optional[dict[str, Any]]:
    """If host runner module exposes product_limits_catalog, use it."""
    h = host or {}
    source = str(h.get("source") or "")
    # source looks like module:attr from resolve_host_runner
    mod_name = source.split(":")[0].strip() if source else ""
    candidates = [mod_name] if mod_name else []
    # Common host monorepo path (soft — not imported unless present)
    candidates.append("conjecture_host.http_driver")
    seen: set[str] = set()
    for name in candidates:
        if not name or name in seen:
            continue
        seen.add(name)
        try:
            mod = importlib.import_module(name)
            fn = getattr(mod, "product_limits_catalog", None)
            if callable(fn):
                raw = fn()
                if isinstance(raw, Mapping):
                    return _merge_host_rows(
                        portable_limits_catalog(),
                        raw,
                        source=f"runner:{name}.product_limits_catalog",
                    )
        except Exception:  # noqa: BLE001
            continue
    return None


def resolve_host_limits_catalog(
    host: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve Admin card payload: portable skeleton ⊕ optional host SPI."""
    for loader in (_try_provider_env, _try_json_env):
        got = loader()
        if got is not None and not got.get("provider_error"):
            return got
        if got is not None and got.get("provider_error"):
            # fall through but keep error on final if nothing else works
            err_cat = got
        else:
            err_cat = None
    got = _try_host_runner_attr(host)
    if got is not None:
        return got
    base = portable_limits_catalog()
    if host and host.get("available"):
        base["lead"] = (
            base["lead"]
            + " Host runner is available but did not publish product_limits_catalog — "
            "showing portable categories only."
        )
    return base


__all__ = [
    "PORTABLE_LIMIT_KEYS",
    "portable_limits_catalog",
    "resolve_host_limits_catalog",
]
