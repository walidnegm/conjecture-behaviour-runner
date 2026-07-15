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

**Narrow by design today.** Even with honest “skip” guidance, this framework only
*shines* if you have (or will build) something like a **conversation control plane**:
exclusive ownership, entity pinning/locking, explicit handoff / yield rules. Free-form
or heavily emergent multi-agent designs (vector search + tool soup, no durable owner)
are not a soft fit — they are a **different architecture**. Forcing this package onto
them means **imposing structure first**. That is a feature for the target audience and
a non-starter for everyone else. The *ideas* (propose vs enforce, failure → law →
proof) can travel; the *machinery* should not be bolted on as fashion.

You are not “adding a test runner.” You are aligning product code to a **control-plane
shape** (or projecting one out of existing ledger state). If that shape is absent,
adoption cost is a **refactor**, not a pip install.

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
an **ongoing tax**, not a one-time setup — especially for a small team shipping weekly:

| Cost | What you do |
|------|-------------|
| **Scripts** | Multi-turn user messages + **expected state after each turn** |
| **Projection** | Map your internal session / graph / workflow state into Observation (owner · pins · outcome) |
| **Drivers** | Keep adapters current for LangGraph, Temporal, HTTP, custom stores, … |
| **Catalog hygiene** | Registry rows, catalog status, seeds under `patterns/` when you promote a law |
| **CI cognition** | Pin or freeze labels so goldens are deterministic (separate from live model quality) |

If you already have exclusive owner + pins after each act, wiring a Driver is the main
job. If you do **not**, the first bill is design, not YAML.

**Many teams will correctly decline.** The burn rate of authority failures may not
justify the tax. That is a product judgment, not a moral failure. Prefer **one** real
law sealed on your path over a growing catalog of aspirational modes. If you only need
the vocabulary, steal **Failure → Law → Proof** and **LLM proposes · code enforces**
without adopting Conjecture at all.

---

## Terminology (onboarding curve)

Precise language reduces ambiguity; it also creates a **non-trivial learning cliff**.
New readers will need a few terms before seeds and drivers make sense:

| Term | Plain meaning |
|------|----------------|
| **Authority failure** | Reply looks fine; who owns / what is locked / what opened is wrong |
| **Enforce half** | Coded rule-set after the model proposes a label |
| **Observation** | Your post-turn state projected into owner · pins · outcome fields Conjecture can check |
| **Pinned cognition** | Labels fixed for CI so the same golden fails for the same state break |
| **Soft enforce** | Code that falls through / fails open so the model can steal while sounding helpful |
| **CAQ-FM** | Named map of authority failure modes + laws + proofs |
| **Seed** | Portable script + planted-bug proof under `patterns/` |
| **Runnable / seed_pending / host_only** | This package can prove it / law named only / product host seals it |

You do not need every term on day one. Start with **owner · pin · handoff** after a
turn. Everything else is packaging around that check.

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
| True async / multi-writer races | See **Known gaps** below — not deep in this guide yet |

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
land as **host_only** or **seed_pending**. You are largely buying a **philosophy +
shared vocabulary + a thin proven core + a harness**, not a comprehensive drop-in
regression wall. Hosts still carry the long tail of seals. That is early-package
reality, not a temporary doc footnote.

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

## Known gaps (honest, expandable)

These are real production classes this guide and package do **not** yet treat deeply:

| Gap | Why it matters | Where it might grow |
|-----|----------------|---------------------|
| **Concurrency / races** | Parallel turns, multi-writer agents, Temporal/async workers can break owner/pin law without any single-turn soft enforce | Host fencing (`expected_version` / claim), future Conjecture multi-actor scripts |
| **Classifier half** | Wrong proposals + green enforce = silent UX decay | Separate evals; not folded into Conjecture goldens |
| **Thin portable battery** | Map >> runnable seeds | Promote host seals when Observation-shaped |
| **Lighter adoption** | Full scripts + drivers is heavy for small teams | Templates, thinner “minimum authority” projection (owner+pin only) |
| **Terminology cliff** | Precise = dense | This glossary; more “plain English first” examples |

Naming a gap is not a roadmap commitment. It is a place the **scope can expand** without
diluting the core.

---

## Broader scope: what can expand (without diluting the core)

The **current slice** is narrow on purpose: **authority after a turn** under pinned
labels, for control-plane-shaped systems.

The **portable core** is broader than the current battery, and is what should grow:

| Layer | Today | Expandable toward |
|-------|--------|-------------------|
| **Doctrine** | LLM proposes · code enforces; Failure → Law → Proof | Same triad for other “code owns truth” surfaces (saves, tables, finite acts) — still not general product QA |
| **Control plane** | Owner · pin · yield / handoff | Optimistic concurrency, multi-agent exclusivity, claim/TTL — still code-owned |
| **Conjecture** | Scripted multi-turn enforce regression | More seeds; multi-actor / race scripts; richer Observations; still not LLM-as-judge |
| **CAQ-FM map** | Named authority modes + status | Promote seed_pending → runnable; keep host_only honest |
| **Half-story pair** | Enforce only | Sibling cognition quality (labels/prompts) without merging into enforce goldens |

**What expansion is not:** turning this into “all agent reliability,” ChatGPT-style evals,
or mandatory process for free-form bots. Breadth grows by **more sealed laws on the
enforce path** and **clearer composition with other tools** — not by claiming every
chat product needs a full CAQ stack.

If you adopt only one idea from this document, take **Failure → Law → Proof** under
**LLM proposes · code enforces**. Everything else (registry, seeds, drivers) is optional
machinery for teams that already pay for state.

---

## How a new reader should use this package

1. **Decide fit** — stateful control plane vs free-form chatbot (see above).  
2. **Read this guide** — state-law breaks, costs, half-story, expansion horizon.  
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
(or will) own a control plane. The core ideas travel farther than the current battery;
the machinery should not be forced on products that do not earn it.
