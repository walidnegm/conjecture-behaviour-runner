# Conversational Authority Quality (CAQ-FM)

How Conjecture catches **state-law breaks that still look fine in chat** — doctrine plus
the concrete loop (scripts, pinned cognition, Observations, invariants, planted bugs).

Install / demos: [README](../README.md) · Mode map: [CATALOG.md](../incidents/CATALOG.md) ·
Package stage: [MATURITY.md](./MATURITY.md)

---

## The failure class

The reply can sound correct while the machine underneath is wrong:

| Looks fine in chat | Broken underneath |
|--------------------|-------------------|
| Helpful “continue” answer | Wrong specialist owns the turn |
| Talks about “this record” | Pin dropped / switched mid-flight |
| Fresh start after a change | Illegal restart wiped mid-flight work |
| “Done” / “saved” / “pinned” | Nothing useful opened; empty advance |

Those are **ledger / handoff / delivery** bugs, not “bad writing.” LLM-as-judge scores
prose. Unit tests *can* assert owner and pin, but by default most suites do not share a
portable observation contract, an incident taxonomy, or a **healthy PASS + planted FAIL**
discipline. Conjecture is for that enforce path.

**“Authority” ≠ IAM.** Here it means who may act, what stays pinned, when ownership may
yield, and what must open after a claimed success.

**CAQ-FM** names the failure modes. **Conjecture** runs the proofs.

---

## Doctrine

**LLM proposes · code enforces.**

| Side | Responsibility |
|------|----------------|
| **LLM** | Labels: continue, detour, new task, abandon, … |
| **Code** | Exclusive owner, pin identity, yield/handoff, open surface |

Conjecture only checks the **enforce** half, under **pinned** labels (CI must not re-roll
a live model each run). Pair with separate classifier evals. Green enforce + wrong live
labels is still a bad product.

**Failure → Law → Proof**

1. **Failure** — plain user experience  
2. **Law** — what must hold after the turn  
3. **Proof** — script that **FAIL**s without the fix and **PASS**es with it  

No law → not a seal. No FAIL/PASS pair → not sealed.

Prefer structural ownership when authority is load-bearing; seeds catch what structure
missed.

---

## How it works (concrete)

### Script

Multi-turn user text + **expected post-turn state** (your vocabulary):

```text
turn 1  user: "start cost work on record R"
        expect: exclusive_owner = cost_out, pins.workflow_id = R

turn 2  user: "change a mid-flight field"     ← reply may still sound fine
        expect: exclusive_owner still cost_out, pins.workflow_id still R
                (not front_door, not a different id, not a restart)
```

Kinds and pin keys are **yours** (`cost_out` / `workflow_id` are mini-app dogfood only).

### Pinned cognition

Each turn’s classification is **fixed** for the run (pin or freeze):

```text
turn 2 label = continue     # not sampled from a live model in CI
```

Question under test: *given this label, did code keep owner · pin · handoff law?*  
Not: *did the model pick the right label?*

### Driver → Act → Observation

1. **Driver** runs your real turn path (in-process, HTTP, LangGraph, Temporal, …).  
2. After Act, project host state into an **Observation** Conjecture can check:

```text
Observation
  exclusive_owner: "cost_out"          # or idle / front_door / your kind
  pins: { workflow_id: "R" }         # any pin map your host freezes
  # optional: open/delivery signals your invariants care about
```

Projection is the integration tax: map *your* session/graph/workflow blob → this shape.
You do not rewrite the whole ledger into Conjecture types.

### Invariants

Typical checks after each turn:

| Check | Example fail |
|-------|----------------|
| Owner held | continue stole to `front_door` / another specialist |
| Pin held | `workflow_id` became null or a different id |
| No illegal restart | mid-flight task wiped and re-opened |
| Handoff law | yield only when your rules allow (e.g. abandon / detour) |
| Open surface | “pinned” / advance with empty delivery |

### Planted-bug proof

| Implementation | Verdict required |
|----------------|------------------|
| Healthy enforce | **PASS** |
| Soft enforce (planted steal / pin drop / illegal restart) | **FAIL** |

If the planted bug still PASSes, the invariant is decoration, not a seal.

```text
  script turns
      │
      ▼
  pinned labels ──► Driver.Act ──► Observation ──► invariants
                                                      │
                                    healthy PASS · planted FAIL
```

Run the mini-app planted demos from the [README](../README.md)
(`conjecture path-faithful --prove-bugs`) to see FAIL then PASS.

### Modes (what the catalog is for)

| User-visible break | Mode id (examples) | Public seed today |
|--------------------|--------------------|-------------------|
| Wrong owner after continue | `owner_steal` | runnable |
| Pin changes mid-flight | `pin_drop` | runnable |
| Work wiped / restarted | `illegal_restart` | runnable |
| Pinned but nothing opens | `hollow_open` | runnable |
| Advance “succeeds” empty | `hollow_advance` | runnable |
| Cold start collapses | `cold_start_collapse` | runnable |
| …other modes | see catalog | seed_pending / host_only |

Full list and status: [CATALOG.md](../incidents/CATALOG.md).  
**Today:** on the order of **six runnable** portable seeds; most of the map is named but
not yet a public battery ([MATURITY.md](./MATURITY.md)). Hosts still seal the long tail.

---

## Cost, AI grind, and when to skip

**Adoption cost is real:** scripts with expected state, Observation projection, driver
upkeep, catalog hygiene. Many teams will **correctly decline** if authority failures are
rare — steal **Failure → Law → Proof** and **LLM proposes · code enforces** without the
package. Prefer **one** sealed law on your path over a large aspirational catalog.

### What AI can do on the grind

A maintenance agent (or host loop) can usefully:

| Task | How it helps |
|------|----------------|
| Script drafting | From soak logs: emit turns + expected owner/pins when anomalies appear |
| Planted variants | Mutate a healthy script into soft-enforce (steal owner, drop pin, restart) |
| Projection stubs | Update Observation mapping when session fields rename |
| Catalog hygiene | Suggest mode id, registry row, seed_pending → runnable after a real FAIL/PASS |

### What AI must not silently own

| Risk | Guard |
|------|--------|
| Wrong law accepted | Human (or explicit high-bar) **sign-off** on the invariant |
| Flaky suite | Drafts only; **pinned** goldens + deterministic Driver in CI |
| Auto-merge without proof | Require planted **FAIL** and healthy **PASS** before merge |
| Recursive drift | Treat the maintainer agent like any LLM: **proposes**, does not own enforce |

Same doctrine one level up: the agent proposes scripts and laws; **code + seal** own what
CI trusts. If the maintainer is nondeterministic, you poison the reliability layer.

**Outsourced build (one line):** implementers may do the grind; whoever is accountable for
outcomes still **accepts** the laws. The engineering object stays scripts, Observations,
and invariants.

---

## Terms

| Term | Meaning |
|------|---------|
| **Pinned cognition** | Labels fixed for the CI run |
| **Observation** | Post-turn owner · pins · outcome projection |
| **Soft enforce** | Code fails open so the model can steal while sounding helpful |
| **Seed** | Portable script + planted-bug proof under `patterns/` |
| **CAQ-FM** | Named modes + laws + proofs for this failure class |

---

## Links

| Doc | Role |
|-----|------|
| [README](../README.md) | Install, planted-bug demos, drivers |
| [CATALOG](../incidents/CATALOG.md) | Full mode list + status |
| [MATURITY.md](./MATURITY.md) | Stage / battery / known gaps |
| [SPEC](./SPEC.md) | Normative package contract |
| [incidents/README](../incidents/README.md) | Classify → land a seed |

---

## One sentence

Pin the labels, project an Observation, require **PASS** on healthy and **FAIL** on
planted soft enforce — so fluent chat cannot hide broken owner · pin · handoff law.
