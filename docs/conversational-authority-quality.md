# Conversational Authority Quality (CAQ-FM)

**Category thesis** for Conjecture Behaviour Runner.  
Install and demos: [README](../README.md). Package maturity and battery size: [MATURITY.md](./MATURITY.md).

---

## The failure class

In multi-turn agents, the **reply can look successful** while the system has violated
**ownership, identity, continuity, or handoff**. Examples:

- Wrong specialist still owns the turn after “continue”
- Locked customer / claim / ticket / account silently changes
- Mid-flight work is illegally restarted
- A “success” opens nothing useful

Those are **state-integrity and handoff** failures — not “bad writing.” LLM-as-judge and
surface evals score prose; they do not prove the machine underneath stayed lawful.

**“Authority” here is not IAM.** It is *conversation and workflow authority*: who may act,
what record stays pinned, when control may yield, and what must be delivered after a
claimed success. Closest enterprise categories: **agent state integrity**, **workflow
integrity**, **transaction continuity**, **invalid handoff**, **unauthorized state
mutation**.

---

## Doctrine

**LLM proposes · code enforces.**

| Side | Role |
|------|------|
| **Cognition (LLM)** | Interprets the user; proposes labels (continue, detour, new task, abandon, …) |
| **Code** | Exclusive owner, pinned entity, when ownership may yield, that delivery actually opens |

If enforcement is soft, the model can steal or hijack the path and still sound helpful.
Conjecture regression-tests the **enforce** side: after each scripted turn, **owner · pin
· handoff law** still hold under **pinned** labels (so CI is deterministic). It does not
score free-text classifiers; pair it with separate cognition evals.

**Institutional memory** for each sealed defect:

1. **Failure** — what the user experienced  
2. **Law** — what must always hold after the turn  
3. **Proof** — a script that fails without the fix and passes with it  

A test with no law is not a seal. A law with no proof is not sealed.

**Why not “just pytest”?** You *can* assert owner and pin in ad-hoc tests. What ordinary
tooling does **not** provide by default is a **shared authority model**, an
**incident-derived taxonomy**, a **portable observation contract**, and a **vendor-neutral
proof discipline** (healthy PASS + planted FAIL, reproducible across stacks). Conjecture
exists to institutionalize that contract — not to invent asserting fields.

---

## Enterprise wedge: who owns the law

Enterprises increasingly **outsource agent implementation** (SI, software vendor, cloud
partner, managed service) while **orchestration and observability** sit on platforms
(Microsoft, AWS, ServiceNow, Salesforce, LangChain, Temporal, …). That does not move
accountability.

| Role | Typical party |
|------|----------------|
| Defines business-acceptable behavior and authority laws | **Enterprise** process / product owner |
| Security and governance requirements | Enterprise architecture / risk / security |
| Builds the agent | SI, vendor, or partner |
| Operates the agent | Enterprise or managed provider |
| Supplies orchestration / observability | Platform vendors |
| Accepts whether implementation is good enough | **Enterprise** — not the implementer alone |

**Companies will offload the machinery. They should not offload the law.**

Implementation providers may draft scripts, projections, drivers, and catalog entries.
AI agents can accelerate that grind. **The enterprise must own and accept the authority
contract** — what counts as correct ownership, pinning, mutation, yield, and delivery.
Otherwise an SI can define weak criteria, implement against them, run its own suite, and
self-certify.

That is the durable reason for a **vendor-neutral** layer:

> **Buyer-owned conformance tests for vendor-built AI agents.**  
> A portable, executable definition of who may act, what must remain pinned, and when
> control may transfer — even when someone else builds and operates the agent.

Adjacent platforms will add multi-turn scripts, invariants, and dashboards. The
differentiator is not “we also test state.” It is that the **acceptance contract stays
owned by the buyer**, portable across implementers, frameworks, and migrations.

### Operating model

| Activity | Enterprise | Delivery provider | Conjecture / independent QA |
|----------|------------|-------------------|-----------------------------|
| Surface experienced failure | Accountable | Consulted | Structures taxonomy |
| Decide the authority **law** | **Accountable** | Consulted | Structures Failure → Law → Proof |
| Implement enforcement | Reviews | **Accountable** | Independent of vendor stack |
| Draft scripts & projections | **Approves** | Performs (or AI-assisted) | Automates / validates shape |
| Planted-failure proof | Reviews | Performs | Verifies PASS/FAIL discipline |
| Production readiness accept | **Accountable** | Cannot self-approve | Supplies reproducible evidence |
| Maintain after platform change | Owns requirement | Performs | Detects weakening |

---

## What Conjecture is

**Not primarily:** “a test runner for teams who already built a control plane.”

**Primarily:** a **vendor-neutral acceptance-contract layer** for stateful multi-turn
systems — client-owned laws, portable observations, framework-independent seeds, and
FAIL/PASS evidence the buyer can keep when the SI or stack changes.

In practice, after each turn of a script:

1. Labels are **pinned** (cognition frozen for the run)  
2. The host projects **Observation** (owner · pins · outcome — your vocabulary)  
3. Invariants are checked  
4. Soft enforcement must **FAIL**; healthy path must **PASS**

```text
  Experienced authority failure
            │
            ▼
  Named mode + law   (CAQ-FM catalog / registry)
            │
            ▼
  Script + invariants  (Conjecture)
            │
            ▼
  Evidence: PASS healthy · FAIL planted violation
```

Named modes and seeds: [CATALOG.md](../incidents/CATALOG.md) ·
[registry.yaml](../incidents/registry.yaml).

**CAQ-FM** = Conversational Authority Quality — Failure Modes: the map of those failures,
their laws, and how they are proven. Conjecture is the engine that runs the proofs.

---

## Fit (one paragraph)

This layer pays rent when **state is load-bearing**: multi-turn workflows, specialists,
pinned records, handoffs. Free-form single-turn Q&A without ownership or pins does not
need it. For package readiness, seed count, and known gaps, see
[MATURITY.md](./MATURITY.md) — not this thesis.

---

## Links

| Doc | Role |
|-----|------|
| [README](../README.md) | Install, demos, drivers |
| [MATURITY.md](./MATURITY.md) | Readiness, battery, gaps |
| [CATALOG](../incidents/CATALOG.md) | Mode list + status |
| [SPEC](./SPEC.md) | Normative package contract |
| [incidents/README](../incidents/README.md) | Classify → land a seed |

---

## One sentence

Fluent answers can conceal broken coded authority. Enterprises may outsource the agent;
they should not outsource the **definition and acceptance** of who may act, what stays
pinned, and when control may transfer. Conjecture makes that contract **executable and
portable**.
