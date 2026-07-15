"""Code-seed candidate paths from host vocabulary (no LLM, no product routing).

Portable cross-products + incident/matrix/residual seeds.
Host fills ``HostVocabulary``; engine does not import host agents.
"""
from __future__ import annotations

from typing import Iterable, Optional, Sequence

from conjecture_behaviour_runner.candidate_author.models import (
    CandidatePath,
    HostIncident,
    HostVocabulary,
    MatrixCell,
    ResidualProbe,
    SealStatus,
    blocks_foreign_leaf,
)


def paths_from_incidents(
    incidents: Sequence[HostIncident],
) -> list[CandidatePath]:
    out: list[CandidatePath] = []
    for row in incidents:
        if row.status == "ok_glossary":
            continue
        seal: SealStatus = (
            "regression_check" if row.status == "sealed" else "open"
        )
        out.append(
            CandidatePath(
                path_id=f"incident.{row.incident_id}",
                source="host_incident",
                priority="medium" if row.status == "sealed" else "high",
                failure_class=row.failure_class_slug,
                title=f"Incident replay: {row.incident_id}",
                start_state={
                    "exclusive_owner_should_win": row.exclusive_owner_should_win,
                },
                turns=(
                    f"(setup) Reach state where exclusive owner should be "
                    f"{row.exclusive_owner_should_win}",
                    f"(probe) Act that previously caused: {row.symptom[:180]}",
                ),
                must_hold=(
                    f"exclusive_owner≈{row.exclusive_owner_should_win}",
                ),
                must_not=(
                    "wrong leaf / steal of the sealed class",
                ),
                seal_status=seal,
                proof_pointer=(
                    f"{row.ratchet_module} · {row.fix_artifact}".strip(" ·")
                ),
                notes=row.symptom[:240],
            ),
        )
    return out


def paths_from_sole_continue_x_foreign(
    vocab: HostVocabulary,
) -> list[CandidatePath]:
    out: list[CandidatePath] = []
    for kind in sorted(vocab.kinds_suppress_surface):
        owner = vocab.owner_for(kind)
        for leaf in sorted(vocab.foreign_capability_leaves):
            blocked = blocks_foreign_leaf(
                vocab, active_kind=kind, leaf=leaf, task_intent="continue",
            )
            out.append(
                CandidatePath(
                    path_id=f"scx.{kind}.continue.{leaf}",
                    source="sole_continue_x_foreign",
                    priority="medium",
                    failure_class="missing_sole_continue",
                    title=f"Mid-{kind}: foreign capability `{leaf}` must not start",
                    start_state={
                        "active_task.kind": kind,
                        "task_intent": "continue",
                    },
                    turns=(
                        f"(setup) Establish sole-continue kind={kind}",
                        f"(probe) Surface/capability label leaf={leaf} "
                        f"with task_intent=continue",
                    ),
                    must_hold=(
                        f"active_task.kind stays {kind} (or explicit escape)",
                        f"exclusive_owner≈{owner}",
                    ),
                    must_not=(
                        f"foreign greenfield start for {leaf}",
                    ),
                    seal_status="partial" if blocked else "open",
                    proof_pointer=(
                        "host sole_continue_blocks_foreign"
                        if blocked
                        else "UNSEALED — host must gate this leaf"
                    ),
                    pin_hints={
                        "task_intent": "continue",
                        "read_kind": leaf,
                    },
                ),
            )
        for leaf in sorted(vocab.foreign_library_leaves):
            blocked = blocks_foreign_leaf(
                vocab, active_kind=kind, leaf=leaf, task_intent="continue",
            )
            out.append(
                CandidatePath(
                    path_id=f"scx.{kind}.continue.{leaf}",
                    source="sole_continue_x_foreign",
                    priority="medium",
                    failure_class="missing_sole_continue",
                    title=f"Mid-{kind}: library `{leaf}` on continue",
                    start_state={
                        "active_task.kind": kind,
                        "task_intent": "continue",
                    },
                    turns=(
                        f"(setup) kind={kind} sole-continue",
                        f"(probe) library/open shaped leaf={leaf}",
                    ),
                    must_hold=(f"kind={kind} continues stream",),
                    must_not=(f"library open via {leaf} steals turn",),
                    seal_status="partial" if blocked else "open",
                    proof_pointer="host library mid sole-continue gate",
                    pin_hints={
                        "task_intent": "continue",
                        "read_kind": leaf,
                    },
                ),
            )

    residual_kinds = sorted(
        vocab.sole_continue_kinds - vocab.kinds_suppress_surface,
    )
    sample_leaves = sorted(vocab.foreign_capability_leaves)[:3]
    for kind in residual_kinds:
        for leaf in sample_leaves:
            blocked = blocks_foreign_leaf(
                vocab, active_kind=kind, leaf=leaf, task_intent="continue",
            )
            out.append(
                CandidatePath(
                    path_id=f"scx.residual.{kind}.continue.{leaf}",
                    source="sole_continue_x_foreign",
                    priority="high",
                    failure_class="missing_sole_continue",
                    title=(
                        f"RESIDUAL: kind={kind} not in surface-suppress set — "
                        f"probe foreign {leaf}"
                    ),
                    start_state={
                        "active_task.kind": kind,
                        "task_intent": "continue",
                        "in_suppress_set": "false",
                    },
                    turns=(
                        f"(setup) Mid-flight {kind}",
                        f"(probe) Greenfield-shaped {leaf} with continue",
                    ),
                    must_hold=(
                        "surface-suppress expands to this kind, or active "
                        "handler proven to refuse foreign start",
                    ),
                    must_not=(f"silent start of {leaf} mid {kind}",),
                    seal_status="open" if not blocked else "partial",
                    proof_pointer="kinds_suppress_surface gap",
                    pin_hints={
                        "task_intent": "continue",
                        "read_kind": leaf,
                    },
                ),
            )
    return out


def paths_from_matrix_cells(
    cells: Sequence[MatrixCell],
) -> list[CandidatePath]:
    out: list[CandidatePath] = []
    for cell in cells:
        if cell.status not in ("seed_pending", "gap", "open"):
            continue
        probe = cell.probe_utterance or f"({cell.move} move)"
        out.append(
            CandidatePath(
                path_id=f"matrix.{cell.cell_id}",
                source="matrix_queue",
                priority="high",
                failure_class=cell.failure_mode or cell.mode_slug,
                title=f"Matrix {cell.status}: {cell.mode_slug} / {cell.cell_id}",
                start_state={
                    "kind": cell.kind,
                    "phase": cell.phase,
                    "pin": cell.pin,
                    "move": cell.move,
                },
                turns=(
                    f"(setup) kind={cell.kind} phase={cell.phase} pin={cell.pin}",
                    f"(probe) {probe}",
                ),
                must_hold=(f"law for mode {cell.mode_slug}",),
                must_not=("failure mode of this matrix slug",),
                seal_status="open",
                proof_pointer=f"matrix cell {cell.cell_id}",
                notes=cell.note,
                pin_hints={
                    "task_intent": "continue" if cell.move == "continue" else cell.move,
                },
            ),
        )
    return out


def paths_from_residuals(
    residuals: Sequence[ResidualProbe],
) -> list[CandidatePath]:
    return [
        CandidatePath(
            path_id=r.path_id,
            source="residual",
            priority=r.priority,
            failure_class=r.failure_class_slug,
            title=r.title,
            start_state=dict(r.start_state),
            turns=tuple(r.turns),
            must_hold=tuple(r.must_hold),
            must_not=tuple(r.must_not),
            seal_status=r.seal_status,
            proof_pointer=r.proof_pointer,
            notes=r.notes,
            pin_hints=dict(r.pin_hints),
        )
        for r in residuals
    ]


def author_candidates(
    *,
    vocabulary: Optional[HostVocabulary] = None,
    incidents: Sequence[HostIncident] = (),
    matrix_cells: Sequence[MatrixCell] = (),
    residuals: Sequence[ResidualProbe] = (),
    include_cross_product: bool = True,
    include_invention: bool = True,
    open_only: bool = False,
    limit: Optional[int] = None,
) -> list[CandidatePath]:
    """Deterministic candidate author (no LLM).

    * **Invention** (default on): exclusive-surface × typed-act × pre-decide
      stealer geometry — invents failures expansive cross-product misses.
    * **Expansion** (``include_cross_product``): sole-continue × foreign leaves.
    * Incidents / matrix / residuals: host seeds.
    """
    paths: list[CandidatePath] = []
    if incidents:
        paths.extend(paths_from_incidents(incidents))
    if include_invention and vocabulary is not None:
        from conjecture_behaviour_runner.candidate_author.invent import invent_all
        from conjecture_behaviour_runner.candidate_author.invent_config import (
            load_invent_config,
        )

        # Cap inventive scenarios per author turn (default 4 via env).
        invent_limit = load_invent_config().max_scenarios
        paths.extend(invent_all(vocabulary, limit=invent_limit))
    if include_cross_product and vocabulary is not None:
        paths.extend(paths_from_sole_continue_x_foreign(vocabulary))
    if matrix_cells:
        paths.extend(paths_from_matrix_cells(matrix_cells))
    if residuals:
        paths.extend(paths_from_residuals(residuals))

    pri = {"high": 0, "medium": 1, "low": 2}
    seal_rank = {"open": 0, "partial": 1, "sealed": 2, "regression_check": 3}
    # Invention before pure expansion when priority ties
    source_rank = {
        "invention": 0,
        "residual": 1,
        "residual_heuristic": 1,
        "host_incident": 2,
        "matrix_queue": 3,
        "sole_continue_x_foreign": 4,
        "example": 5,
    }

    def _key(p: CandidatePath) -> tuple:
        return (
            pri.get(p.priority, 9),
            seal_rank.get(p.seal_status, 9),
            source_rank.get(p.source, 9),
            p.path_id,
        )

    paths = sorted(paths, key=_key)
    if open_only:
        paths = [p for p in paths if p.seal_status in ("open", "partial")]
    if limit is not None and limit >= 0:
        paths = paths[:limit]
    return paths


def format_candidates_markdown(paths: Iterable[CandidatePath]) -> str:
    paths = list(paths)
    by_seal: dict[str, int] = {}
    by_src: dict[str, int] = {}
    for p in paths:
        by_seal[p.seal_status] = by_seal.get(p.seal_status, 0) + 1
        by_src[p.source] = by_src.get(p.source, 0) + 1
    lines = [
        "# Candidate paths (portable Conjecture author)",
        "",
        "Host vocabulary × incidents × matrix × residuals. "
        "**Not** product routing. **Not** LLM discovery.",
        "",
        f"**count:** {len(paths)}  by_seal={by_seal}  by_source={by_src}",
        "",
    ]
    for p in paths:
        lines.append(f"### `{p.path_id}` — {p.title}")
        lines.append(
            f"- **source:** {p.source} · **priority:** {p.priority} · "
            f"**seal:** {p.seal_status}"
        )
        lines.append(f"- **failure_class:** {p.failure_class}")
        lines.append(f"- **start:** `{p.start_state}`")
        lines.append("- **turns:**")
        for i, t in enumerate(p.turns, 1):
            lines.append(f"  {i}. {t}")
        lines.append(f"- **must hold:** {', '.join(p.must_hold) or '—'}")
        lines.append(f"- **must not:** {', '.join(p.must_not) or '—'}")
        if p.proof_pointer:
            lines.append(f"- **proof:** {p.proof_pointer}")
        lines.append("")
    return "\n".join(lines)


__all__ = [
    "author_candidates",
    "format_candidates_markdown",
    "paths_from_incidents",
    "paths_from_matrix_cells",
    "paths_from_residuals",
    "paths_from_sole_continue_x_foreign",
]
