"""Reusable **pipeline stage tracker** for multi-step dialogue / IR progress.

Same contract shape as product authoring ladders (Prose → Draft IR → Staffed IR
→ Compile/save): ordered stages with ``complete | current | upcoming`` state.

Use for:
  * **Discovery** (this package) — host vocab → invent → expand → scenario → script → sealed
  * **Authoring IR** (host apps) — prose → draft_ir → staffed_ir → save
  * Future dialogue pipelines that need one shared “where we are” strip

Code owns stage keys and labels; UIs only render the payload.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Literal, Optional, Sequence

StageState = Literal["complete", "current", "upcoming"]


@dataclass(frozen=True)
class PipelineStageDef:
    """Static stage definition (ladder template)."""

    key: str
    label: str
    hint: str
    meaning: str = ""


@dataclass(frozen=True)
class PipelineStageView:
    """One rendered stage for FE / markdown / console."""

    key: str
    label: str
    hint: str
    state: StageState
    meaning: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "key": self.key,
            "label": self.label,
            "hint": self.hint,
            "state": self.state,
            "meaning": self.meaning,
        }


# ---------------------------------------------------------------------------
# Discovery ladder (candidate author — invent + expand)
# Parallel to product authoring: Prose → Draft IR → Staffed IR → Compile/save
# ---------------------------------------------------------------------------

DISCOVERY_LADDER_STAGES: tuple[PipelineStageDef, ...] = (
    PipelineStageDef(
        key="vocab",
        label="Host vocab",
        hint="kinds · surfaces · stealers",
        meaning=(
            "Host declares sole-continue kinds, foreign leaves, and invent "
            "geometry (exclusive surfaces, pre-decide stealers, typed acts). "
            "No product agents are imported into Conjecture."
        ),
    ),
    PipelineStageDef(
        key="invent",
        label="Invent",
        hint="surface × act × stealer",
        meaning=(
            "Inventor engine: exclusive-owner geometry — when a surface is "
            "armed, a typed reply must not yield to a pre-decide stealer. "
            "Finds polarities expansion misses. Cap default 4 scenarios."
        ),
    ),
    PipelineStageDef(
        key="expand",
        label="Expand",
        hint="kind × foreign leaf",
        meaning=(
            "Expander engine: finite cross-product of mid-flight kinds with "
            "foreign capability/library leaves, plus matrix/residual seeds. "
            "High volume; invent runs first when both apply."
        ),
    ),
    PipelineStageDef(
        key="scenario",
        label="Scenario",
        hint="candidate YAML",
        meaning=(
            "CandidatePath → Conjecture Scenario YAML (description language). "
            "Review in the local console; not yet a CI golden."
        ),
    ),
    PipelineStageDef(
        key="script",
        label="Script",
        hint="CI golden",
        meaning=(
            "Compile / author Conjecture Script — turns + pins + invariants. "
            "This is the executable test case under stub/freeze cognition."
        ),
    ),
    PipelineStageDef(
        key="sealed",
        label="Sealed",
        hint="forever regression",
        meaning=(
            "Land pattern under incidents/ (portable seed) or host ratchet. "
            "Seal status open → partial → sealed / regression_check."
        ),
    ),
)

# Illustrative authoring ladder (same tracker contract; host owns product IR).
AUTHORING_LADDER_STAGES: tuple[PipelineStageDef, ...] = (
    PipelineStageDef(
        key="prose",
        label="Prose",
        hint="chat draft steps",
        meaning="Conversational sketch — not structured IR yet.",
    ),
    PipelineStageDef(
        key="draft_ir",
        label="Draft IR",
        hint="structure review",
        meaning="Intermediate representation of process structure only.",
    ),
    PipelineStageDef(
        key="staffed_ir",
        label="Staffed IR",
        hint="who does each step",
        meaning="Second intermediate: staffing / pre-build cleanup.",
    ),
    PipelineStageDef(
        key="save",
        label="Compile / save",
        hint="real artifact",
        meaning="Committed artifact — not another intermediate.",
    ),
)


def lifecycle_payload(
    stages: Sequence[PipelineStageDef],
    current: str,
) -> list[PipelineStageView]:
    """Build complete|current|upcoming views for an ordered ladder.

    Unknown ``current`` falls back to the first stage.
    """
    keys = {s.key for s in stages}
    cur = (current or "").strip().lower()
    if cur not in keys:
        cur = stages[0].key if stages else ""

    past = True
    out: list[PipelineStageView] = []
    for stage in stages:
        if stage.key == cur:
            state: StageState = "current"
            past = False
        elif past:
            state = "complete"
        else:
            state = "upcoming"
        out.append(
            PipelineStageView(
                key=stage.key,
                label=stage.label,
                hint=stage.hint,
                state=state,
                meaning=stage.meaning,
            ),
        )
    return out


def discovery_lifecycle_payload(current: str = "invent") -> list[PipelineStageView]:
    """Candidate discovery strip: vocab → invent → expand → scenario → script → sealed."""
    return lifecycle_payload(DISCOVERY_LADDER_STAGES, current)


def authoring_lifecycle_payload(current: str = "draft_ir") -> list[PipelineStageView]:
    """Host-style IR authoring strip (same tracker; product labels)."""
    return lifecycle_payload(AUTHORING_LADDER_STAGES, current)


def render_lifecycle_diagram(
    stages: Sequence[PipelineStageDef] | Sequence[PipelineStageView],
    current: Optional[str] = None,
    *,
    title: str = "Where we are",
) -> str:
    """One-line markdown progress strip (authoring-style).

    Completed stages use strikethrough; current is bold.
    """
    if not stages:
        return f"📍 **{title}:**"
    # Accept either defs + current or pre-built views
    if isinstance(stages[0], PipelineStageView):
        views = list(stages)  # type: ignore[arg-type]
    else:
        views = lifecycle_payload(stages, current or stages[0].key)  # type: ignore[arg-type]

    flow_parts: list[str] = []
    current_hint = ""
    for v in views:
        if v.state == "current":
            flow_parts.append(f"**{v.label}**")
            current_hint = v.hint
        elif v.state == "complete":
            flow_parts.append(f"~~{v.label}~~")
        else:
            flow_parts.append(v.label)
    flow = " → ".join(flow_parts)
    if current_hint:
        return f"📍 **{title}:** {flow}  ·  *{current_hint}*"
    return f"📍 **{title}:** {flow}"


def render_discovery_lifecycle_diagram(current: str = "invent") -> str:
    return render_lifecycle_diagram(
        DISCOVERY_LADDER_STAGES,
        current,
        title="Discovery path",
    )


def format_lifecycle_table(
    stages: Sequence[PipelineStageDef] | Sequence[PipelineStageView],
    current: Optional[str] = None,
) -> str:
    """Markdown table: stage · hint · state · meaning (docs / console)."""
    if not stages:
        return ""
    if isinstance(stages[0], PipelineStageView):
        views = list(stages)  # type: ignore[arg-type]
    else:
        views = lifecycle_payload(stages, current or stages[0].key)  # type: ignore[arg-type]

    lines = [
        "| Stage | Hint | State | Meaning |",
        "|-------|------|-------|---------|",
    ]
    for v in views:
        mark = {"current": "● now", "complete": "✓", "upcoming": "○"}.get(v.state, v.state)
        meaning = (v.meaning or "").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| **{v.label}** | {v.hint} | {mark} | {meaning} |")
    return "\n".join(lines)


def lifecycle_as_dicts(
    stages: Sequence[PipelineStageView],
) -> list[dict[str, str]]:
    return [s.to_dict() for s in stages]


def discovery_mermaid(*, highlight: str = "invent") -> str:
    """Mermaid flowchart for docs (static diagram; highlight is comment-only)."""
    # highlight reserved for future styling; graph is the full path
    _ = highlight
    return """```mermaid
flowchart LR
  V[Host vocab] --> I[Invent]
  V --> E[Expand]
  I --> C[Scenario]
  E --> C
  C --> S[Script]
  S --> Z[Sealed]
  style I fill:#e0e7ff,stroke:#6366f1
  style E fill:#f1f5f9,stroke:#94a3b8
  style Z fill:#dcfce7,stroke:#16a34a
```"""


__all__ = [
    "AUTHORING_LADDER_STAGES",
    "DISCOVERY_LADDER_STAGES",
    "PipelineStageDef",
    "PipelineStageView",
    "authoring_lifecycle_payload",
    "discovery_lifecycle_payload",
    "discovery_mermaid",
    "format_lifecycle_table",
    "lifecycle_as_dicts",
    "lifecycle_payload",
    "render_discovery_lifecycle_diagram",
    "render_lifecycle_diagram",
]
