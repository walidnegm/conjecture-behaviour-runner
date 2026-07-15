"""Inventive candidate author — failure **geometry**, not expand-only cross-product.

Expansive mode (``paths_from_sole_continue_x_foreign``)
-------------------------------------------------------
Multiplies known axes: kind × foreign leaf. High volume, low novelty. Misses
polarities and fine phases (e.g. domain_picker armed + typed label vs
inventory soft-name).

Inventive mode (this module)
----------------------------
Starts from **exclusive-owner geometry**:

* An **armed surface** must own the next free-text reply.
* A **pre-decide stealer** may claim that free text if not suppressed.
* A **typed reply act** is how users answer without perfect chips.

Invention rule (code-seed, no LLM, no product routing)::

    for surface in exclusive_owner_surfaces:
      for stealer in pre_decide_stealing_leaves:
        for act in typed_reply_acts:
          invent: "when {surface} armed, {act} must not yield to {stealer}"

That is how we invent candidates the expansive product never names — including
conv_5e398f46 class **before** the next live miss — when the host declares
surfaces and stealers.

Host still supplies vocabulary; engine never imports product agents.
"""
from __future__ import annotations

from typing import Optional, Sequence

from conjecture_behaviour_runner.candidate_author.models import (
    CandidatePath,
    HostVocabulary,
    SealStatus,
)

# Probe sketches — geometry labels, not NL laundry for runtime routing.
_ACT_PROBES: dict[str, str] = {
    "typed_label": "User types the option label (not a chip click)",
    "ordinal": "User types a list number for the armed card",
    "chip_send_text": "User pastes the chip send_text string as free chat",
}

_STEALER_FAILURE: dict[str, str] = {
    "inventory_soft_name": "delivery_order_gap",
    "inventory_name_resolve": "delivery_order_gap",
    "glossary_concept": "packaging_too_wide",
    "referential_list": "delivery_order_gap",
    "orientation_status": "missing_state_leaf",
    "discovery_greenfield": "missing_sole_continue",
    "outcome_value_setup": "missing_sole_continue",
}


def invent_exclusive_owner_conflicts(
    vocab: HostVocabulary,
    *,
    limit: Optional[int] = None,
) -> list[CandidatePath]:
    """Invent exclusive-surface vs pre-decide-stealer candidates.

    Skips empty geometry (host must declare surfaces + stealers).
    """
    surfaces = sorted(vocab.exclusive_owner_surfaces or ())
    stealers = sorted(vocab.pre_decide_stealing_leaves or ())
    acts = sorted(vocab.typed_reply_acts or ())
    if not surfaces or not stealers or not acts:
        return []

    sealed = vocab.sealed_exclusive_pairs or frozenset()
    out: list[CandidatePath] = []
    for surface in surfaces:
        owner = surface  # exclusive owner id ≈ surface id
        for stealer in stealers:
            pair = vocab.pair_key(surface, stealer)
            already = pair in sealed
            for act in acts:
                probe = _ACT_PROBES.get(act, f"User performs {act}")
                fc = _STEALER_FAILURE.get(stealer, "delivery_order_gap")
                seal: SealStatus = "regression_check" if already else "open"
                pri = "medium" if already else "high"
                out.append(
                    CandidatePath(
                        path_id=f"invent.exclusive.{surface}.{act}.{stealer}",
                        source="invention",
                        priority=pri,  # type: ignore[arg-type]
                        failure_class=fc,
                        title=(
                            f"INVENT: armed `{surface}` + {act} must not yield "
                            f"to `{stealer}`"
                        ),
                        start_state={
                            "exclusive_surface": surface,
                            "armed": "true",
                            "typed_act": act,
                            "competing_leaf": stealer,
                        },
                        turns=(
                            f"(setup) Arm exclusive surface={surface} "
                            f"(finite card / gate open)",
                            f"(probe) {probe} while {surface} still owns the turn",
                        ),
                        must_hold=(
                            f"exclusive_owner≈{owner}",
                            f"{surface} binds reply or re-prompts — not {stealer}",
                        ),
                        must_not=(
                            f"{stealer} wins delivery",
                            "context loss / freeform derout of armed pick",
                        ),
                        seal_status=seal,
                        proof_pointer=(
                            f"sealed pair {pair}"
                            if already
                            else "UNINVENTED seal — host exclusive gate missing"
                        ),
                        notes=(
                            "Inventive geometry (exclusive surface × typed act × "
                            "pre-decide stealer). Not sole-continue×foreign expand."
                        ),
                        pin_hints={
                            "task_intent": "continue",
                            "exclusive_surface": surface,
                            "typed_act": act,
                            "stealer": stealer,
                        },
                    ),
                )
    # Prefer open inventions first (already sorted by author_candidates)
    if limit is not None and limit >= 0:
        return out[:limit]
    return out


def invent_polarity_flips_from_seals(
    vocab: HostVocabulary,
) -> list[CandidatePath]:
    """When A exclusive-beats B is sealed, invent B-armed must-beat A (if both declared).

    Example: inventory exclusive when list armed → invent domain_picker armed
    must beat inventory (conv_5e398f46 class) when both are in host geometry.
    """
    sealed = vocab.sealed_exclusive_pairs or frozenset()
    surfaces = vocab.exclusive_owner_surfaces or frozenset()
    stealers = vocab.pre_decide_stealing_leaves or frozenset()
    out: list[CandidatePath] = []
    for pair in sorted(sealed):
        if "|" not in pair:
            continue
        a, b = pair.split("|", 1)
        a, b = a.strip(), b.strip()
        # Flip: if A beat B, invent when B is the exclusive surface and A steals
        if b in surfaces and a in stealers:
            flip = vocab.pair_key(b, a)
            if flip in sealed:
                continue
            out.append(
                CandidatePath(
                    path_id=f"invent.polarity.{b}.vs.{a}",
                    source="invention",
                    priority="high",
                    failure_class="delivery_order_gap",
                    title=(
                        f"INVENT polarity: `{b}` armed must beat stealer `{a}` "
                        f"(flip of sealed {pair})"
                    ),
                    start_state={
                        "exclusive_surface": b,
                        "armed": "true",
                        "competing_leaf": a,
                        "polarity_of": pair,
                    },
                    turns=(
                        f"(setup) Arm exclusive surface={b}",
                        f"(probe) Free-text that {a} would claim when cold",
                    ),
                    must_hold=(f"exclusive_owner≈{b}",),
                    must_not=(f"{a} steals while {b} armed",),
                    seal_status="open",
                    proof_pointer=f"polarity invent from sealed {pair}",
                    notes="Polarity flip invention — seals one direction, invent the other.",
                    pin_hints={
                        "task_intent": "continue",
                        "exclusive_surface": b,
                        "stealer": a,
                    },
                ),
            )
    return out


def invent_all(
    vocab: HostVocabulary,
    *,
    include_polarity: bool = True,
    limit: Optional[int] = None,
) -> list[CandidatePath]:
    """Invent exclusive-geometry candidates.

    ``limit`` caps how many inventive scenarios are returned for one author
    turn. Default: ``CONJECTURE_INVENT_MAX_SCENARIOS`` (4). Prefer **open**
    (unsealed) inventions first so a small budget surfaces novel gaps.
    """
    from conjecture_behaviour_runner.candidate_author.invent_config import (
        load_invent_config,
    )

    paths = invent_exclusive_owner_conflicts(vocab)
    if include_polarity:
        paths.extend(invent_polarity_flips_from_seals(vocab))
    # Dedupe by path_id
    seen: set[str] = set()
    uniq: list[CandidatePath] = []
    for p in paths:
        if p.path_id in seen:
            continue
        seen.add(p.path_id)
        uniq.append(p)

    # Open / unsealed first so max_scenarios budget is inventive, not regression
    seal_rank = {"open": 0, "partial": 1, "sealed": 2, "regression_check": 3}
    uniq.sort(key=lambda p: (seal_rank.get(p.seal_status, 9), p.path_id))

    if limit is None:
        limit = load_invent_config().max_scenarios
    if limit is not None and limit >= 0:
        return uniq[: int(limit)]
    return uniq


__all__ = [
    "invent_all",
    "invent_exclusive_owner_conflicts",
    "invent_polarity_flips_from_seals",
]
