# Incident: hollow async advance (portable seed)

| Field | Value |
|-------|--------|
| **Slug** | `hollow_async_advance` |
| **Failure mode (plain)** | Hollow advance (silent success) |
| **Family** | Hollow delivery (sibling of **hollow open** / `pin_without_open`) |
| **Date** | 2026-07-13 |
| **Host** | path-faithful mini-app · host dogfood Bot0 |
| **Conversation / ref** | Bot0 `conv_f583ecd5` (Continue to structured draft) |
| **Conjecture-class?** | yes (open surface after advance) |

## Symptom (what the user saw)

- User advanced an authoring stream (chip or **proceed** / “Continue to structured draft”).
- Backend **job/gate succeeded** (or phase moved to IR review).
- UI showed **nothing** — empty reply, no IR card, loading cleared.
- User believes the product is stuck; control state may already have advanced.

Planted bug id (mini-app): `hollow_async_advance`.

## Portable law (vocabulary-independent)

**When a turn advances multi-step authoring** (sketch → structured review / gate /
async worker completion), delivery must:

1. **Open a product surface** — non-empty user-visible content **and/or** structured
   blocks (`open_surface` / `blocks_resolve`), **or**
2. **Fail closed** with a typed user-visible error.

Never report **success** with an empty open surface (silent success).

### Granularity vs hollow open

| Failure mode | Slug | Wrong thing |
|--------------|------|-------------|
| **Hollow open** | `pin_without_open` | Identity **pin** written; answer is pin-status only |
| **Hollow advance** | `hollow_async_advance` | **Advance** (job/gate/chip) succeeds; answer/surface empty |

Same family (**open leaf** law); different trigger (pin resolve vs authoring advance).

## Layer trace (earliest wrong layer)

Chip CTA → non-SSE send → `async_job_queued` **without poll** (host FE) **and/or**
worker writes `succeeded` with `reply_len=0` and no blocks → user path silent.

Not owner steal. Not cold system-suggest miss (first sketch). **Hollow delivery after advance.**

## Classification

- [x] Plausible while state advanced without surface
- [x] Expressible as `open_surface` / `blocks_resolve` / `reply_nonempty` after
      `authoring_advance`
- [x] Cognition pin-driven (`read_kind=authoring_advance`)
- [x] Host path seals product transport (chip poll + worker empty seal)

## Expected law (observation)

| Field | Expected (healthy) | Observed (bug) |
|-------|--------------------|----------------|
| exclusive_owner | `authoring` | may still be authoring |
| phase | `ir_review` | may be ir_review |
| extras.blocks_resolve | true | false |
| extras.open_surface | true | false |
| extras.reply_nonempty | true | false |
| observed_outcome | `ir_review_open` | `async_succeed_empty` |

## Twists (scenario steps)

1. User opens system-suggest sketch for a domain (`system_suggest_open`).
2. Sketch open succeeds (`sketch_produced`, open surface).
3. User advances to structured review (`authoring_advance` / Continue chip).
4. Host must open IR/review surface — not empty success.

## Artifacts

- [x] `script.json` (required)
- [x] Red: `MiniChatApp(bug="hollow_async_advance")`
- [x] Green: healthy mini-app
- [x] `CATALOG.md` row
- Host path seal: `test_hollow_async_advance_seal` (FE chip poll + IR lead + worker)

## Fix notes (portable)

- Advance delivery: non-empty reply and/or blocks; never empty succeed
- Host FE: chip paths must poll `async_job_queued` (not sync-only `res.answer`)
- Host worker: seal empty result before status=succeeded

## Notes

Demo uses generic `authoring` kind + `authoring_advance` read_kind. Hosts map to
drafting proceed / IR gate chips. Do not bake product button labels into the law.
