# Conversational Authority Quality (CAQ-FM)

**How Conjecture relates to named failure modes — and why that matters.**

This is the portable quality guide for [conjecture-behaviour-runner](https://github.com/walidnegm/conjecture-behaviour-runner).  
If you only read one conceptual doc beyond the README, make it this one.

---

## Why this exists

Multi-turn agents fail in a distinctive way: the **reply can look fine** while the
**conversation machine underneath is wrong**.

Examples users actually hit:

- They say “continue,” and a *different* specialist takes over (wrong owner).
- They refer to “this workflow,” but the system silently switched records (pin dropped).
- They open a saved scenario and get “Pinned scenario…” with nothing useful to work on
  (pin without an open surface).
- Advance/continue reports success, but the UI shows an empty step (hollow advance).

Those are not “bad writing.” They are **authority failures**: who owns the turn, what is
locked, whether delivery opened a real surface, whether a save was real.

Ordinary unit tests and LLM-as-judge evals often miss them, because the **prose** still
passes. Conjecture is built for the cases where **state law** is broken.

---

## Where Conjecture fits

The design principle is simple:

> **LLM proposes · code enforces.**

| Side | Responsibility |
|------|----------------|
| **LLM** | Interpret the user; propose labels such as continue, detour, new task, abandon |
| **Code** | Decide exclusive owner, pin identity, when ownership may yield, and that delivery actually opens |

If enforcement is soft, the model can **steal or hijack** the path and still produce a
helpful-looking answer. Conjecture regression-tests the **enforce** half:

1. You write a short multi-turn **script** (user messages + expected state after each turn).  
2. Cognition is **pinned or frozen** so CI is repeatable (this package does not score free-text classifiers).  
3. After each turn, Conjecture checks **owner · pin · open surface · handoff law**.  
4. A planted soft-enforce bug must **FAIL**; the healthy path must **PASS**.

So Conjecture is not “did the bot sound smart?” It is: **given these labels, did your
coded rule-set still seal the conversation?**

---

## What “Conversational Authority Quality” means

**CAQ-FM** is the name for that quality program:  
**Conversational Authority Quality — Failure Modes.**

It answers:

1. **What classes of authority failure exist?** (named modes, plain English)  
2. **What law was broken?** (one sentence)  
3. **How do we prove it stays fixed?** (portable seed and/or host tests)

Conjecture is the **engine** that runs those proofs under pinned cognition.  
CAQ-FM is the **map of failures** and how they relate to the engine.

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

## Doctrine in one page

### The split (again, with stakes)

| If only the LLM owns the path… | If only code owns meaning… |
|--------------------------------|----------------------------|
| Fluent steals, silent pin drops, empty “success” | Brittle keyword routing, no real understanding |

Viable products do both: **model for irregular language**, **code for authority**.

### Unit of institutional memory

When something breaks and you fix it, capture:

1. **Failure** — what the user experienced (plain language)  
2. **Law** — what must always hold after the turn  
3. **Proof** — a seed or test that fails without the fix and passes with it  

That unit is more valuable than a test named `test_scenario_xyz` with no stated invariant.

### Prevention still beats paperwork

The strongest fix is structural: early-return after real saves, exclusive owners, finite
chips for code-owned choices, no fall-through into freestyle chat for authority paths.

Conjecture seeds and host ratchets **catch what structure missed**. They are not a
substitute for making the right path the only easy path in product code.

---

## Failure modes: the catalog companion

The full list of modes lives in:

**[incidents/CATALOG.md](../incidents/CATALOG.md)** — comprehensive human index  
**[incidents/registry.yaml](../incidents/registry.yaml)** — machine source of truth  

Examples of modes (see catalog for the full set):

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

**Status in the catalog** tells you honestly:

- **runnable** — this package can FAIL/PASS it under `patterns/`  
- **seed_pending** — law is named; public seed not landed yet  
- **host_only** — product hosts seal it; not a mini-app seed (e.g. substrate save rewrite)

So the catalog is **not** “only six demos.” It is the **full map**, with honest status.

### Seed folders vs mode ids

Some `patterns/` folder names are older than the declarative ids. That is intentional
so CI paths stay stable:

| Mode id (prefer this in discussion) | Folder under `patterns/` |
|-------------------------------------|---------------------------|
| `owner_steal` | `owner_steal_mid_continue` |
| `pin_drop` | `drop_pin_mid_continue` |
| `illegal_restart` | `illegal_restart_mid_continue` |
| `hollow_open` | `pin_without_open` |
| `hollow_advance` | `hollow_async_advance` |
| `cold_start_collapse` | `cold_system_suggest_miss` |

Talk in plain failure language or declarative ids. Use folder names only for paths.

---

## How a new reader should use this package

1. **Read the [README](../README.md)** — what Conjecture checks after each turn.  
2. **Skim this doc** — why authority failures matter and how CAQ-FM relates.  
3. **Open the [catalog](../incidents/CATALOG.md)** — which modes exist and which are runnable.  
4. **Run a planted-bug demo** from the README / examples — see FAIL then PASS.  
5. **Land a law** only when you have a real multi-turn state break:
   - classify (see [incidents/README.md](../incidents/README.md))  
   - add registry row + `patterns/<seed>/` + catalog status  
   - prove FAIL without the fix, PASS with it  

You do **not** need a new public seed for every host bug. Prefer structural host fixes;
promote to a portable seed when the law is Observation-shaped and reusable.

---

## What Conjecture does *not* claim

| Not Conjecture’s job | Where that lives instead |
|----------------------|---------------------------|
| Free-text classifier quality | Separate cognition / prompt tests |
| Domain math, pricing tables | Domain / product tests |
| Prose tone and style | LLM eval |
| Save rewritten by prompt/worker desync | Host substrate seals (listed as host_only in catalog) |

Conjecture pins cognition on purpose so CI is **deterministic**. Pair it with classifier
tests if you care about “was the label right?”

---

## Relationship to a full product host

Product hosts (e.g. Bot0) may keep:

- more modes and STEAL incident tables  
- unit ratchets and deploy checks  
- a longer private registry  

This package ships the **portable companion**: shared doctrine, shared mode names, and
runnable seeds that any host can adopt without product secrets.

Optional deeper vocabulary when you work inside such a monorepo:  
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

**Conjecture** runs multi-turn scripts that fail when coded authority softens.  
**CAQ-FM** names those failures, their laws, and which ones this package can prove today.  
Together they make “LLM proposes · code enforces” **testable**, not just a slogan.
