# Conjecture portable failure-mode catalog

Portable CAQ-FM slice (**LLM proposes · code enforces**).

| Need | Open |
|------|------|
| **Doctrine** | [`../docs/conversational-authority-quality.md`](../docs/conversational-authority-quality.md) |
| **Machine SoT** | [`registry.yaml`](registry.yaml) |
| **Land playbook** | [`README.md`](README.md) |
| **Proofs** | `patterns/<portable_seed>/` |

Not the full host product history.

---

## Vocabulary

| Term | Meaning |
|------|---------|
| **Failure mode** | Plain English what went wrong |
| **id** | Declarative machine id |
| **portable_seed** | `patterns/` folder (may differ from id) |
| **Law** | One-line invariant |

---

## Runnable portable seeds

| What the user hits | id | portable_seed | Plane |
|--------------------|-----|---------------|-------|
| Wrong owner after continue | `owner_steal` | `owner_steal_mid_continue` | ownership |
| Locked record changes mid-flight | `pin_drop` | `drop_pin_mid_continue` | ownership |
| Mid-flight work wiped | `illegal_restart` | `illegal_restart_mid_continue` | ownership |
| Pinned but nothing useful opens | `hollow_open` | `pin_without_open` | delivery |
| Advance “succeeds” empty | `hollow_advance` | `hollow_async_advance` | delivery |
| Cold start fails to sketch / domain sticky | `cold_start_collapse` | `cold_system_suggest_miss` | authoring |

Prove: healthy mini-app **PASS**; planted bug **FAIL**.

---

## Broader modes (seed may be pending)

| What the user hits | id | parent | seed_status |
|--------------------|-----|--------|-------------|
| Glossary over action | `packaging_steal` | — | seed_pending |
| Lost activity recall | `lost_activity_recall` | — | seed_pending |
| Wrong code path wins (coarse) | `wrong_delivery_leaf` | — | partial |
| Known name dumps stream | `named_item_misresolve` | `wrong_delivery_leaf` | seed_pending |
| Fuzzy name → glossary | `soft_name_misresolve` | `wrong_delivery_leaf` | seed_pending |
| Ambient pin steals activity | `ambient_pin_hijack` | `wrong_delivery_leaf` | seed_pending |
| Fall into freestyle fabrication | `fall_through_fabrication` | — | seed_pending |
| Definitional answer OK | `intentional_glossary` | — | n_a |

---

## Out of public scope

See `out_of_scope` in [`registry.yaml`](registry.yaml) (substrate rewrite, host-only modes until portable).

---

## Candidate discovery

```bash
conjecture candidates author --example --out /tmp/cbr_candidates
```

Utterances = script variety only — never product routing.
