# Conversational Authority Quality (CAQ-FM)

## Why you are here

Multi-turn AI agents fail not only by writing a bad sentence. They also fail when
**state law** breaks under a reply that still *sounds* successful: the wrong specialist
keeps talking, the wrong customer or ticket is “current,” mid-flight work restarts, or a
claimed success opens nothing the user can act on.

Demos and chat transcripts can look fine. LLM-as-judge often scores the prose. Ordinary
tests may only check that *something* returned. The machine underneath — **who owns the
turn, which record is active, when ownership may yield** — can still be wrong.

**This document** is the conceptual home for that problem and how Conjecture addresses it.

| Piece | Role |
|-------|------|
| **CAQ-FM** | Named failure modes (the map): wrong owner, pin drop, illegal restart, hollow open, … |
| **Conjecture** | Multi-turn scripts that **PASS** when enforcement holds and **FAIL** when it is soft |
| **Doctrine** | **LLM proposes · code enforces** |
| **Memory** | **Failure → Law → Proof** so a class cannot silently return |

Install and demos: [README](../README.md). Mode map: [CATALOG.md](../incidents/CATALOG.md).
Stage and seed battery: [MATURITY.md](./MATURITY.md).

**“Authority” ≠ IAM.** Here it means conversation and workflow authority: who may act,
which record stays active (pinned), when control may yield, and what must open after a
claimed success.

---

## Doctrine

**LLM proposes · code enforces.**

| Side | Responsibility |
|------|----------------|
| **LLM** | Irregular language; labels such as continue, detour, new task, abandon |
| **Code** | Exclusive owner, active record pin, yield/handoff, that delivery actually opens |

If enforcement fails open (**soft enforcement**), the model can steal or hijack the path
and still sound helpful. Conjecture regression-tests the **enforce half** under **pinned
cognition** (labels fixed for CI — not a live model roll). It does not prove the
classifier picked the right label; pair with separate cognition evals. Green enforce +
wrong live labels is still a bad product.

**Failure → Law → Proof**

1. **Failure** — what the user experienced  
2. **Law** — what must always hold after the turn  
3. **Proof** — a script that **FAIL**s without the fix and **PASS**es with it  

No law → not sealed. No FAIL/PASS pair → not sealed. Prefer structural ownership when
authority is load-bearing; proofs catch what structure missed.

### Same ideas in plain systems terms

Skeptical readers often reduce this correctly:

| Our phrasing | Familiar systems idea |
|--------------|------------------------|
| Who owns the turn? | Exclusive owner / mutex for the active workflow |
| Which record stays active? | Stable foreign key / entity pin |
| When may ownership yield? | Lock-release / handoff condition |
| Failure → Law → Proof | Bug → invariant → regression test |
| LLM proposes · code enforces | Nondeterministic text must not mutate critical state without validation |

We are **not** claiming to invent locks, foreign keys, or regression tests.

What is under-tested in multi-turn LLM products is the **failure class**: free-form
routing fail-opens into a helpful path (glossary, FAQ, another specialist), the **prose
looks fine**, and owner / active record / handoff were never checked. Chat evals score
sentences. Conjecture standardizes **post-turn state asserts**, **intentional handoff vs
informational detour**, and **planted soft-enforcement must FAIL**.

One-line product truth:

> After every turn, assert that the correct owner and active record remain intact.
> Test intentional handoffs separately from informational detours. Plant a steal and
> require the suite to catch it.

---

## Worked example (end-to-end)

**Conversation**

1. Claims Agent owns the thread mid-flight. Active record: claim **C-1042**.  
2. User: *“Continue — but what does deductible mean?”*  
3. Glossary answers helpfully. The definition is correct.  
4. Fail-open routing **overwrites** exclusive owner (or clears `claim_id`) — not a coup,
   an orchestration bug.  
5. A human reading the chat: “Nice explanation.” Business continuity is already wrong.

**Law**

> A definitional detour must not transfer exclusive ownership or clear the active claim.
> After the turn: owner remains claims, pin remains C-1042.

**Pinned cognition (CI)**

```text
turn N label = continue   # or detour-with-return — fixed for the run, not re-sampled
```

**Observation after Act (healthy)**

```text
exclusive_owner: "claims"
pins: { claim_id: "C-1042" }
```

**Proof**

| Path | Expected |
|------|----------|
| Healthy (detour answers; owner + pin held) | **PASS** |
| Planted bug (owner overwritten / pin cleared) | **FAIL** |

Helpful prose, broken state, regression that catches the overwrite.

---

## How Conjecture works

### Script

Multi-turn user text + **expected post-turn state** (your vocabulary):

```text
turn 1  user: "start claims work on C-1042"
        expect: exclusive_owner = claims, pins.claim_id = C-1042

turn 2  user: "continue — what does deductible mean?"
        expect: exclusive_owner still claims, pins.claim_id still C-1042
```

Kinds and pin keys are **yours** (claims / claim_id here; mini-app demos use `cost_out` /
`workflow_id` only as dogfood).

### Pinned cognition

Labels are **fixed** for the run. Question under test: *given this label, did code keep
owner · pin · handoff law?* — not *did the model pick the right label?*

### Driver → Act → Observation

1. **Driver** runs your real turn path (in-process, HTTP, LangGraph, Temporal, …).  
2. Project host state into an **Observation**:

```text
Observation
  exclusive_owner: "…"     # your kind / idle / front door
  pins: { … }              # active record map your host freezes
  # optional delivery / open-surface signals
```

### Invariants

| Check | Example fail |
|-------|----------------|
| Owner held | continue stole to another specialist / front door |
| Active record held | pin null or switched id |
| No illegal restart | mid-flight work wiped |
| Handoff law | yield only when rules allow |
| Open surface | “success” with empty delivery |

### Planted-failure discipline

| Implementation | Verdict |
|----------------|---------|
| Healthy enforcement | **PASS** |
| Soft enforcement (planted steal / pin drop / restart) | **FAIL** |

If the planted bug still PASSes, the check is decoration.

```text
  script → pinned labels → Driver.Act → Observation → invariants
                              healthy PASS · planted FAIL
```

Mini-app demos: [README](../README.md) (`conjecture path-faithful --prove-bugs`).

---

## Why not just pytest?

You *can* assert `exclusive_owner` and pins in pytest, Cucumber, LangSmith, or an
internal harness. See also the plain-systems table above: this is control state, not a
new CS primitive.

Conjecture **standardizes the discipline** so the same shape can be shared, reviewed,
and promoted:

| Convention | What you get |
|------------|----------------|
| Multi-turn **script** structure | Expected state after *each* turn, not a single endpoint check |
| **Observation** contract | Portable owner · pins · outcome fields after Act |
| **Pinned cognition** | Enforce tests isolated from live classifier drift |
| **Planted-failure** evidence | Healthy PASS + intentional soft FAIL required to trust a law |
| **Incident taxonomy** (CAQ-FM) | Shared names for steal, pin drop, hollow open, … |
| **Seed packaging** | Promote a host law into a reusable `patterns/` proof when it generalizes |
| **Drivers** | Same script shape over mini-app, HTTP, or host adapters |

If you only need the ideas, steal **LLM proposes · code enforces** and
**Failure → Law → Proof** without the package. Adopt Conjecture when you want that
discipline as a **shared, reviewable artifact** — not another one-off assert in a private
test file.

---

## What “portable” means

**Portable** = the **law + conversation shape + Observation expectations + planted-failure
pattern** can travel across hosts and vendors.

**Not portable / always host-specific:**

- projecting proprietary session/graph/workflow state into Observation  
- Driver / adapter wiring  
- many production laws that stay **host_only** (product secrets, substrate, UI)

So: portable is **not** integration-free. You still pay projection and driver cost; you
reuse the *proof shape* and, when a law is general, a public seed.

---

## Fit (once)

Pays rent when **state is load-bearing**: exclusive owners, real records, pins, handoffs.
Free-form single-turn Q&A without that shape does not need the machinery. Adoption cost
is real (scripts, projection, drivers, catalog). Prefer **one** sealed law on your path
over a large aspirational catalog. Battery size and stage: [MATURITY.md](./MATURITY.md)
(~**six** runnable public seeds today; map is broader — see [CATALOG](../incidents/CATALOG.md)).

---

## Cost, AI grind, and ownership

**Adoption cost is real.** Many teams correctly decline if authority failures are rare.

### AI can grind the tax

| Task | Role |
|------|------|
| Script drafts from soak logs | Propose turns + expected owner/pins |
| Planted variants | Soft-enforcement mutants (steal owner, drop pin, restart) |
| Projection stubs | Keep Observation mapping current when schema drifts |
| Catalog hygiene | Suggest mode id / seed promotion after real FAIL/PASS |

### AI must not silently own

| Risk | Guard |
|------|--------|
| Wrong law accepted | Human (or high-bar) sign-off on the invariant |
| Flaky suite | Drafts only; pinned goldens + deterministic Driver in CI |
| Auto-merge without proof | Require planted FAIL and healthy PASS |
| Recursive drift | Maintainer agent **proposes**; code + acceptance **own** CI |

### When someone else builds the agent

Implementers (SI, vendor, AI) may write scripts, projections, and drivers. Whoever is
accountable for outcomes **accepts** the laws and retains the PASS/FAIL evidence after
handoff — the builder should not self-certify against weak criteria.

---

## Terms

| Term | Meaning |
|------|---------|
| **Pinned cognition** | Labels fixed for the CI run |
| **Observation** | Post-turn owner · pins · outcome projection |
| **Soft enforcement** | Code fails open so the model can steal while sounding helpful |
| **Seed** | Portable script + planted-failure proof under `patterns/` |
| **CAQ-FM** | Named modes + laws + proofs for this failure class |

---

## Links

| Doc | Role |
|-----|------|
| [README](../README.md) | Install, planted-bug demos, drivers |
| [CATALOG](../incidents/CATALOG.md) | Full mode list + status |
| [registry.yaml](../incidents/registry.yaml) | Machine mode list (`id` ↔ seed) |
| [MATURITY.md](./MATURITY.md) | Stage / battery / known gaps |
| [SPEC](./SPEC.md) | Normative package contract |
| [incidents/README](../incidents/README.md) | Classify → land a seed |

---

## One sentence

Pin the labels, project an Observation, require **PASS** on healthy and **FAIL** on
planted soft enforcement — so fluent chat cannot hide broken owner · pin · handoff law.
