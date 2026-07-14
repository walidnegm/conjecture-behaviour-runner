"""Load example / host YAML into portable author models."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from conjecture_behaviour_runner.candidate_author.models import (
    HostIncident,
    HostVocabulary,
    MatrixCell,
    ResidualProbe,
)


def _require_yaml():
    """PyYAML is optional (``[scenarios]`` extra); only needed when loading YAML templates."""
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "YAML template load requires PyYAML — "
            "pip install conjecture-behaviour-runner[scenarios]"
        ) from exc
    return yaml

# templates: package-local first, then extract repo templates/
_PKG = Path(__file__).resolve().parent
_PKG_TEMPLATES = _PKG / "templates"
# editable: .../candidate_author → src → package root
_REPO_TEMPLATES = _PKG.parents[3] / "templates" / "candidate_author"


def _templates_dir() -> Path:
    for p in (_PKG_TEMPLATES, _REPO_TEMPLATES):
        if p.is_dir() and (p / "host_vocabulary.example.yaml").is_file():
            return p
    return _PKG_TEMPLATES


def _load_yaml(path: Path) -> dict[str, Any]:
    yaml = _require_yaml()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def load_vocabulary_yaml(path: Path | str) -> HostVocabulary:
    data = _load_yaml(Path(path))
    return HostVocabulary(
        sole_continue_kinds=frozenset(data.get("sole_continue_kinds") or []),
        kinds_suppress_surface=frozenset(
            data.get("kinds_suppress_surface")
            or data.get("sole_continue_kinds")
            or []
        ),
        foreign_capability_leaves=frozenset(
            data.get("foreign_capability_leaves") or []
        ),
        foreign_library_leaves=frozenset(data.get("foreign_library_leaves") or []),
        kind_to_owner=dict(data.get("kind_to_owner") or {}),
        hard_escape_intents=frozenset(
            data.get("hard_escape_intents")
            or ("new_task", "abandon", "handoff")
        ),
        soft_escape_intents=frozenset(
            data.get("soft_escape_intents")
            or ("detour", "new_task", "abandon", "handoff")
        ),
    )


def load_matrix_yaml(path: Path | str) -> list[MatrixCell]:
    data = _load_yaml(Path(path))
    cells: list[MatrixCell] = []
    for raw in data.get("cells") or []:
        if not isinstance(raw, dict):
            continue
        cells.append(
            MatrixCell(
                cell_id=str(raw["cell_id"]),
                mode_slug=str(raw.get("mode_slug") or raw.get("slug") or ""),
                failure_mode=str(raw.get("failure_mode") or ""),
                kind=str(raw.get("kind") or "none"),
                phase=str(raw.get("phase") or "sole_continue"),
                pin=str(raw.get("pin") or "none"),
                move=str(raw.get("move") or "continue"),
                status=str(raw.get("status") or "seed_pending"),
                note=str(raw.get("note") or ""),
                probe_utterance=str(raw.get("probe_utterance") or ""),
            ),
        )
    return cells


def load_residuals_yaml(path: Path | str) -> list[ResidualProbe]:
    data = _load_yaml(Path(path))
    out: list[ResidualProbe] = []
    for raw in data.get("residuals") or []:
        if not isinstance(raw, dict):
            continue
        out.append(
            ResidualProbe(
                path_id=str(raw["path_id"]),
                title=str(raw.get("title") or raw["path_id"]),
                failure_class_slug=str(
                    raw.get("failure_class_slug") or raw.get("failure_class") or "gap"
                ),
                start_state=dict(raw.get("start_state") or {}),
                turns=tuple(raw.get("turns") or ("continue",)),
                must_hold=tuple(raw.get("must_hold") or ()),
                must_not=tuple(raw.get("must_not") or ()),
                priority=raw.get("priority") or "high",  # type: ignore[arg-type]
                seal_status=raw.get("seal_status") or "open",  # type: ignore[arg-type]
                proof_pointer=str(raw.get("proof_pointer") or ""),
                notes=str(raw.get("notes") or ""),
                pin_hints=dict(raw.get("pin_hints") or {}),
            ),
        )
    return out


def load_incidents_yaml(path: Path | str) -> list[HostIncident]:
    data = _load_yaml(Path(path))
    out: list[HostIncident] = []
    for raw in data.get("incidents") or []:
        if not isinstance(raw, dict):
            continue
        out.append(
            HostIncident(
                incident_id=str(raw["incident_id"]),
                failure_class_slug=str(raw.get("failure_class_slug") or ""),
                symptom=str(raw.get("symptom") or ""),
                exclusive_owner_should_win=str(
                    raw.get("exclusive_owner_should_win") or ""
                ),
                fix_artifact=str(raw.get("fix_artifact") or ""),
                ratchet_module=str(raw.get("ratchet_module") or ""),
                status=raw.get("status") or "sealed",  # type: ignore[arg-type]
            ),
        )
    return out


def load_example_template_bundle(
    templates_dir: Optional[Path | str] = None,
) -> dict[str, Any]:
    """Load shipped example YAMLs (placeholder host vocabulary)."""
    base = Path(templates_dir) if templates_dir else _templates_dir()
    vocab_path = base / "host_vocabulary.example.yaml"
    matrix_path = base / "matrix.example.yaml"
    residual_path = base / "residual.example.yaml"
    result: dict[str, Any] = {
        "templates_dir": str(base),
        "vocabulary": None,
        "matrix_cells": [],
        "residuals": [],
    }
    if vocab_path.is_file():
        result["vocabulary"] = load_vocabulary_yaml(vocab_path)
    if matrix_path.is_file():
        result["matrix_cells"] = load_matrix_yaml(matrix_path)
    if residual_path.is_file():
        result["residuals"] = load_residuals_yaml(residual_path)
    return result


__all__ = [
    "load_example_template_bundle",
    "load_incidents_yaml",
    "load_matrix_yaml",
    "load_residuals_yaml",
    "load_vocabulary_yaml",
]
