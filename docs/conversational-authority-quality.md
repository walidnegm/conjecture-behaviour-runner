# Conversational Authority Quality (CAQ-FM)

## Catch state-law breaks that still look fine in chat

In multi-turn agents, the reply can sound correct while the **conversation machine**
underneath is wrong: the wrong specialist owns the turn, the locked record silently
changed, or a mid-flight task was illegally restarted. Those failures are **ledger and
handoff bugs**, not “bad writing.” Ordinary unit tests and LLM-as-judge evals usually
miss them.

The design principle is **LLM proposes · code enforces**. The model may emit
labels—continue, detour, new task, abandon—but **deterministic code** (your rule-set)
must decide exclusive owner, pin identity, and when ownership may yield. If that
enforcement is soft, the model can **steal or hijack** the path and still produce a
helpful-looking answer. Conjecture is regression for the **enforce** half: after each
scripted turn it checks that owner · pin · handoff law still hold.

That is the quality problem this package is built around. **CAQ-FM**
(**Conversational Authority Quality — Failure Modes**) names those breaks, their laws,
and how you prove they stay sealed.

This guide is the conceptual home for that pitch. The [README](../README.md) is the
package face (install, demos, drivers). If you only read one conceptual doc, make it
this one.

---

## Who this is for — and who should skip it

**Worth studying / adopting when** you already run (or are committed to building) a
**stateful multi-turn agent** with real records and handoffs: claims, tickets,
workflows, multi-step planning, specialists that must not steal mid-flight. If wrong
owner / silent pin drop / illegal restart would be a product incident, this vocabulary
pays rent.

**Safely ignore for now when** you are still “chain some prompts and see,” or ship a
mostly free-form RAG / single-turn Q&A bot without exclusive ownership, entity locks, or
handoff law. In that world Conjecture is **over-engineered**: you would first have to
pay the **control-plane design debt** (name owners, pins, yield rules) before any seed
is meaningful. Guardrails + prompt hygiene may be enough until state becomes load-bearing.

The package is honest that it targets complex stateful agents. What it often under-states
is how much **upfront structural work** that implies: you are not “adding a test runner”;
you are aligning product code to a **control plane shape** (or projecting one out of
existing ledger state). If that shape is absent, adoption cost is a **refactor**, not a
pip install.

---

## Doctrine

| Side | Responsibility |
|------|----------------|
| **LLM** | Interpret the user; propose labels such as continue, detour, new task, abandon |
| **Code** | Decide exclusive owner, pin identity, when ownership may yield, and that delivery actually opens |

| If only the LLM owns the path… | If only code owns meaning… |
|--------------------------------|----------------------------|
| Fluent steals, silent pin drops, empty “success” | Brittle keyword routing, no real understanding |

Stateful products that hit authority failures usually need **both**: model for irregular
language, code for authority. Simpler products may never need the full split.

**Unit of institutional memory** when something breaks and you fix it:

1. **Failure** — what the user experienced (plain language)  
2. **Law** — what must always hold after the turn  
3. **Proof** — a seed or test that fails without the fix and passes with it  

A test with no law is not a seal. A law with no ratchet is not sealed.

### Structure helps; it is not a religion

When authority is load-bearing, **prefer** structural ownership (early-return after real
saves, exclusive owners, finite chips for code-owned choices, no soft fall-through into
freestyle chat for mutative paths). That is where most production pain lives.

It is **not** a claim that every conversational product needs a full “authority quality”
layer, registry, and seed library. Some domains are simple enough that a few guardrails
and solid prompts suffice. Use this machinery when the failure class keeps burning money
or trust — not because a doc said so.

Conjecture seeds and host ratchets **catch what structure missed**. They do not replace
product design.

---

## What adoption actually costs

The demo loop (plant a bug → FAIL → PASS) is clean in a mini-app. On a real backend it is
**non-trivial busywork**, especially for a small team shipping weekly:

| Cost | What you do |
|------|-------------|
| **Scripts** | Multi-turn user messages + **expected state after each turn** |
| **Projection** | Map your internal session / graph / workflow state into Observation (owner · pins · outcome) |
| **Drivers** | Keep adapters current for LangGraph, Temporal, HTTP, custom stores, … |
| **Catalog hygiene** | Registry rows, catalog status, seeds under `patterns/` when you promote a law |
| **CI cognition** | Pin or freeze labels so goldens are deterministic (separate from live model quality) |

If you already have exclusive owner + pins after each act, wiring a Driver is the main
job. If you do **not**, the first bill is design, not YAML. Prefer **one** real law sealed
on your path over a growing catalog of aspirational modes.

---

## What Conjecture checks (the enforce half)

1. You write a short multi-turn **script** (user messages + expected state after each turn).  
2. Cognition is **pinned or frozen** so CI is repeatable (this package does not score free-text classifiers).  
3. After each turn, Conjecture checks **owner · pin · open surface · handoff law**.  
4. A planted soft-enforce bug must **FAIL**; the healthy path must **PASS**.

So Conjecture is not “did the bot sound smart?” It is: **given these labels, did your
coded rule-set still seal the conversation?**

```text
  User-visible authority failure
            │
            ▼
  Named mode + law  (CAQ-FM catalog / registry)
            │
            ▼
  Script + invariants  (Conjecture)
            │
            ▼
  CI: FAIL on soft enforce, PASS when sealed
```

---

## Half the quality story (classifier drift)

Conjecture is deliberately **only the enforce half**. That is a feature for CI
repeatability and a **hard limit** in production:

- If the model starts proposing the **wrong label** more often, enforcement goldens can
  stay **green** while user experience degrades.  
- The two halves are **coupled in the product** even when tests split them.  
- You still need **separate classifier evals, prompt regression, and monitoring**.  

Do not treat a green Conjecture suite as “conversation quality is fine.” It means:
**given the labels you pinned, code did not soften.** Cognition drift is a different
budget.

| Not Conjecture’s job | Where that lives instead |
|----------------------|---------------------------|
| Free-text classifier quality / drift | Cognition tests, prompt evals, online monitoring |
| Domain math, pricing tables | Domain / product tests |
| Prose tone and style | LLM eval |
| Save rewritten by prompt/worker desync | Host substrate seals (`host_only` in catalog) |

---

## Failure modes: map vs battery

The full list of modes lives in:

**[incidents/CATALOG.md](../incidents/CATALOG.md)** — human index  
**[incidents/registry.yaml](../incidents/registry.yaml)** — machine source of truth  

| What the user hits | Mode id | Public seed? |
|--------------------|---------|--------------|
| Wrong specialist after “continue” | `owner_steal` | Yes (`owner_steal_mid_continue`) |
| Locked record changes mid-flight | `pin_drop` | Yes |
| Mid-flight work wiped | `illegal_restart` | Yes |
| Pinned but nothing useful opens | `hollow_open` | Yes |
| Advance “succeeds” empty | `hollow_advance` | Yes |
| Cold start fails to sketch / domain sticky | `cold_start_collapse` | Yes |
| Glossary answers instead of the action | `packaging_steal` | Named; seed pending |
| “Do X and tell me Y” loses half | `compound_act_loss` | Host prove-out today |

**Status** is intentional honesty:

- **runnable** — this package can FAIL/PASS it under `patterns/`  
- **seed_pending** — law named; no public seed yet  
- **host_only** — product hosts seal it; not a portable mini-app seed  

**Readiness (v0.1.x):** the **catalog is broader than the battery**. Today there are on
the order of **six runnable portable seeds**. Most production bugs you will hit still
land as **host_only** or **seed_pending**. That is normal for a young package: you are
largely buying a **philosophy + shared vocabulary + a thin proven core**, not a
battle-tested wall of every failure mode. Hosts still carry the long tail of seals.

### Seed folders vs mode ids

Some `patterns/` folder names are older than the declarative ids (CI path stability):

| Mode id (prefer in discussion) | Folder under `patterns/` |
|--------------------------------|---------------------------|
| `owner_steal` | `owner_steal_mid_continue` |
| `pin_drop` | `drop_pin_mid_continue` |
| `illegal_restart` | `illegal_restart_mid_continue` |
| `hollow_open` | `pin_without_open` |
| `hollow_advance` | `hollow_async_advance` |
| `cold_start_collapse` | `cold_system_suggest_miss` |

Talk in plain failure language or declarative ids. Use folder names only for paths.

---

## How a new reader should use this package

1. **Decide fit** — stateful control plane vs free-form chatbot (see above).  
2. **Read this guide** — state-law breaks, costs, half-story.  
3. **Skim the [README](../README.md)** — install, demos, drivers.  
4. **Open the [catalog](../incidents/CATALOG.md)** — map vs which modes are runnable.  
5. **Run a planted-bug demo** — see FAIL then PASS on the mini-app.  
6. **Land a law only when you have a real multi-turn state break** on *your* path:
   - classify (see [incidents/README.md](../incidents/README.md))  
   - registry + seed when the law is Observation-shaped and reusable  
   - prove FAIL without the fix, PASS with it  

You do **not** need a new public seed for every host bug. Prefer a structural fix on the
host; promote a portable seed when the law generalizes.

---

## Relationship to a full product host

Product hosts (e.g. Bot0) may keep more modes, STEAL incident tables, unit ratchets,
deploy checks, and a longer private registry. This package ships the **portable
companion**: shared doctrine, shared mode names, and the runnable seeds any host can
adopt without product secrets.

Optional deeper vocabulary inside such a monorepo:  
`docs/the-language-of-building-ai-products.md` (host repo — not copied here).

---

## Quick links

| Doc | Role |
|-----|------|
| [README](../README.md) | Package face + demos |
| [CATALOG](../incidents/CATALOG.md) | Full mode list + status |
| [registry.yaml](../incidents/registry.yaml) | Machine mode list |
| [incidents/README](../incidents/README.md) | Classify → capture → land |
| [SPEC](./SPEC.md) | Normative package contract |

---

## In one sentence

**Conjecture** fails CI when coded authority softens under pinned labels.  
**CAQ-FM** names those failures and which ones this package can prove today.  
Together they make “LLM proposes · code enforces” **testable** — for teams that already
(or will) own a control plane. Everyone else can take the idea and skip the machinery.
