"""Single version source for package metadata, CLI, and docs checks.

Prefer installed package metadata; fall back to the constant when running
from a source tree without an editable install.
"""
from __future__ import annotations

# Keep in lockstep with pyproject.toml [project].version
__version__ = "0.1.6"


def get_version() -> str:
    """Return the package version (metadata if installed, else source constant)."""
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version("conjecture-behaviour-runner")
        except PackageNotFoundError:
            return __version__
    except Exception:  # noqa: BLE001 — never break CLI on metadata quirks
        return __version__
