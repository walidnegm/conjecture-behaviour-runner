# Failure-mode catalog (portable CAQ-FM)

**Comprehensive list of authority failure modes** under **LLM proposes · code enforces**.  
This is the human index for [Conversational Authority Quality](../docs/conversational-authority-quality.md).

Each **mode id** is a **slug**: the unique Conjecture/CAQ-FM registry id for a *class*
(e.g. `owner_steal`). That is not an incident id and not a candidate scenario id.
Many incidents and trajectories map to one slug. Full map:
[CAQ § Working taxonomy](../docs/conversational-authority-quality.md#working-taxonomy-not-fmea-reinvention)
(not a full FMEA product).

| Need | Open |
|------|------|
| **Thesis + taxonomy** | [docs/conversational-authority-quality.md](../docs/conversational-authority-quality.md) |
| **Maturity / battery honesty** | [docs/MATURITY.md](../docs/MATURITY.md) |
| **Machine SoT** | [registry.yaml](registry.yaml) (`id` = slug) |
| **Land a seed** | [README.md](README.md) |
| **Runnable proofs** | `patterns/<portable_seed>/` |

**Status legend**

| Status | Meaning |
|--------|---------|
| **runnable** | Portable seed under `patterns/` — FAIL/PASS in CI |
| **seed_pending** | Law is named; no public seed yet (host may already seal) |
| **partial** | Coarse bucket or incomplete portable proof |
| **n_a** | Intentional non-bug path (no seed needed) |
| **host_only** | Documented here for the map; prove-out lives in product hosts (not this package) |

Host monorepos may keep extra product-specific modes. This catalog is the **shared map**
of known CAQ-FM modes. Runnable battery size and package stage: [MATURITY.md](../docs/MATURITY.md).

---

## Vocabulary

| Term | Meaning |
|------|---------|
| **Failure mode** | What went wrong (plain English) |
| **id** | Declarative machine id |
| **portable_seed** | `patterns/` folder name (may differ from id) |
| **Law** | One-line invariant |

---

## Full mode list

### Ownership

| What the user hits | id | portable_seed | Status |
|--------------------|-----|---------------|--------|
| Wrong agent/task keeps talking after continue | `owner_steal` | `owner_steal_mid_continue` | **runnable** |
| Locked record silently changes mid-flight | `pin_drop` | `drop_pin_mid_continue` | **runnable** |
| Mid-flight work wiped / restarted | `illegal_restart` | `illegal_restart_mid_continue` | **runnable** |
| “What am I waiting on?” → wrong leaf | `lost_activity_recall` | — | seed_pending |

### Delivery / open surface

| What the user hits | id | portable_seed | Status |
|--------------------|-----|---------------|--------|
| “Pinned…” but nothing useful opens | `hollow_open` | `pin_without_open` | **runnable** |
| Continue/advance “succeeds” with empty UI | `hollow_advance` | `hollow_async_advance` | **runnable** |
| Wrong code path wins the turn (coarse bucket) | `wrong_delivery_leaf` | — | partial |
| Known name dumps a stream instead of open/pick | `named_item_misresolve` | — | seed_pending |
| Fuzzy name hits glossary, not tenant inventory | `soft_name_misresolve` | — | seed_pending |
| Ambient pin steals the wrong activity | `ambient_pin_hijack` | — | seed_pending |
| Domain pick text hits inventory instead | `domain_pick_misbound` | — | host_only |

### Packaging

| What the user hits | id | portable_seed | Status |
|--------------------|-----|---------------|--------|
| Help/glossary answers instead of the action | `packaging_steal` | — | seed_pending |
| Definitional answer when that is correct | `intentional_glossary` | — | n_a |

### Authoring / cognition

| What the user hits | id | portable_seed | Status |
|--------------------|-----|---------------|--------|
| Cold start fails to sketch / forgets domain | `cold_start_collapse` | `cold_system_suggest_miss` | **runnable** |
| Code path falls into freestyle fabrication | `fall_through_fabrication` | — | seed_pending |
| “Do X and tell me Y” loses half the ask | `compound_act_loss` | — | host_only |

### Substrate (host prove-out — not Conjecture mini-app seeds)

| What the user hits | id | Status |
|--------------------|-----|--------|
| “Saved!” without a real durable id (tool/model rewrite) | `success_payload_rewrite` | host_only |
| Claims saved when commit never ran | `false_save_claim` | host_only |

These stay on host unit/deploy seals (early-return, prompt ban, worker). Listed so the
map is complete; do not invent a second public stack for them without an
Observation-shaped portable proof.

---

## Runnable seeds (quick view)

| id | portable_seed | Prove |
|----|---------------|--------|
| `owner_steal` | `owner_steal_mid_continue` | healthy PASS / planted steal FAIL |
| `pin_drop` | `drop_pin_mid_continue` | |
| `illegal_restart` | `illegal_restart_mid_continue` | |
| `hollow_open` | `pin_without_open` | |
| `hollow_advance` | `hollow_async_advance` | |
| `cold_start_collapse` | `cold_system_suggest_miss` | |

**Count:** 6 runnable · rest named for the shared map (seed_pending / host_only / n_a).

---

## Candidate discovery

```bash
conjecture candidates author --example --out /tmp/cbr_candidates
```

Utterances = script variety only — never product routing.

When a seed lands, add `patterns/<portable_seed>/`, set status **runnable** in
`registry.yaml`, and refresh this catalog.
