# Conversational Authority Quality (public companion)

## 0. Setup

**Short name:** CAQ-FM (portable)

**Problem.** Multi-turn agents often fail without sounding broken: the wrong specialist
owns the turn, a pin drops, or “open” returns empty status. That is **authority
leakage**, not bad prose.

**What Conjecture does here.** Under **LLM proposes · code enforces**, this package
regression-tests the **enforce** half: after scripted turns, **owner · pin · open ·
handoff** still hold when cognition is pinned/frozen for CI.

**What this package is.** The **portable slice** of CAQ-FM — laws that can be proved
without a full product host. Fuller host monorepos may keep a longer mode list and
substrate seals.

| Start here | Path |
|------------|------|
| **This doc** | Doctrine + land checklist |
| **Mode list** | [`../incidents/CATALOG.md`](../incidents/CATALOG.md) |
| **Machine SoT** | [`../incidents/registry.yaml`](../incidents/registry.yaml) |
| **How to land a seed** | [`../incidents/README.md`](../incidents/README.md) |
| **Runner face** | [`../README.md`](../README.md) |

**Vocabulary.** Everyday terms (seal, sole-continue, open leaf, exclusive owner, pin)
appear in this doc and CATALOG. Optional deeper monorepo lexicon: host path
`docs/the-language-of-building-ai-products.md` (not vendored here — keeps CBR lean).

---

## 1. Doctrine

| LLM | Code |
|-----|------|
| Labels / options under pin-freeze | Exclusive owner, pin, open surface, handoff law |

**Unit:** failure → law → seed (or seed_pending) → CI FAIL/PASS.

Prevention in the host beats stacking more public seeds.

---

## Seed join (declarative id ↔ patterns folder)

| id (declarative) | portable_seed (folder) |
|------------------|-------------------------|
| `owner_steal` | `owner_steal_mid_continue` |
| `pin_drop` | `drop_pin_mid_continue` |
| `illegal_restart` | `illegal_restart_mid_continue` |
| `hollow_open` | `pin_without_open` |
| `hollow_advance` | `hollow_async_advance` |
| `cold_start_collapse` | `cold_system_suggest_miss` |

Folder names stay stable for CI paths; **ids** are the readable mode names.

---

## In / out

| In | Out |
|----|-----|
| Owner steal, pin drop, illegal restart | Success-payload rewrite / false save (host) |
| Hollow open / advance | Prompt + worker deploy |
| Cold-start collapse | Domain math, prose tone |

---

## Land a portable law

1. Row in `registry.yaml` (`id`, `portable_seed`, `law`)  
2. `patterns/<portable_seed>/` with FAIL/PASS proof  
3. CATALOG update  

Classify: [incidents/README.md](../incidents/README.md).

---

## Rule

Doctrine and laws. Prefer host structural seals. Public seeds only when portable and
still need prove-out. Prune noise.
