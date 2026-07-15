"""Configurable invent / LLM propose settings (public package — env only).

Does **not** hardcode product model names or adopter service keys.
Hosts may override via env; public adopters set their own endpoint.

Environment
-----------
``CONJECTURE_INVENT_MAX_PROPOSALS``
    Max geometry proposals from one LLM invent turn (default **4**).

``CONJECTURE_INVENT_MAX_SCENARIOS``
    Max Scenario/CandidatePath rows emitted from inventive geometry in one
    author run (default **4**). Caps volume after invent_all prioritization.

``CONJECTURE_INVENT_PROMPT_PATH``
    Absolute or relative path to the propose system prompt markdown.
    Default: package ``candidate_author/prompts/geometry_propose.md``.

``CONJECTURE_INVENT_LLM_BASE_URL``
    OpenAI-compatible chat completions base (e.g. ``https://api.openai.com/v1``).
    If unset, portable ``env_llm_complete`` is unavailable (host may inject).

``CONJECTURE_INVENT_LLM_MODEL``
    Model id for the invent propose call (required with base URL).

``CONJECTURE_INVENT_LLM_API_KEY``
    API key (falls back to ``OPENAI_API_KEY`` if set). Never log this value.

``CONJECTURE_INVENT_LLM_TIMEOUT_S``
    HTTP timeout seconds (default 60).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Callable, Optional


def _env_int(name: str, default: int, *, lo: int = 1, hi: int = 64) -> int:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        n = int(raw)
    except ValueError:
        return default
    return max(lo, min(hi, n))


def _env_float(name: str, default: float) -> float:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class InventConfig:
    """Resolved invent configuration for one author turn."""

    max_proposals: int = 4
    max_scenarios: int = 4
    prompt_path: str | None = None  # None → package default
    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = None
    llm_timeout_s: float = 60.0

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_base_url and self.llm_model and self.llm_api_key)


def load_invent_config() -> InventConfig:
    """Load invent config from environment (safe defaults)."""
    key = (os.environ.get("CONJECTURE_INVENT_LLM_API_KEY") or "").strip()
    if not key:
        key = (os.environ.get("OPENAI_API_KEY") or "").strip() or None
    base = (os.environ.get("CONJECTURE_INVENT_LLM_BASE_URL") or "").strip() or None
    model = (os.environ.get("CONJECTURE_INVENT_LLM_MODEL") or "").strip() or None
    prompt = (os.environ.get("CONJECTURE_INVENT_PROMPT_PATH") or "").strip() or None
    return InventConfig(
        max_proposals=_env_int("CONJECTURE_INVENT_MAX_PROPOSALS", 4),
        max_scenarios=_env_int("CONJECTURE_INVENT_MAX_SCENARIOS", 4),
        prompt_path=prompt,
        llm_base_url=base.rstrip("/") if base else None,
        llm_model=model,
        llm_api_key=key,
        llm_timeout_s=_env_float("CONJECTURE_INVENT_LLM_TIMEOUT_S", 60.0),
    )


def default_prompt_path() -> Path:
    """Package-shipped geometry propose prompt."""
    try:
        ref = resources.files("conjecture_behaviour_runner.candidate_author").joinpath(
            "prompts/geometry_propose.md",
        )
        # Python 3.11+ Traversable
        return Path(str(ref))
    except Exception:  # noqa: BLE001
        return Path(__file__).resolve().parent / "prompts" / "geometry_propose.md"


def load_geometry_propose_prompt(
    *,
    path: str | Path | None = None,
    max_proposals: int = 4,
    surfaces: str = "(none)",
    stealers: str = "(none)",
    acts: str = "typed_label, ordinal, chip_send_text",
    slugs: str = "",
) -> str:
    """Load prompt file and fill placeholders (system prompt body).

    Placeholders: ``{max_proposals}``, ``{surfaces}``, ``{stealers}``,
    ``{acts}``, ``{slugs}``. Missing file falls back to a minimal inline stub.
    """
    cfg_path = path
    if cfg_path is None:
        cfg_path = load_invent_config().prompt_path
    p = Path(cfg_path) if cfg_path else default_prompt_path()
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        # Fallback if package data not installed
        text = (
            "Propose geometry JSON only. Max {max_proposals} proposals.\n"
            "Surfaces: {surfaces}\nStealers: {stealers}\nActs: {acts}\n"
            "Slugs: {slugs}\n"
        )
    # Safe replace only for our slots — prompt body contains JSON braces.
    out = text
    for key, val in (
        ("{max_proposals}", str(max_proposals)),
        ("{surfaces}", surfaces),
        ("{stealers}", stealers),
        ("{acts}", acts),
        ("{slugs}", slugs or "(see package laws)"),
    ):
        out = out.replace(key, val)
    return out


def env_llm_complete(
    user_prompt: str,
    *,
    config: InventConfig | None = None,
    system_prompt: str | None = None,
) -> str:
    """OpenAI-compatible chat completion from env config (no product keys).

    Raises ``RuntimeError`` if env is incomplete. Never logs the API key.
    """
    cfg = config or load_invent_config()
    if not cfg.llm_configured:
        raise RuntimeError(
            "Invent LLM not configured. Set CONJECTURE_INVENT_LLM_BASE_URL, "
            "CONJECTURE_INVENT_LLM_MODEL, and CONJECTURE_INVENT_LLM_API_KEY "
            "(or OPENAI_API_KEY).",
        )
    url = f"{cfg.llm_base_url}/chat/completions"
    sys_content = system_prompt or (
        "You propose control-plane test geometry only. Output compact JSON."
    )
    body: dict[str, Any] = {
        "model": cfg.llm_model,
        "messages": [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg.llm_api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=cfg.llm_timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"Invent LLM HTTP {exc.code} (model not logged; check env)",
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Invent LLM transport error: {exc.reason}") from exc

    choices = payload.get("choices") if isinstance(payload, dict) else None
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("Invent LLM response missing choices")
    msg = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = (msg or {}).get("content") if isinstance(msg, dict) else None
    if not content:
        raise RuntimeError("Invent LLM empty content")
    return str(content)


def make_env_llm_complete(
    *,
    config: InventConfig | None = None,
    system_prompt: str | None = None,
) -> Callable[[str], str]:
    """Return ``llm_complete(user_prompt) -> str`` bound to invent env config."""

    def _complete(user_prompt: str) -> str:
        return env_llm_complete(
            user_prompt, config=config, system_prompt=system_prompt,
        )

    return _complete


__all__ = [
    "InventConfig",
    "default_prompt_path",
    "env_llm_complete",
    "load_geometry_propose_prompt",
    "load_invent_config",
    "make_env_llm_complete",
]
