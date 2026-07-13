# Conjecture patterns inventory (incident catalog)

**This is the public registry of failure-class patterns.**  
One row per **slug** · one folder under `patterns/<slug>/` · executable `script.json` when CI-ready.

| Concept | Meaning |
|---------|---------|
| **Failure mode** | What goes wrong (plain language) |
| **Slug** | Stable id of that failure mode (`pin_without_open`) |
| **Law** | What must hold after Act |
| **Pattern** | `INCIDENT.md` + `script.json` under `patterns/<slug>/` |
| **Ratchet** | Script/test that keeps the law green forever |

Playbook (how to add, Conjecture-class filter): [`README.md`](README.md).  
Vocabulary (seal, pin, open leaf, …): monorepo `docs/the-language-of-building-ai-products.md` when developing Bot0; portable ideas restated in each `INCIDENT.md`.

---

## Index

| Slug | Class | Law broken | Host kind / pin example | Status | Notes |
|------|-------|------------|-------------------------|--------|-------|
| `owner_steal_mid_continue` | owner steal | exclusive_owner must stay mid-flight kind on continue | demo: `cost_out` | portable seed | Mini-app bug `owner_steal` |
| `drop_pin_mid_continue` | pin drop | pin_equals / pin_present on continue | demo: `workflow_id` | portable seed | Mini-app bug `drop_pin` |
| `illegal_restart_mid_continue` | illegal restart | mid-flight must not wipe active task | demo: `cost_out` | portable seed | Mini-app bug `illegal_restart` |
| `pin_without_open` | hollow open | identity pin must not be sole answer; open surface (`blocks_resolve`) | demo: `scenario_id` | portable seed | Mini-app bug `pin_without_open`; host path seal + staging ref `conv_09449a0d` |

Add a row when you land `patterns/<slug>/` with at least `INCIDENT.md` + `script.json`.

**Host vocabulary:** replace demo kinds/pins with your ledger types when porting.

---

## How this relates to other docs

```text
incidents/CATALOG.md          ← YOU ARE HERE (patterns inventory)
incidents/README.md           ← classify → capture → land pattern
incidents/patterns/<slug>/    ← one failure class each
examples/                     ← demos / E2E (not the full inventory)
templates/                    ← parameterized script shapes
tests/                        ← package unit tests (harness), not product goldens
```

**Host-private product goldens** (full chat path, tenant data) stay in the **host
application repository** — not this package. Adopters keep their own script
registry and path seals next to their product; only **portable** patterns land
here.

Do not copy tenant/product-only goldens into this public tree.
