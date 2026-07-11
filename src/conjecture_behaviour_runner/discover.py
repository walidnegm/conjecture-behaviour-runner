"""Script discovery for the CLI runner."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, Sequence

from conjecture_behaviour_runner.script import ConjectureScript, script_from_dict


def iter_script_paths(
    roots: Sequence[str | Path],
    *,
    pattern: str = "*.json",
) -> Iterator[Path]:
    for root in roots:
        p = Path(root)
        if p.is_file() and p.suffix in {".json", ".yaml", ".yml"}:
            yield p
            continue
        if p.is_dir():
            yield from sorted(p.rglob(pattern))
            for yaml_pat in ("*.yaml", "*.yml"):
                yield from sorted(p.rglob(yaml_pat))


def load_script_path(path: Path) -> ConjectureScript:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "YAML scripts require PyYAML — "
                "pip install conjecture-behaviour-runner[scenarios]"
            ) from exc
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return script_from_dict(data)


def discover_scripts(
    roots: Sequence[str | Path],
    *,
    tags: Sequence[str] = (),
    script_id_prefix: str = "",
) -> list[tuple[Path, ConjectureScript]]:
    """Load scripts under roots; optional tag filter (all tags must match)."""
    seen: set[Path] = set()
    out: list[tuple[Path, ConjectureScript]] = []
    for path in iter_script_paths(roots):
        path = path.resolve()
        if path in seen:
            continue
        seen.add(path)
        try:
            script = load_script_path(path)
        except Exception:
            continue
        if script_id_prefix and not script.script_id.startswith(script_id_prefix):
            continue
        if tags:
            stags = set(script.tags)
            if not all(t in stags for t in tags):
                continue
        out.append((path, script))
    return out
