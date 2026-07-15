"""LLM **proposes** new exclusive surfaces / pre-decide stealers; code **backs**.

Split (AGENTS-shaped)
---------------------
* **LLM:** invent candidate geometry tokens + short rationale (constrained JSON).
* **Code laws:** viability against control-plane geometry rules.
* **Code physics:** would a real user likely be able to do this act on that surface?
* **Host:** injects ``llm_complete(prompt) -> str``, or use
  ``CONJECTURE_INVENT_LLM_*`` env (OpenAI-compatible). Portable package never
  imports a product LLM factory.

Never sole-arbitrates product NL meaning. Proposals do not auto-route chat.
Accepted proposals feed inventive geometry (``invent_all``) after merge into vocab.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Optional, Sequence

from conjecture_behaviour_runner.candidate_author.models import HostVocabulary

# Closed law vocabulary (portable) — host may extend via allow_extra_failure_classes
KNOWN_FAILURE_SLUGS: frozenset[str] = frozenset({
    "missing_sole_continue",
    "delivery_order_gap",
    "packaging_too_wide",
    "missing_state_leaf",
    "pin_without_open",
    "hollow_async_advance",
    "true_glossary_detour",
    "compound_primary_secondary",
})

KNOWN_TYPED_ACTS: frozenset[str] = frozenset({
    "typed_label",
    "ordinal",
    "chip_send_text",
})

# Surfaces that imply a finite card was shown (physics: user saw options)
SURFACE_KIND_HINTS: frozenset[str] = frozenset({
    "picker", "gate", "fork", "list", "menu", "chip", "card", "confirm",
    "strengtheners", "setup", "proposal",
})

# Stealers that are plausible pre-decide / early delivery leaves
STEALER_KIND_HINTS: frozenset[str] = frozenset({
    "inventory", "soft_name", "name_resolve", "glossary", "concept",
    "referential", "orientation", "discovery", "greenfield", "outcome",
    "value", "list", "marketplace", "workspace",
})

_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


@dataclass(frozen=True)
class GeometryProposal:
    kind: str  # surface | stealer
    id: str
    label: str
    rationale: str
    user_can_reach: str
    typed_acts: tuple[str, ...]
    failure_slug: str
    confidence: float
    source: str = "llm"


@dataclass(frozen=True)
class ProposalVerdict:
    proposal: GeometryProposal
    accepted: bool
    reasons: tuple[str, ...]  # law/physics failures or accept notes
    layer: str  # law | physics | accept


@dataclass
class ProposeResult:
    raw_proposals: list[GeometryProposal] = field(default_factory=list)
    verdicts: list[ProposalVerdict] = field(default_factory=list)

    @property
    def accepted(self) -> list[GeometryProposal]:
        return [v.proposal for v in self.verdicts if v.accepted]

    @property
    def rejected(self) -> list[ProposalVerdict]:
        return [v for v in self.verdicts if not v.accepted]

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": [asdict(p) for p in self.accepted],
            "rejected": [
                {
                    "proposal": asdict(v.proposal),
                    "reasons": list(v.reasons),
                    "layer": v.layer,
                }
                for v in self.rejected
            ],
        }


def _extract_json(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def parse_proposals(raw: str) -> list[GeometryProposal]:
    data = _extract_json(raw)
    if not data:
        return []
    rows = data.get("proposals")
    if not isinstance(rows, list):
        return []
    out: list[GeometryProposal] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        kind = str(row.get("kind") or "").strip().lower()
        pid = str(row.get("id") or "").strip().lower()
        acts_raw = row.get("typed_acts") or []
        acts: list[str] = []
        if isinstance(acts_raw, list):
            for a in acts_raw:
                s = str(a or "").strip().lower()
                if s:
                    acts.append(s)
        try:
            conf = float(row.get("confidence", 0.5))
        except (TypeError, ValueError):
            conf = 0.5
        conf = max(0.0, min(1.0, conf))
        out.append(
            GeometryProposal(
                kind=kind,
                id=pid,
                label=str(row.get("label") or pid)[:120],
                rationale=str(row.get("rationale") or "")[:400],
                user_can_reach=str(row.get("user_can_reach") or "")[:400],
                typed_acts=tuple(acts),
                failure_slug=str(row.get("failure_slug") or "").strip().lower(),
                confidence=conf,
            ),
        )
    return out


def check_laws(
    proposal: GeometryProposal,
    vocab: HostVocabulary,
    *,
    extra_failure_slugs: frozenset[str] | None = None,
) -> tuple[bool, list[str]]:
    """Code-owned law backcheck (viability)."""
    reasons: list[str] = []
    known_s = set(vocab.exclusive_owner_surfaces or ())
    known_t = set(vocab.pre_decide_stealing_leaves or ())
    slugs = set(KNOWN_FAILURE_SLUGS) | set(extra_failure_slugs or ())

    if proposal.kind not in ("surface", "stealer"):
        reasons.append("kind must be surface|stealer")
    if not _ID_RE.match(proposal.id or ""):
        reasons.append("id must be snake_case 2–64 chars")
    if proposal.id in known_s or proposal.id in known_t:
        reasons.append("id already in host vocabulary (not novel)")
    if proposal.kind == "surface" and proposal.id in known_t:
        reasons.append("surface id collides with known stealer")
    if proposal.kind == "stealer" and proposal.id in known_s:
        reasons.append("stealer id collides with known surface")
    if proposal.kind == "stealer":
        if proposal.failure_slug and proposal.failure_slug not in slugs:
            reasons.append(f"unknown failure_slug={proposal.failure_slug}")
        if not proposal.failure_slug:
            reasons.append("stealer requires failure_slug")
    for act in proposal.typed_acts:
        if act not in KNOWN_TYPED_ACTS:
            reasons.append(f"unknown typed_act={act}")
    if proposal.confidence < 0.35:
        reasons.append("confidence too low (<0.35)")
    return (len(reasons) == 0, reasons)


def check_physics(proposal: GeometryProposal) -> tuple[bool, list[str]]:
    """Code-owned physics: would a user likely be able to do this?"""
    reasons: list[str] = []
    reach = (proposal.user_can_reach or "").strip().lower()
    if len(reach) < 12:
        reasons.append("user_can_reach too thin (need realistic prior step)")

    pid = proposal.id or ""
    # Surface physics: name/shape should look like an armed UI surface
    if proposal.kind == "surface":
        if not any(h in pid for h in SURFACE_KIND_HINTS):
            # allow if rationale mentions card/gate/list
            blob = f"{proposal.label} {proposal.rationale} {reach}".lower()
            if not any(h in blob for h in SURFACE_KIND_HINTS):
                reasons.append(
                    "surface physics: no card/gate/list/picker signal in id or reach",
                )
        if "ordinal" in proposal.typed_acts and not any(
            x in pid for x in ("list", "picker", "menu", "fork", "path")
        ):
            # ordinal without list-like surface is weak physics
            if "number" not in reach and "ordinal" not in reach and "list" not in reach:
                reasons.append(
                    "physics: ordinal act without list/numbered surface story",
                )

    if proposal.kind == "stealer":
        if not any(h in pid for h in STEALER_KIND_HINTS):
            blob = f"{proposal.label} {proposal.rationale} {reach}".lower()
            if not any(h in blob for h in STEALER_KIND_HINTS):
                reasons.append(
                    "stealer physics: no inventory/glossary/discovery/list signal",
                )

    # Fantasy / impossible simultaneity
    fantasy = (
        "teleport", "omniscient", "read mind", "all gates at once",
        "without ui", "no user action",
    )
    blob_all = f"{proposal.rationale} {reach}".lower()
    for f in fantasy:
        if f in blob_all:
            reasons.append(f"physics fantasy phrase: {f}")

    return (len(reasons) == 0, reasons)


def backcheck_proposal(
    proposal: GeometryProposal,
    vocab: HostVocabulary,
    *,
    extra_failure_slugs: frozenset[str] | None = None,
) -> ProposalVerdict:
    ok_law, law_reasons = check_laws(
        proposal, vocab, extra_failure_slugs=extra_failure_slugs,
    )
    if not ok_law:
        return ProposalVerdict(
            proposal=proposal,
            accepted=False,
            reasons=tuple(law_reasons),
            layer="law",
        )
    ok_phys, phys_reasons = check_physics(proposal)
    if not ok_phys:
        return ProposalVerdict(
            proposal=proposal,
            accepted=False,
            reasons=tuple(phys_reasons),
            layer="physics",
        )
    return ProposalVerdict(
        proposal=proposal,
        accepted=True,
        reasons=("passed law + physics backcheck",),
        layer="accept",
    )


def merge_proposals_into_vocab(
    vocab: HostVocabulary,
    accepted: Sequence[GeometryProposal],
) -> HostVocabulary:
    """Return a new HostVocabulary with accepted surface/stealer ids unioned."""
    surfaces = set(vocab.exclusive_owner_surfaces or ())
    stealers = set(vocab.pre_decide_stealing_leaves or ())
    acts = set(vocab.typed_reply_acts or ())
    for p in accepted:
        if p.kind == "surface":
            surfaces.add(p.id)
        elif p.kind == "stealer":
            stealers.add(p.id)
        for a in p.typed_acts:
            if a in KNOWN_TYPED_ACTS:
                acts.add(a)
    return HostVocabulary(
        sole_continue_kinds=vocab.sole_continue_kinds,
        kinds_suppress_surface=vocab.kinds_suppress_surface,
        foreign_capability_leaves=vocab.foreign_capability_leaves,
        foreign_library_leaves=vocab.foreign_library_leaves,
        kind_to_owner=dict(vocab.kind_to_owner or {}),
        hard_escape_intents=vocab.hard_escape_intents,
        soft_escape_intents=vocab.soft_escape_intents,
        exclusive_owner_surfaces=frozenset(surfaces),
        pre_decide_stealing_leaves=frozenset(stealers),
        typed_reply_acts=frozenset(acts) if acts else vocab.typed_reply_acts,
        sealed_exclusive_pairs=vocab.sealed_exclusive_pairs,
    )


def build_propose_user_prompt(
    vocab: HostVocabulary,
    *,
    max_proposals: int | None = None,
    extra_failure_slugs: frozenset[str] | None = None,
    prompt_path: str | None = None,
) -> str:
    """Render file-based system/user invent prompt with current vocab fill-ins.

    Prompt lives in ``prompts/geometry_propose.md`` (override via
    ``CONJECTURE_INVENT_PROMPT_PATH`` or ``prompt_path``).
    """
    from conjecture_behaviour_runner.candidate_author.invent_config import (
        load_geometry_propose_prompt,
        load_invent_config,
    )

    cfg = load_invent_config()
    n = max_proposals if max_proposals is not None else cfg.max_proposals
    return load_geometry_propose_prompt(
        path=prompt_path or cfg.prompt_path,
        max_proposals=n,
        surfaces=", ".join(sorted(vocab.exclusive_owner_surfaces or ())) or "(none)",
        stealers=", ".join(sorted(vocab.pre_decide_stealing_leaves or ())) or "(none)",
        acts=", ".join(sorted(vocab.typed_reply_acts or KNOWN_TYPED_ACTS)),
        slugs=", ".join(sorted(KNOWN_FAILURE_SLUGS | set(extra_failure_slugs or ()))),
    )


def propose_geometry(
    vocab: HostVocabulary,
    *,
    llm_complete: Callable[[str], str] | None = None,
    max_proposals: int | None = None,
    extra_failure_slugs: frozenset[str] | None = None,
    prompt_path: str | None = None,
    use_env_llm: bool = False,
) -> ProposeResult:
    """LLM proposes; code backchecks law + physics.

    * ``llm_complete`` — injected completer (host or test).
    * ``use_env_llm`` — build completer from ``CONJECTURE_INVENT_LLM_*`` env
      (public package; no product service keys).
    * ``max_proposals`` — default from ``CONJECTURE_INVENT_MAX_PROPOSALS`` (4).
    """
    from conjecture_behaviour_runner.candidate_author.invent_config import (
        load_invent_config,
        make_env_llm_complete,
    )

    cfg = load_invent_config()
    n = max_proposals if max_proposals is not None else cfg.max_proposals
    n = max(1, min(64, int(n)))

    complete = llm_complete
    if complete is None and use_env_llm:
        # System role stays short; full laws/physics live in the prompt file.
        complete = make_env_llm_complete(
            config=cfg,
            system_prompt=(
                "You propose multi-turn control-plane test geometry only. "
                "Follow the user prompt. Output compact JSON only."
            ),
        )
    if complete is None:
        return ProposeResult(
            raw_proposals=[],
            verdicts=[
                ProposalVerdict(
                    proposal=GeometryProposal(
                        kind="surface",
                        id="llm_not_configured",
                        label="llm_not_configured",
                        rationale="no llm_complete and use_env_llm false/unset",
                        user_can_reach="n/a",
                        typed_acts=(),
                        failure_slug="",
                        confidence=0.0,
                        source="llm",
                    ),
                    accepted=False,
                    reasons=(
                        "pass llm_complete=... or set CONJECTURE_INVENT_LLM_* "
                        "and use_env_llm=True",
                    ),
                    layer="law",
                ),
            ],
        )

    prompt = build_propose_user_prompt(
        vocab,
        max_proposals=n,
        extra_failure_slugs=extra_failure_slugs,
        prompt_path=prompt_path,
    )
    try:
        raw = complete(prompt)
    except Exception as exc:  # noqa: BLE001
        return ProposeResult(
            raw_proposals=[],
            verdicts=[
                ProposalVerdict(
                    proposal=GeometryProposal(
                        kind="surface",
                        id="llm_error",
                        label="llm_error",
                        rationale=str(exc)[:200],
                        user_can_reach="n/a",
                        typed_acts=(),
                        failure_slug="",
                        confidence=0.0,
                        source="llm",
                    ),
                    accepted=False,
                    reasons=(f"llm_complete failed: {exc}",),
                    layer="law",
                ),
            ],
        )

    proposals = parse_proposals(raw)[:n]
    # Dedupe by id
    seen: set[str] = set()
    uniq: list[GeometryProposal] = []
    for p in proposals:
        if p.id in seen:
            continue
        seen.add(p.id)
        uniq.append(p)

    verdicts = [
        backcheck_proposal(p, vocab, extra_failure_slugs=extra_failure_slugs)
        for p in uniq
    ]
    return ProposeResult(raw_proposals=uniq, verdicts=verdicts)


__all__ = [
    "GeometryProposal",
    "KNOWN_FAILURE_SLUGS",
    "KNOWN_TYPED_ACTS",
    "ProposalVerdict",
    "ProposeResult",
    "backcheck_proposal",
    "build_propose_user_prompt",
    "check_laws",
    "check_physics",
    "merge_proposals_into_vocab",
    "parse_proposals",
    "propose_geometry",
]
