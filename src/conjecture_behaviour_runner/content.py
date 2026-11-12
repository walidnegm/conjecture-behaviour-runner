"""Content invariants — grade WHAT an agent said, not only who said it.

The standard invariants (``invariants.py``) prove behaviour: which owner took the
turn, which task is open, which pin is bound. They pass a turn that lands in the
right place and says something wrong. Content invariants close that gap for
retrieval-backed answers, stage by stage, so a failure names the stage that broke:

=============  ==============================================  ===================
stage          question                                        checked by
=============  ==============================================  ===================
retrieve       Was the expected source among the candidates?   code (ids)
select         Did the selector pick an acceptable source,     code (ids)
               never a forbidden one — or abstain when told?
answer         Is the answer faithful to its sources and       an LLM judge
               relevant to the question?                       (``ContentJudge``)
=============  ==============================================  ===================

**Observation convention.** A host fills these keys in ``TurnObservation.extras``:

* ``question`` (str) — the user text the answer responds to
* ``answer`` (str) — what the agent said
* ``contexts`` (list[str]) — the passages the answer was built from
* ``retrieved_ids`` (list[str]) — candidate source ids, best first
* ``selected_id`` (str | None) — the source the selector chose (None = abstained)

**Golden cases.** ``GoldenCase`` is the fixture: an utterance with its expected
primary source, acceptable alternatives, forbidden sources, or an expected
abstention. ``case_script`` turns one into a one-turn ``ConjectureScript``;
``summarize`` aggregates a run into the three selection rates that matter —
Top-1, acceptable-hit and **forbidden-selection** (a confident wrong pick is the
dangerous failure, so it is reported on its own).

The judge is optional and pluggable. Deterministic kinds never call a model;
``judged_at_least`` fails closed when no judge is bound. See
``contrib.deepeval_judge`` for a DeepEval-backed judge.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional, Protocol, Sequence, runtime_checkable

from conjecture_behaviour_runner.protocol import TurnObservation
from conjecture_behaviour_runner.script import ConjectureScript, DialogueTurn, InvariantSpec

__all__ = [
    "CONTENT_INVARIANT_KINDS",
    "ContentJudge",
    "GoldenCase",
    "JudgeScore",
    "case_script",
    "check_content_invariant",
    "load_golden_cases",
    "summarize",
]

CONTENT_INVARIANT_KINDS: tuple[str, ...] = (
    "retrieved_includes",  # expected={"id": X, "k": N}: X in retrieved_ids[:N] (k optional)
    "retrieved_excludes",  # expected={"ids": [...], "k": N}: none of ids in retrieved_ids[:N]
    "selected_in",         # expected=[ids]: selected_id is one of them
    "selected_not_in",     # expected=[ids]: selected_id is none of them (abstain passes)
    "abstained",           # selected_id is None
    "judged_at_least",     # expected={"metric": name, "threshold": t}: judge score >= t
)


@dataclass(frozen=True)
class JudgeScore:
    """One judged metric: a score in [0, 1] and the judge's reason."""

    metric: str
    score: float
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"metric": self.metric, "score": self.score, "reason": self.reason}


@runtime_checkable
class ContentJudge(Protocol):
    """Scores an answer on a named metric. Implementations call a model."""

    def score(
        self,
        metric: str,
        *,
        question: str,
        answer: str,
        contexts: Sequence[str],
    ) -> JudgeScore:
        ...


def _ids(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


def check_content_invariant(
    observation: TurnObservation,
    spec: InvariantSpec,
    *,
    judge: Optional[ContentJudge] = None,
    scores: Optional[dict[str, JudgeScore]] = None,
) -> Optional[str]:
    """Return a failure message if the content invariant fails, else ``None``.

    ``scores`` (optional) collects every judged score, so a runner can report the
    number even when the threshold passes. Unknown kinds fail closed.
    """
    ex = observation.extras
    kind = spec.kind
    exp = spec.expected

    if kind in ("retrieved_includes", "retrieved_excludes"):
        if "retrieved_ids" not in ex:
            return f"{kind}: extras has no 'retrieved_ids' (host must report the candidates)"
        got = _ids(ex.get("retrieved_ids"))
        exp_map = exp if isinstance(exp, Mapping) else {"id": exp}
        k = exp_map.get("k")
        window = got[: int(k)] if k else got
        if kind == "retrieved_includes":
            want = str(exp_map.get("id"))
            if want in window:
                return None
            return f"retrieved_includes: {want!r} not in top {k or len(got)} {window!r}"
        bad = sorted(set(_ids(exp_map.get("ids"))) & set(window))
        if not bad:
            return None
        return f"retrieved_excludes: forbidden {bad!r} in top {k or len(got)} {window!r}"

    if kind in ("selected_in", "selected_not_in", "abstained"):
        if "selected_id" not in ex:
            return f"{kind}: extras has no 'selected_id' (None means abstained; missing means unknown)"
        sel = ex.get("selected_id")
        if kind == "abstained":
            return None if sel is None else f"abstained: expected no selection, got {sel!r}"
        allowed = _ids(exp)
        if kind == "selected_in":
            if sel is not None and str(sel) in allowed:
                return None
            return f"selected_in: selected {sel!r}, expected one of {allowed!r}"
        if sel is None or str(sel) not in allowed:
            return None
        return f"selected_not_in: selected forbidden {sel!r}"

    if kind == "judged_at_least":
        if judge is None:
            return "judged_at_least: no ContentJudge bound — refusing to pass unjudged"
        exp_map = dict(exp or {})
        metric = str(exp_map.get("metric") or "")
        threshold = float(exp_map.get("threshold", 0.5))
        answer = str(ex.get("answer") or "")
        if not answer.strip():
            return f"judged_at_least[{metric}]: empty answer"
        result = judge.score(
            metric,
            question=str(ex.get("question") or ""),
            answer=answer,
            contexts=[str(c) for c in (ex.get("contexts") or [])],
        )
        if scores is not None:
            scores[metric] = result
        # The harness copies extras into the run record after the checks, so every judged
        # score and reason reaches the artifact — pass or fail.
        observation.extras.setdefault("judged", {})[metric] = result.to_dict()
        if result.score >= threshold:
            return None
        return (
            f"judged_at_least[{metric}]: {result.score:.2f} < {threshold:.2f}"
            + (f" — {result.reason}" if result.reason else "")
        )

    return (
        f"unknown content invariant kind={kind!r} — content kinds: "
        f"{', '.join(CONTENT_INVARIANT_KINDS)}"
    )


@dataclass(frozen=True)
class GoldenCase:
    """A fixture: an utterance and where its answer must (and must not) come from.

    ``expect_abstain`` cases have no primary: the right behaviour is to decline.
    ``judged`` names the answer metrics to score and their thresholds.
    """

    case_id: str
    utterance: str
    primary: Optional[str] = None
    acceptable: tuple[str, ...] = ()
    forbidden: tuple[str, ...] = ()
    expect_abstain: bool = False
    retrieve_k: int = 5
    judged: Mapping[str, float] = field(default_factory=dict)
    note: str = ""

    def __post_init__(self) -> None:
        if self.expect_abstain and self.primary:
            raise ValueError(f"{self.case_id}: an abstention case has no primary")
        if not self.expect_abstain and not self.primary:
            raise ValueError(f"{self.case_id}: a case needs a primary or expect_abstain")
        clash = set(self.forbidden) & ({self.primary} | set(self.acceptable))
        if clash:
            raise ValueError(f"{self.case_id}: {sorted(clash)} both expected and forbidden")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GoldenCase":
        return cls(
            case_id=str(data["id"]),
            utterance=str(data["utterance"]),
            primary=data.get("primary"),
            acceptable=tuple(_ids(data.get("acceptable"))),
            forbidden=tuple(_ids(data.get("forbidden"))),
            expect_abstain=bool(data.get("expect_abstain", False)),
            retrieve_k=int(data.get("retrieve_k", 5)),
            judged=dict(data.get("judged") or {}),
            note=str(data.get("note") or ""),
        )


def load_golden_cases(rows: Iterable[Mapping[str, Any]]) -> list[GoldenCase]:
    cases = [GoldenCase.from_dict(r) for r in rows]
    seen: set[str] = set()
    for c in cases:
        if c.case_id in seen:
            raise ValueError(f"duplicate golden case id {c.case_id!r}")
        seen.add(c.case_id)
    return cases


def case_script(
    case: GoldenCase,
    *,
    stages: Sequence[str] = ("retrieve", "select", "answer"),
) -> ConjectureScript:
    """One golden case → a one-turn script carrying its content invariants."""
    inv: list[InvariantSpec] = []
    if case.expect_abstain:
        if "select" in stages:
            inv.append(InvariantSpec("abstained", reason="no source answers this"))
    else:
        if "retrieve" in stages:
            inv.append(InvariantSpec("retrieved_includes", {"id": case.primary, "k": case.retrieve_k}))
        if "select" in stages:
            inv.append(InvariantSpec("selected_in", [case.primary, *case.acceptable]))
        if "answer" in stages:
            for metric, threshold in case.judged.items():
                inv.append(InvariantSpec("judged_at_least", {"metric": metric, "threshold": threshold}))
    if case.forbidden and "select" in stages:
        inv.append(InvariantSpec("selected_not_in", list(case.forbidden),
                                 reason="a confident wrong pick is the dangerous failure"))
    return ConjectureScript(
        script_id=f"content:{case.case_id}",
        description=case.note or case.utterance,
        conversation_id=f"content-{case.case_id}",
        tags=("content",),
        turns=[DialogueTurn(user_text=case.utterance, invariants=inv)],
    )


def summarize(
    cases: Sequence[GoldenCase],
    selected: Mapping[str, Optional[str]],
) -> dict[str, Any]:
    """Selection rates over a run. ``selected`` maps case_id → selected id (None = abstained).

    * ``top1`` — the primary was selected (answerable cases)
    * ``acceptable_hit`` — the primary or an acceptable source was selected
    * ``forbidden_selection`` — a forbidden source was selected (all cases with any)
    * ``abstention_correct`` — abstained when told to (abstention cases)
    """
    answerable = [c for c in cases if not c.expect_abstain and c.case_id in selected]
    abstain = [c for c in cases if c.expect_abstain and c.case_id in selected]
    with_forbidden = [c for c in cases if c.forbidden and c.case_id in selected]

    def rate(n: int, d: int) -> Optional[float]:
        return round(n / d, 4) if d else None

    top1 = sum(1 for c in answerable if selected[c.case_id] == c.primary)
    acc = sum(1 for c in answerable if selected[c.case_id] in {c.primary, *c.acceptable})
    forb = [c.case_id for c in with_forbidden if selected[c.case_id] in set(c.forbidden)]
    abst = sum(1 for c in abstain if selected[c.case_id] is None)
    return {
        "cases": len(selected),
        "top1": rate(top1, len(answerable)),
        "acceptable_hit": rate(acc, len(answerable)),
        "forbidden_selection": rate(len(forb), len(with_forbidden)),
        "forbidden_cases": forb,
        "abstention_correct": rate(abst, len(abstain)),
    }
