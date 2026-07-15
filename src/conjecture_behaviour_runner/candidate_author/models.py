"""Portable candidate-path models (host vocabulary stays outside this package).

Host supplies kinds, competing leaves, incidents, matrix cells.
Engine emits CandidatePath → Conjecture Scenario YAML (precursor to Script).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Mapping, Optional, Sequence

Priority = Literal["high", "medium", "low"]
SealStatus = Literal["open", "partial", "sealed", "regression_check"]
Source = Literal[
    "host_incident",
    "sole_continue_x_foreign",
    "matrix_queue",
    "residual",
    "residual_heuristic",  # host alias
    "invention",  # geometry invent (not cross-product expand)
    "example",
]


@dataclass(frozen=True)
class HostVocabulary:
    """Host-declared multi-turn kinds and competing surface leaves.

    All strings are **host vocabulary** — not a Conjecture catalog.
    """

    sole_continue_kinds: frozenset[str]
    """Ledger kinds that own continue until escape."""

    kinds_suppress_surface: frozenset[str]
    """Kinds that should suppress foreign surface classifiers mid-flight."""

    foreign_capability_leaves: frozenset[str]
    """Competing multi-turn starts (read_kind / capability labels)."""

    foreign_library_leaves: frozenset[str] = frozenset()
    """Inventory/list/open leaves that steal mid sole-continue on continue."""

    kind_to_owner: Mapping[str, str] = field(default_factory=dict)
    """Optional map kind → exclusive_owner id (defaults to kind)."""

    hard_escape_intents: frozenset[str] = frozenset(
        {"new_task", "abandon", "handoff"},
    )
    """Escape that may start a foreign capability."""

    soft_escape_intents: frozenset[str] = frozenset(
        {"detour", "new_task", "abandon", "handoff"},
    )
    """Escape for library leaves (detour allowed)."""

    # --- Invention geometry (not sole-continue expansion) ---
    exclusive_owner_surfaces: frozenset[str] = frozenset()
    """Armed finite surfaces that must exclusive-own the next free-text reply
    (domain_picker, path_picker, ir_gate, cost_fork, armed_list, …)."""

    pre_decide_stealing_leaves: frozenset[str] = frozenset()
    """Pre-decide / early leaves that steal when exclusive surface is armed
    (inventory_soft_name, inventory_name_resolve, glossary, referential_list, …)."""

    typed_reply_acts: frozenset[str] = frozenset(
        {"typed_label", "ordinal", "chip_send_text"},
    )
    """How the user replies without a perfect chip click."""

    sealed_exclusive_pairs: frozenset[str] = frozenset()
    """Pairs already sealed as ``surface|stealer`` — invention skips or marks
    regression_check (e.g. ``domain_picker|inventory_soft_name``)."""

    def owner_for(self, kind: str) -> str:
        k = (kind or "").strip()
        if not k:
            return "default"
        return str(self.kind_to_owner.get(k) or k)

    def pair_key(self, surface: str, stealer: str) -> str:
        return f"{(surface or '').strip()}|{(stealer or '').strip()}"


@dataclass(frozen=True)
class HostIncident:
    """One sealed or open host incident (optional seed for candidates)."""

    incident_id: str
    failure_class_slug: str
    symptom: str
    exclusive_owner_should_win: str
    fix_artifact: str = ""
    ratchet_module: str = ""
    status: Literal["sealed", "open", "ok_glossary"] = "sealed"


@dataclass(frozen=True)
class MatrixCell:
    """One finite-expansion cell (host matrix or portable example)."""

    cell_id: str
    mode_slug: str
    failure_mode: str
    kind: str
    phase: str
    pin: str
    move: str
    status: str  # sealed | seed_pending | gap | host_only | n/a
    note: str = ""
    probe_utterance: str = ""


@dataclass(frozen=True)
class ResidualProbe:
    """Hand-authored high-value residual (host-specific or template)."""

    path_id: str
    title: str
    failure_class_slug: str
    start_state: Mapping[str, str]
    turns: Sequence[str]
    must_hold: Sequence[str]
    must_not: Sequence[str]
    priority: Priority = "high"
    seal_status: SealStatus = "open"
    proof_pointer: str = ""
    notes: str = ""
    pin_hints: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CandidatePath:
    """One authored stress path — precursor to Scenario YAML."""

    path_id: str
    source: Source
    priority: Priority
    failure_class: str
    title: str
    start_state: dict[str, str]
    turns: tuple[str, ...]
    must_hold: tuple[str, ...]
    must_not: tuple[str, ...]
    seal_status: SealStatus
    proof_pointer: str = ""
    notes: str = ""
    pin_hints: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["turns"] = list(self.turns)
        d["must_hold"] = list(self.must_hold)
        d["must_not"] = list(self.must_not)
        return d


def blocks_foreign_leaf(
    vocab: HostVocabulary,
    *,
    active_kind: str,
    leaf: str,
    task_intent: str = "continue",
) -> bool:
    """Portable sole-continue vs foreign leaf gate (host supplies sets)."""
    kind = (active_kind or "").strip()
    rk = (leaf or "").strip().lower()
    if not kind or kind not in vocab.sole_continue_kinds:
        return False
    if not rk or rk == "none":
        return False
    intent = (task_intent or "continue").strip().lower()
    # Same-stream restart: block unless hard escape
    if rk == kind or vocab.kind_to_owner.get(kind) == rk:
        return intent not in vocab.hard_escape_intents
    if rk in vocab.foreign_capability_leaves:
        return intent not in vocab.hard_escape_intents
    if rk in vocab.foreign_library_leaves:
        return intent not in vocab.soft_escape_intents
    return False


__all__ = [
    "CandidatePath",
    "HostIncident",
    "HostVocabulary",
    "MatrixCell",
    "Priority",
    "ResidualProbe",
    "SealStatus",
    "Source",
    "blocks_foreign_leaf",
]
