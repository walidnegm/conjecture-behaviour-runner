# Conjecture patterns inventory (incident catalog)

**This file is the public registry of portable failure-mode patterns.**  
It is **not** the full history of every host product bug.

## Vocabulary

| Term | Meaning | Example |
|------|---------|---------|
| **Failure mode** | What goes wrong (plain English; industry term) | hollow open · packaging steal |
| **Slug** | Stable machine **id** only (folders, scripts, greps) | `pin_without_open` |
| **Class** (if used in a table) | Same as **failure mode** — not the snake_case id |

Snake_case strings like `delivery_order_gap` / `packaging_too_wide` are **slugs**, not mode names.

| Layer | What lives here |
|-------|-----------------|
| **Portable seeds** (`patterns/<slug>/` + `script.json`) | Runnable without a product host |
| **Documented failure modes** | Plain-language laws; seed may be pending |
| **Host product inventory** | Host app STEAL + chat-path scripts — many more rows |

Playbook: [`README.md`](README.md).

---

## Portable seeds (runnable mini-app)

| Failure mode | Slug (id) | Law broken | Demo pin / kind | Status |
|--------------|-----------|------------|-----------------|--------|
| Owner steal | `owner_steal_mid_continue` | exclusive_owner must stay mid-flight on continue | kind `cost_out` | portable seed |
| Pin drop | `drop_pin_mid_continue` | pin must stay on continue | pin `workflow_id` | portable seed |
| Illegal restart | `illegal_restart_mid_continue` | continue must not wipe active task | kind `cost_out` | portable seed |
| Hollow open | `pin_without_open` | pin is not the product answer; open surface (`blocks_resolve`) | pin `scenario_id` | portable seed |
| Cold system-suggest miss | `cold_system_suggest_miss` | cold system-suggest open → authoring sketch + domain sticky on short re-ask | kind `authoring`, pin `domain_label`, extra `sketch_produced` | portable seed |
| Hollow advance | `hollow_async_advance` | authoring advance must open surface (not silent job/gate success) | kind `authoring`, `read_kind=authoring_advance`, extras `open_surface` / `reply_nonempty` | portable seed |

Prove: healthy mini-app **PASS**; planted bug **FAIL**. See `tests/test_incidents_library.py`.

---

## Broader failure modes (tracked laws — not only four)

Runnable public seeds exist only where Status says “portable seed.” Host dogfood seals many more with product path tests (not published here).

| Failure mode (plain) | Slug (if any) | Law (one line) | Portable seed |
|----------------------|---------------|----------------|---------------|
| Owner steal | `owner_steal_mid_continue` / host `missing_sole_continue` | Mid-flight continue keeps exclusive owner | `owner_steal_mid_continue` |
| Pin drop | `drop_pin_mid_continue` | Mid-flight continue keeps identity pin | `drop_pin_mid_continue` |
| Illegal restart | `illegal_restart_mid_continue` | Continue must not wipe active task | `illegal_restart_mid_continue` |
| Hollow open | `pin_without_open` | Pin is routing authority; delivery must open surface | `pin_without_open` |
| Hollow advance | `hollow_async_advance` | Authoring advance / async job success must open surface (not empty succeed) | `hollow_async_advance` |
| Packaging steal | `packaging_too_wide` | Glossary must not package over action or inventory | seed pending |
| Missing session leaf | `missing_state_leaf` | Session / waiting-on → ledger leaf, not glossary | seed pending |
| Wrong delivery leaf | `delivery_order_gap` | Wrong code leaf won (inventory, save, dispatch, …) | partial |
| Inventory name exclusive | *(often under wrong delivery leaf)* | Known inventory name → code open/pick, not LLM dump | seed pending |
| Inventory soft name | *(often under wrong delivery leaf)* | Partial name → tenant inventory, not platform glossary | seed pending |
| Context-pin hijack | *(often under wrong delivery leaf)* | Ambient pin must not steal wrong activity | seed pending |
| Fall-through trap | — | Code-owned turn must not fall into freestyle LLM | seed pending |
| Cold system-suggest miss | `cold_system_suggest_miss` | Cold system-suggest open enters authoring + produces first sketch; short re-ask binds prior domain — not thin-structure refuse / amnesia | `cold_system_suggest_miss` |
| Intentional glossary detour | `true_glossary_detour` | Definitional answer when packaging *should* run (OK) | n/a |

**Honest count:** 6 runnable public seeds · **dozen+** plain failure modes · host tables often **10–20+** sealed incident rows.

### Candidate discovery: expander + inventor (portable)

Do **not** wait only for production soaks. Author **candidate Scenarios** from host
vocabulary, then promote open paths to Scripts. Normative: [docs/SPEC.md §2.2](../docs/SPEC.md).

| Engine | What it does | Package surface |
|--------|--------------|-----------------|
| **Inventor** (prefer first) | Geometry: exclusive surface × typed act × pre-decide stealer | `candidate_author.invent` · `invent_all` |
| **Expander** | Cross-product: sole-continue kind × foreign leaf; matrix cells | `paths_from_sole_continue_x_foreign` · matrix YAML |
| **Propose** (opt-in) | LLM suggests surfaces/stealers; code law + physics backcheck | `--invent-llm` · `CONJECTURE_INVENT_LLM_*` |

```bash
conjecture candidates author --example --out /tmp/cbr_candidates
conjecture candidates author --example --invent-llm --out /tmp/cbr_candidates
```

Defaults: **4** inventive scenarios / **4** LLM proposals per author turn.  
Templates: [`templates/candidate_author/`](../templates/candidate_author/).

Host monorepos may keep a private **law-centric finite matrix** (core + neighbors) and
long-tail utterances for script authoring only — never runtime routing vocabulary.

| Artifact | Where |
|----------|--------|
| Portable candidate author | `conjecture candidates author` · `templates/candidate_author/` |
| Invent prompt (editable) | `candidate_author/prompts/geometry_propose.md` |
| Host matrix / utterances | Host-private (optional) |
| Gap report | Host gap CLI (optional) |

When a portable seed lands here, the host matrix cell for that slug should move to
`sealed` (or stay `host_only` only if no public seed is intended).

---

## How this relates to other docs

```text
incidents/CATALOG.md          ← YOU ARE HERE
incidents/README.md           ← classify → capture → land pattern
incidents/patterns/<slug>/    ← runnable seeds (folder name = slug)
templates/candidate_author/   ← expand + invent host vocabulary templates
docs/SPEC.md §2.2             ← normative expander + inventor
examples/                     ← demos (not full inventory)
tests/                        ← package unit tests — NOT the inventory
```

When you land `patterns/<slug>/` with `INCIDENT.md` + `script.json`, add a **portable seeds** row using **failure mode** + **slug** columns.

**Host-private product goldens** stay in the host application repository.
