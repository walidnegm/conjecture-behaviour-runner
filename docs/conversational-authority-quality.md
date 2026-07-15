# Conversational Authority Quality (CAQ-FM)

**Conceptual home** for Conjecture Behaviour Runner.  
Install / demos: [README](../README.md). Package stage and seed battery: [MATURITY.md](./MATURITY.md).

---

## Catch state-law breaks that still look fine in chat

In multi-turn agents, the reply can sound correct while the **conversation machine**
underneath is wrong: wrong specialist owns the turn, locked record silently changed,
mid-flight work illegally restarted, or a “success” that opens nothing useful.

Those are **ledger / handoff / delivery** failures — not “bad writing.” Surface evals and
LLM-as-judge score prose. They do not prove ownership, identity, continuity, or handoff
still held.

**“Authority” here is not IAM.** It means conversation and workflow authority: who may
act, what record stays pinned, when control may yield, what must open after a claimed
success. Familiar labels: agent state integrity, workflow integrity, invalid handoff,
unauthorized state mutation.

**CAQ-FM** (Conversational Authority Quality — Failure Modes) names those breaks, their
laws, and how they are proven. **Conjecture** runs the proofs.

---

## Doctrine

**LLM proposes · code enforces.**

| Side | Role |
|------|------|
| **LLM** | Interprets the user; proposes labels (continue, detour, new task, abandon, …) |
| **Code** | Exclusive owner, pin identity, when ownership may yield, that delivery actually opens |

If enforcement is soft, the model can steal or hijack the path and still sound helpful.
Conjecture regression-tests the **enforce** half under **pinned** labels so CI is
repeatable. It does not score free-text classifiers — pair it with separate cognition
evals. Green enforce + wrong live labels is still a bad product.

**Institutional memory** when something breaks and you seal it:

1. **Failure** — what the user experienced  
2. **Law** — what must always hold after the turn  
3. **Proof** — a script that fails without the fix and passes with it  

A test with no law is not a seal. A law with no proof is not sealed.

When authority is load-bearing, prefer structural ownership (exclusive owner, real pins,
early-return after real saves, finite chips for code-owned acts). Seeds and ratchets
catch what structure missed; they do not replace product design.

**Why not only ad-hoc unit tests?** You *can* assert owner and pin in pytest. Ordinary
tooling does not, by default, give a **shared authority model**, **incident-derived
taxonomy**, **portable observation contract**, or **healthy PASS + planted FAIL**
discipline reusable across hosts. That institutionalization is the point.

---

## What Conjecture checks (the how)

After each turn of a multi-turn **script**:

1. User messages run through your **Driver** (in-process or HTTP).  
2. Cognition is **pinned or frozen** (labels fixed for the run — not a live model roll).  
3. Your host projects an **Observation**: owner · pins · outcome (your vocabulary).  
4. Invariants check **owner · pin · open surface · handoff law**.  
5. A planted soft-enforce bug must **FAIL**; the healthy path must **PASS**.

```text
  Experienced authority failure
            │
            ▼
  Named mode + law   (catalog / registry)
            │
            ▼
  Script + Observation + invariants
            │
            ▼
  PASS healthy · FAIL planted violation
```

Modes and status: [CATALOG.md](../incidents/CATALOG.md) ·
[registry.yaml](../incidents/registry.yaml).  
Seed folders may keep older names; prefer declarative mode ids in discussion (see
catalog).

**Fit in one line:** pays rent when state is load-bearing (owners, pins, handoffs). Free-form
single-turn Q&A without that shape does not need the machinery — take the doctrine if useful.
Readiness and battery size: [MATURITY.md](./MATURITY.md).

---

## Who does the work

| Work | Who can perform it | Who must own acceptance |
|------|--------------------|-------------------------|
| Draft scripts, projections, drivers, catalog rows | Implementers, SIs, **AI agents** | — |
| Decide the **law** (what must always hold) | Process / architecture proposes | **Buyer of the outcome** (product owner, not the implementer alone) |
| Accept production readiness | Reviews evidence | **Buyer** — vendor should not self-certify against weak criteria |

**AI can grind the tax** (script drafts from logs, projection patches, registry hygiene,
driver stubs). That is pragmatic for small teams. **Law definition and seal sign-off**
stay human-led (or extreme oversight). Wrong laws = false security. A nondeterministic
agent that *maintains* the suite can inject flakiness into the layer that exists to catch
flakiness — keep CI proofs deterministic even when drafts are AI-assisted.

When delivery is **outsourced** (SI, vendor, managed service), the same split scales up:
enterprise owns the authority contract; the provider implements and proves against it.
Conjecture is useful as a **portable, vendor-neutral evidence layer** for that contract —
not only as an in-house test harness. Adjacent platforms will add scripts and dashboards;
the durable point is that **acceptance criteria stay owned by the party accountable for
outcomes**, not only the party writing the agent.

---

## Terms (minimal)

| Term | Meaning |
|------|---------|
| **Observation** | Post-turn state projected for checks (owner · pins · outcome) |
| **Pinned cognition** | Labels fixed for CI so the same golden fails for the same state break |
| **Soft enforce** | Code fails open so the model can steal while sounding helpful |
| **Seed** | Portable script + planted-bug proof under `patterns/` |

---

## Links

| Doc | Role |
|-----|------|
| [README](../README.md) | Install, demos, drivers |
| [MATURITY.md](./MATURITY.md) | Stage, battery, gaps |
| [CATALOG](../incidents/CATALOG.md) | Mode list + status |
| [SPEC](./SPEC.md) | Normative contract |
| [incidents/README](../incidents/README.md) | Classify → land a seed |

---

## One sentence

Fluent answers can conceal broken coded authority. **LLM proposes · code enforces**;
Conjecture proves the enforce half under pinned labels. Keep the **law** with whoever is
accountable for the outcome — implementers and agents may do the grind.
