# Conversational Authority Quality (CAQ-FM)

**Conceptual home** for Conjecture Behaviour Runner — the failure class, the doctrine,
and how proofs work.  
Install / demos: [README](../README.md). Package stage and seed battery: [MATURITY.md](./MATURITY.md).

---

## Catch state-law breaks that still look fine in chat

In multi-turn agents, the reply can sound correct while the **conversation machine**
underneath is wrong:

- Wrong specialist owns the turn after “continue”
- Locked record (claim, ticket, account, workflow) silently changes
- Mid-flight work is illegally restarted
- A “success” opens nothing useful

Those are **ledger / handoff / delivery** failures — not “bad writing.” LLM-as-judge and
surface evals score prose. They do not prove ownership, identity, continuity, or handoff
still held.

**“Authority” here is not IAM.** It is conversation and workflow authority: who may act,
what record stays pinned, when control may yield, what must open after a claimed success.
Familiar names: agent state integrity, workflow integrity, invalid handoff, unauthorized
state mutation.

**CAQ-FM** = Conversational Authority Quality — Failure Modes: named breaks, laws, and
proofs. **Conjecture** runs those proofs.

---

## Doctrine

**LLM proposes · code enforces.**

| Side | Role |
|------|------|
| **LLM** | Interprets the user; proposes labels (continue, detour, new task, abandon, …) |
| **Code** | Exclusive owner, pin identity, when ownership may yield, that delivery actually opens |

If enforcement is soft, the model can steal or hijack the path and still sound helpful.
Conjecture tests the **enforce** half under **pinned** labels so CI is deterministic. It
does **not** score free-text classifiers — pair it with separate cognition evals. Green
enforce + wrong live labels is still a bad product.

**Institutional memory** for each sealed defect:

1. **Failure** — what the user experienced  
2. **Law** — what must always hold after the turn  
3. **Proof** — a script that fails without the fix and passes with it  

A test with no law is not a seal. A law with no proof is not sealed.

When authority is load-bearing, prefer structural ownership (exclusive owner, real pins,
early-return after real saves). Seeds catch what structure missed; they do not replace
product design.

**Why not only ad-hoc unit tests?** You *can* assert owner and pin in pytest. Ordinary
tooling does not, by default, give a shared authority model, an incident-derived taxonomy,
a portable observation contract, or a healthy PASS + planted FAIL discipline reusable
across hosts. That institutionalization is the point of this package.

---

## How Conjecture works (the mechanics)

This is the load-bearing section. If you only remember one procedure, remember this.

### 1. Script

A multi-turn list of user messages plus **expected state after each turn** (owner, pins,
handoff constraints). Scripts are host vocabulary: your kind strings, your pin keys.

### 2. Pinned cognition

Classification labels for each turn are **fixed** (pin or freeze) for the run. CI must
not re-roll a live model every time. Conjecture answers: *given these labels, did code
still seal?* — not “was the classifier right?”

### 3. Driver + Act

Your **Driver** runs the real turn path (in-process mini-app, HTTP JSON, LangGraph,
Temporal projection, …). After Act, the host is in some internal session state.

### 4. Observation

You **project** that state into a small portable shape Conjecture can check:

| Field family | Meaning |
|--------------|---------|
| **Owner** | Exclusive owner / active kind (your strings) |
| **Pins** | Locked entity ids (workflow_id, claim_id, …) |
| **Outcome** | What opened / was delivered when relevant |

You do not rewrite your ledger into Conjecture’s types beyond this projection.

### 5. Invariants

After each turn, checks such as:

- exclusive owner still equals the mid-flight kind  
- pins still equal the locked record  
- no illegal restart / silent pin drop  
- handoff only when your rules allow  
- delivery opened a real surface when the law requires it  

### 6. Planted-bug discipline

For a law to count as sealed:

| Path | Required verdict |
|------|------------------|
| Healthy implementation | **PASS** |
| Soft-enforce / planted violation | **FAIL** |

If soft enforce still PASSes, the invariant is not load-bearing.

```text
  User turns (script)
        │
        ▼
  Pinned labels ──► Driver.Act ──► Observation
                                      │
                                      ▼
                              Invariant checks
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
              healthy → PASS                    planted bug → FAIL
```

Named modes and seeds: [CATALOG.md](../incidents/CATALOG.md) ·
[registry.yaml](../incidents/registry.yaml). Some `patterns/` folder names are older than
declarative mode ids (CI path stability); prefer ids in discussion.

**Fit:** pays rent when state is load-bearing (owners, pins, handoffs). Free-form
single-turn Q&A without that shape does not need the machinery — the doctrine still
travels. Seed count and package stage: [MATURITY.md](./MATURITY.md) (~6 runnable seeds
today; map is broader).

---

## Who does the work (grind vs law)

| Work | Can be delegated | Must not be weakly owned |
|------|------------------|---------------------------|
| Scripts, projections, drivers, catalog drafts | Implementers, SIs, **AI agents** | — |
| The **law** (what must always hold) | Proposed by anyone | **Accepted** by whoever is accountable for outcomes |
| Production readiness | Evidence from implementer | Accountable party signs off — implementer should not self-certify alone |

### AI can grind the tax

Mechanical cost is real: multi-turn scripts, Observation mapping, driver upkeep, catalog
hygiene. A well-scoped agent (or host loop) can:

- Draft scripts from conversation logs / soaks when owner/pin anomalies appear  
- Propose planted-bug variants for soft enforce  
- Keep projection stubs in sync when session schema drifts  
- Suggest registry rows and seed promotions  

That makes the package more practical for small teams **if** drafts stay subordinate to
deterministic CI and human seal of laws.

### Recursion risk

If the agent that *maintains* the suite is nondeterministic or drifting, you inject
flakiness into the layer that exists to catch flakiness. Rules of thumb:

1. AI **proposes** scripts and laws; **pinned** goldens and code-owned invariants **own** CI.  
2. Never auto-merge a law without a FAIL-without-fix / PASS-with-fix check.  
3. Treat suite maintenance agents as untrusted authors — same as untrusted LLM labels.

Same doctrine, one level up: **LLM proposes · code (and human seal) enforces.**

### When delivery is outsourced

SIs and vendors often build and operate the agent. They may do the grind. The buyer still
**accepts** the authority laws and the evidence bundle. That is a short governance note,
not the main product pitch — the engineering object remains scripts, Observations, and
invariants.

Adoption cost is real. Prefer one sealed law on your path over a large aspirational
catalog. If authority failures are rare, steal the doctrine and skip the machinery.

---

## Terms

| Term | Meaning |
|------|---------|
| **Observation** | Post-turn projection: owner · pins · outcome |
| **Pinned cognition** | Labels fixed for CI |
| **Soft enforce** | Code fails open so the model can steal while sounding helpful |
| **Seed** | Portable script + planted-bug proof under `patterns/` |
| **Runnable / seed_pending / host_only** | This package proves it / law named only / host seals it |

---

## Links

| Doc | Role |
|-----|------|
| [README](../README.md) | Install, demos, drivers |
| [MATURITY.md](./MATURITY.md) | Stage, battery size, gaps |
| [CATALOG](../incidents/CATALOG.md) | Mode list + status |
| [SPEC](./SPEC.md) | Normative contract |
| [incidents/README](../incidents/README.md) | Classify → land a seed |

---

## One sentence

Fluent answers can conceal broken coded authority. Pin the labels, project an
Observation, require PASS on healthy and FAIL on planted soft enforce — and keep law
acceptance with whoever owns the outcome.
