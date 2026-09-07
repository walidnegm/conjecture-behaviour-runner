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
| **Golden-turn stage** | Where on the SDK [golden turn](https://github.com/walidnegm/conversation-control-plane/blob/main/docs/conversation-control-plane-sdk.md#the-golden-turn--one-correct-turn-end-to-end) (0–6 + **5b**) the class burns |

Diagnose by stage before patching: a steal is stage **4**, a hollow open is stage **5**,
a CONTINUES act that never reaches its editor is stage **5b**, a complete that was
an abandon is stage **6**. The catalog below is the class list; the stage is the
audit lens (same template as the Control Plane SDK — not a second doctrine).

---

## Full mode list

### Ownership

| What the user hits | id | portable_seed | Status |
|--------------------|-----|---------------|--------|
| Wrong agent/task keeps talking after continue | `owner_steal` | `owner_steal_mid_continue` | **runnable** |
| Locked record silently changes mid-flight | `pin_drop` | `drop_pin_mid_continue` | **runnable** |
| Mid-flight work wiped / restarted | `illegal_restart` | `illegal_restart_mid_continue` | **runnable** |
| Mid cost-out + “any recommendations?” re-loops sizing / free-form tips | `owner_steal` (neighbor) | `cost_out_recommend_no_leave` | **runnable** (host) / seed |
| Stale recommendation route after project/workflow change | `wrong_delivery_leaf` | — | seed_pending (`rec_route_*` host slugs) |
| Duplicate objective chip double-launches setup | `wrong_delivery_leaf` | — | seed_pending (`rec_route_duplicate_chip_idempotent`) |
| “What am I waiting on?” → wrong leaf | `lost_activity_recall` | — | seed_pending |

### Delivery / open surface

| What the user hits | id | portable_seed | Status |
|--------------------|-----|---------------|--------|
| “Pinned…” but nothing useful opens | `hollow_open` | `pin_without_open` | **runnable** |
| Continue/advance “succeeds” with empty UI | `hollow_advance` | `hollow_async_advance` | **runnable** |
| Stated CONTINUES act never reaches its host reader (editor) | `continues_act_not_delivered` | — | **host_only** (`conv_5566b22c` · TC-O) |
| Asks for a name/pick but next free-text is greenfield | `open_leaf_unarmed_return` | — | seed_pending |
| “Next: Goal Seek?” then “yes please” → list/workflows | `continuum_invite_unarmed_affirm` | — | seed_pending |
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
| Open mid-draft improve/strengthen steals to IR | `draft_improve_to_ir` | — | host_only |
| Cognition labels rewritten by apply_* / gate_detour / decide | `cognition_override` | — | seed_pending |
| Staffed/compiled then cold re-extract | `staffed_free_text_advance` | — | host_only |

### Open-leaf / continuum (portable law — host proofs today)

| What the user hits | id | Status | Law sketch |
|--------------------|-----|--------|------------|
| Invite without stamp; next token re-routes cold | `open_leaf_unarmed_return` | seed_pending | Ask ⇒ arm same package |
| Continuum chips; natural affirm misses target surface | `continuum_invite_unarmed_affirm` | seed_pending | Pin + armed-only affirm |
| After mute/disconnect, freestyle without ledger View | `resume_without_rehydrate` | seed_pending | Rehydrate projection first |

### Substrate (host prove-out — not Conjecture mini-app seeds)

| What the user hits | id | Status |
|--------------------|-----|--------|
| “Saved!” without a real durable id (tool/model rewrite) | `success_payload_rewrite` | host_only |
| Claims saved when commit never ran | `false_save_claim` | host_only |
| Name pin claimed as registry row without id | `soft_existence_claim` | seed_pending (portable law · A19) |
| Closed id slot accepts freestyle garbage | `id_slot_thin_verify` | host_only |

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

**Count:** 6 runnable · 25 registry modes (incl. 2026-08 continuum / open-leaf / soft-existence promotions) · rest seed_pending / host_only / n_a.

---

## Broader failure modes

Named on the shared map but **not** all runnable in this package (host seals /
seed_pending). Still first-class slugs in `registry.yaml`. Plain mode names
(human) sit beside machine ids / legacy STEAL buckets:

| Plain failure mode | id / legacy |
|--------------------|-------------|
| Packaging steal | `packaging_steal` · legacy `packaging_too_wide` |
| Cognition overwritten after propose | `cognition_override` · C26 S0d/S2 (named) |
| Staffed then cold extract | `staffed_free_text_advance` · host |
| Missing session leaf | `lost_activity_recall` · legacy `missing_state_leaf` |
| Hollow open | `hollow_open` · portable seed `pin_without_open` |
| CONTINUES act never reaches host reader | `continues_act_not_delivered` · host TC-O |
| Wrong delivery leaf | `wrong_delivery_leaf` · legacy `delivery_order_gap` |
| Open mid-draft improve → IR | `draft_improve_to_ir` · host `conv_1732aa88` |
| Compound act loss | `compound_act_loss` · host compound leaves |
| ID slot thin-verify | `id_slot_thin_verify` · host `conv_828ad8d5` · purity L42 |
| Utterance-to-slot leakage | `utterance_to_slot_leakage` · host name pins · L41 cousin |

| id | Where prove-out lives today |
|----|-----------------------------|
| `draft_improve_to_ir` | Host monorepo · residual open-improve-not-IR |
| `compound_act_loss` | Host compound primary/secondary leaves |
| `continues_act_not_delivered` | Host · `test_host_act_reachability_contract` · scan of CONTINUES read_kinds vs `chat()` doors |
| `packaging_steal` / `wrong_delivery_leaf` / … | Host STEAL table + product ratchets |
| `success_payload_rewrite` / `false_save_claim` | Host unit / deploy |
| `id_slot_thin_verify` | Host · `test_id_slot_thin_verify_seal` · pattern_id / create_scenario / risk_id |
| `utterance_to_slot_leakage` | Host · `test_utterance_to_slot_seal` |

### Fix approach — `id_slot_thin_verify` (practice, not one-offs)

When this mode burns (free text as closed id; identity-fallback normalize; raw
slot in chat errors), **do not** invent a side normalizer or phrase laundry.
Follow the host law (AGENTS §2 *ID-slot thin-verify* · purity L42):

| # | Practice | Detail |
|---|----------|--------|
| **1. Law** | LLM proposes · code thin-verifies | Membership in allow-table / catalog only. No identity fallback on ids. |
| **2. Normalize** | Chip/alias → id · Unknown → empty · Omitted → optional default · Invalid present → **refuse** | Never default freestyle NL to a real pattern id. Contains-match only under short chip grammar. |
| **3. Error** | Product refuse | Never put unresolved raw slot values in user-facing `detail` / `summary.error`. |
| **4. Crawl** | Bounded ratchet | Grep `normalize_*_id` for miss without closed-set check — start pattern, scenario, risk, domain, role_id, profile_id tool args. Metadata return-raw helpers often OK (not enum SoR). |
| **5. Separate backlog** | Wrong leaf under sticky midflight | Impact-score → `create_scenario` is **routing** (tool allow-table / pre-decide yield) — not another normalizer tweak. Neighbor: fall-through / owner steal. |

**Cousins (do not collapse):**

| Mode | Layer |
|------|--------|
| `utterance_to_slot_leakage` | Short **name** value vs naming speech act |
| `soft_existence_claim` | Name pin ≠ registry **existence** (A19) — **seed_pending** in `registry.yaml` |
| `id_slot_thin_verify` | Closed **identity** membership after LLM tool args |

Host contract: monorepo `id_slot_thin_verify_contract` · registry law on this slug.

Do not invent a second public mini-app stack for host-only modes without an
Observation-shaped portable proof.

---

## Candidate discovery

```bash
conjecture candidates author --example --out /tmp/cbr_candidates
```

Utterances = script variety only — never product routing.

When a seed lands, add `patterns/<portable_seed>/`, set status **runnable** in
`registry.yaml`, and refresh this catalog.
