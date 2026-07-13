# Conjecture patterns inventory (incident catalog)

**This file is the public registry of portable failure-class patterns.**  
It is **not** the full history of every host product bug.

| Layer | What lives here |
|-------|-----------------|
| **Portable seeds** (`patterns/<slug>/` + runnable `script.json` on mini-app) | Adopters can FAIL/PASS without a product host |
| **Documented classes** (table below, seed pending) | Named laws we track; host may already seal them |
| **Host product inventory** | Stays in the host application (STEAL table, chat-path scripts, path seals) — **many more rows** than this file |

Playbook: [`README.md`](README.md).  
Vocabulary: seal · slug · pin · open leaf · ratchet (see host lexicon when dogfooding Bot0).

---

## Portable seeds (runnable mini-app)

| Slug | Class | Law broken | Demo kind / pin | Status | Notes |
|------|-------|------------|-----------------|--------|-------|
| `owner_steal_mid_continue` | owner steal | exclusive_owner must stay mid-flight kind on continue | `cost_out` | portable seed | Mini-app bug `owner_steal` |
| `drop_pin_mid_continue` | pin drop | pin_equals / pin_present on continue | `workflow_id` | portable seed | Mini-app bug `drop_pin` |
| `illegal_restart_mid_continue` | illegal restart | mid-flight must not wipe active task | `cost_out` | portable seed | Mini-app bug `illegal_restart` |
| `pin_without_open` | hollow open | identity pin must not be sole answer; open surface (`blocks_resolve`) | `scenario_id` | portable seed | Mini-app bug `pin_without_open` |

Prove: healthy mini-app **PASS**; planted bug **FAIL**. See `tests/test_incidents_library.py`.

---

## Broader failure classes (tracked laws — not only four)

These are **real classes** in multi-turn hosts (control plane + delivery). Public **runnable** seeds exist only where Status says “portable seed.” The rest are **named laws** adopters should seal in the host; Bot0 dogfood seals many of them with product path tests (not published here).

| Class / slug | Law (one line) | Portable seed | Typical host proof |
|--------------|----------------|---------------|--------------------|
| **owner steal** | Mid-flight continue keeps exclusive owner | `owner_steal_mid_continue` | sole-continue matrix / chat-path |
| **pin drop** | Mid-flight continue keeps identity pin | `drop_pin_mid_continue` | pin-hold scripts |
| **illegal restart** | Continue must not wipe active task | `illegal_restart_mid_continue` | path-faithful prove-bugs |
| **pin_without_open** | Pin is routing authority; delivery must open surface | `pin_without_open` | host open-leaf + content blocks |
| **packaging_too_wide** | Glossary / product_knowledge must not package over action or inventory | seed pending | concept_packaging gates + exclusive owner |
| **missing_state_leaf** | Session / waiting-on / activities must hit ledger leaf, not glossary | seed pending | session_activities exclusive owner |
| **missing_sole_continue** | Sticky kinds own continue vs front-door / concept | related: owner steal | sole_continue_blocks_concept_gate |
| **delivery_order_gap** | Wrong leaf won (inventory name, save, dispatch, soft name, …) | partial | delivery-order table + inventory resolve |
| **inventory name exclusive** | Armed / known inventory name → code open or pick, not LLM stream dump | seed pending | armed_list_name_contract |
| **inventory soft token** | Partial name (“keynote project”) hits tenant inventory, not platform glossary | seed pending | soft distinctive-token match |
| **concept_gate steals inventory** | Definitional packaging must yield when inventory resolves | seed pending | same family as packaging + inventory |
| **context-pin hijack** | Ambient pin must not steal wrong activity | seed pending | delivery-order / active_flow yield |
| **fall-through trap** | Code-owned turn must not return None into freestyle LLM tables | seed pending | host path seals |
| **true_glossary_detour** | Intentional definitional answer when packaging eligible (OK) | n/a | not a bug class |

**Honest count:** 4 runnable public seeds · **dozen+** named classes · host product tables often hold **10–20+ sealed incident rows** per mature dogfood.

---

## How this relates to other docs

```text
incidents/CATALOG.md          ← YOU ARE HERE (public patterns inventory)
incidents/README.md           ← classify → capture → land pattern
incidents/patterns/<slug>/    ← runnable portable seeds only
examples/                     ← demos (not full inventory)
templates/                    ← parameterized script shapes
tests/                        ← package unit tests — NOT the inventory
```

When you land `patterns/<slug>/` with `INCIDENT.md` + `script.json`, add a **portable seeds** row.

**Host-private product goldens** stay in the host application repository. Do not copy tenant data or monorepo-only paths into this tree.

---

## Expanding this catalog (expected growth)

Public seeds should grow as we prove FAIL/PASS on the mini-app (or a sanitized host adapter):

1. packaging_too_wide  
2. missing_state_leaf / session status  
3. inventory soft token / concept steals inventory  
4. context-pin hijack  

Until then, the **class rows above** are the inventory of laws — not an empty world of four bugs.
