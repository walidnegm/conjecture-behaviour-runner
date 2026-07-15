# Conversational Authority Quality (CAQ-FM)

## Why you are here

Multi-turn agents don’t only fail by writing a bad answer. They fail when the reply
looks right and **state law** underneath is wrong: wrong owner, wrong active record,
illegal restart, hollow “done.”

**Applies to** agentic / LLM products with **durable workflows, real records, and real
handoffs**—claims, tickets, cases, multi-step operations. Free-form Q&A often does not
need this machinery.

**What conversational authority regression must provide:**

- a shared multi-turn script shape  
- a portable post-turn Observation  
- deterministic enforcement tests with fixed labels  
- separate router and enforcement evaluation  
- a healthy-PASS / planted-FAIL discipline  
- a named taxonomy of authority failures  
- discoverability of hard multi-turn paths  
- trajectory invention that plausibly creates edge conditions (then human-accepted laws)  

| Piece | Role |
|-------|------|
| **CAQ-FM** | Named failure modes (the map) |
| **Conjecture** | Runs the proofs: PASS healthy · FAIL planted soft enforcement |
| **Doctrine** | **LLM proposes · policy validates · code commits** |
| **Memory** | **Failure → Law → Proof** |

Install: [README](../README.md) · Modes: [CATALOG](../incidents/CATALOG.md) · Stage:
[MATURITY](./MATURITY.md). **“Authority” ≠ IAM** — who may act, which record stays
active, when ownership may yield, whether claimed success produced the promised effect.

### Working taxonomy (not FMEA reinvention)

We use a small layered map so discovery, classification, and validation stay consistent.
This is **not** a full FMEA product — only enough structure to connect failure laws,
observed incidents, candidate trajectories, executable tests, and evidence.

| Layer | What it is | Example |
|-------|------------|---------|
| **Failure mode** (`id` / **slug**) | Named class of prohibited/incorrect behavior in CAQ-FM / `registry.yaml`. Slug = Conjecture’s unique id for the *class*, not one occurrence. | `owner_steal`, `hollow_open`, `packaging_steal` |
| **Incident** | One observed production, soak, eval, or test occurrence of a mode. Many incidents → one mode. | “Glossary stole ownership mid-claim on C-1042 on 2026-07-01.” |
| **Candidate scenario** | One authored multi-turn trajectory that can expose or stress a mode. Inventory rows are trajectories, not modes. Many scenarios → one mode. | `invent_…_glossary_concept`, `matrix.hollow_open.…` |
| **Script / sealed pattern** | Deterministic CI-runnable form of a scenario (setup, turns, asserts). Linked via `patterns/<portable_seed>/` and registry `portable_seed`. | `patterns/owner_steal_mid_continue/` |
| **Execution evidence** | Trace, assertions, artifacts, and verdict from running a sealed pattern — proof the law held or broke under that trajectory. | Trace: claims stayed authoritative; C-1042 stayed pinned. |

**Core relationships** (not strictly 1:1): mode = reusable class · incident = occurrence ·
scenario = trajectory · sealed pattern = repeatable test · evidence = run verdict.
Many incidents/scenarios → one mode; one scenario may expose multiple modes; one pattern
→ many results across models, versions, configs.

**Supporting metadata** (not separate layers): trigger/context · effect ·
cause/insufficiency hypothesis · invariant/law violated · detection signal ·
mitigation/guardrail.

**Discovery:** Invent (surface × act × stealer) · Expand (sole×foreign · matrix · residual).  
**Maturation:** Open trajectory → Candidate scenario → Sealed pattern → Execution evidence.

**Terminology guardrails:** mode slug ≠ incident id ≠ scenario id. Portable seed links
registry → pattern. Script = runnable artifact. Proof = evidence + verdict.

**Candidate scenario split** (authoring / console):

| Concept | Meaning |
|---------|---------|
| **User trajectory** | Behavioral story |
| **Scenario geometry** | Normalized adversarial conditions (surface × act × stealer, pins) |
| **Failure-mode mapping** | Class stressed (registry slug) |
| **Mode detection** | Observable evidence the mode materialized (not an “oracle”) |

Optional causal analysis (still not FMEA product): functional insufficiency → trigger →
behavioral failure mode (slug) → effect; incident = one occurrence of that chain.

---

## Doctrine

**LLM proposes · policy validates · code commits** (shorthand: **LLM proposes · code
enforces**).

| Side | Responsibility |
|------|----------------|
| **LLM** | Irregular language; may propose continue, detour, new task, abandon, … |
| **Policy / code** | Whether the transition is permitted; who may commit authoritative state; which record stays active; when ownership may yield; whether a claimed success produced the promised effect |

If enforcement fails open (**soft enforcement**), a plausible model decision can hijack
the path while the reply still sounds helpful. Conjecture regression-tests the
**enforcement layer** under **fixed labels** for CI (not a live model roll).

**Router accuracy** (separate): did the model propose the correct label?  
**Enforcement regression** (Conjecture): given that label, did policy preserve or
transition state correctly? Green enforce + wrong live labels is still a bad product.

**Failure → Law → Proof**

1. **Failure** — what the user experienced  
2. **Law** — what must always hold after the turn  
3. **Proof** — a script that **FAIL**s without the fix and **PASS**es with it  

No law → not sealed. No FAIL/PASS pair → not sealed. Prefer structural ownership when
authority is load-bearing; proofs catch what structure missed.

### In multi-turn systems (plain terms)

In multi-turn systems, each governed workflow transition needs one **authoritative
owner**, a **stable active record**, and rules for when **authority may yield** — even
when several agents contribute to the turn. We are **not inventing** those primitives;
we are **asserting them after every turn** under LLM routing, when helpful detours often
fail-open and chat evals only score the prose.

For readers who prefer classical systems vocabulary:

| Our phrasing | Familiar systems idea |
|--------------|------------------------|
| Who owns the turn? | Exclusive owner (mutex for the active workflow) |
| Which record stays active? | Stable entity pin (foreign-key style) |
| When may ownership yield? | Handoff / lock-release condition |
| Failure → Law → Proof | Bug → invariant → regression test |
| LLM proposes · code enforces | Nondeterministic text must not mutate critical state without validation |

What is under-tested is the **failure class**, not the existence of locks: free-form
routing fail-opens into a helpful path, the prose looks fine, and owner / active record
were never checked. Conjecture standardizes **post-turn state asserts**, **intentional
handoff vs informational detour**, and **planted soft-enforcement must FAIL**.

> After every turn, assert that the correct owner and active record remain intact.
> Test intentional handoffs separately from informational detours. Plant a steal and
> require the suite to catch it.

---

## Worked example (end-to-end)

**Conversation**

1. Claims Agent owns the C-1042 workflow.  
2. User: *“Continue — but what does deductible mean?”*  
3. Glossary Agent answers correctly as a **non-owning contributor**.  
4. A fail-open handoff lets Glossary become **authoritative** — Claims loses ownership;
   C-1042 may lose its pin. Orchestration bug, not a dramatic “coup.”  
5. A human reading the chat: “Nice explanation.” An **executable invariant** is already
   violated: after a definitional detour, Claims must still own the workflow and C-1042
   must remain active.

**Law**

> A definitional detour must not transfer authority or drop the active claim.

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

You *can* assert owner and active record in pytest. That is control state, not a new
primitive. What most suites still miss is the **full list above**: shared multi-turn
shape, portable Observation, fixed-label enforce CI, router vs enforcement split,
planted-FAIL, taxonomy, **discoverability**, and **trajectory invention**.

Happy-path tests check what the engineer remembered. Authority bugs live on compound
turns and soft handoffs nobody scripted until a soak or generator surfaces them.
Invention without acceptance is noise; acceptance without discovery is a thin battery.

Steal the doctrine without the package if you want. Adopt Conjecture when you want that
discipline as a **shared, reviewable artifact**.

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

Same as the opener: durable workflows + real records + real handoffs. Free-form Q&A:
skip. Prefer **one** sealed law over a large aspirational catalog. Battery:
[MATURITY.md](./MATURITY.md) (~six runnable public seeds; [CATALOG](../incidents/CATALOG.md)).

---

## Cost, AI grind, and ownership

**Adoption cost is real.** Many teams correctly decline if authority failures are rare.

### AI can grind the tax

| Task | Role |
|------|------|
| **Trajectory invention** | Propose multi-turn scripts that plausibly create edge conditions (compound continue+detour, mid-flight FAQ, restart, soft handoff) |
| **Discoverability** | Flag soak/log paths where owner or pin already drifted under helpful replies |
| Script drafts | Turns + expected owner/pins from those trajectories |
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

Relinquishing *build* does not relinquish **governance of quality**. Whether you build
in-house or via an SI, builder, or runtime, you still need **multi-turn regression on
the enforcement layer** — not “did the sentence sound smart?” Chat evals can stay with
delivery; post-turn **authoritative owner · active record · handoff** remains someone’s
explicit responsibility, with proofs the buyer can re-run after handoff.

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
