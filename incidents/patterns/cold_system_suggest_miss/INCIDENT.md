# Incident: cold system-suggest miss (portable seed)

| Field | Value |
|-------|--------|
| **Slug** | `cold_system_suggest_miss` |
| **Failure mode (plain)** | Cold system-suggest miss |
| **Date** | 2026-07-13 |
| **Host** | path-faithful mini-app (public demo) · host dogfood Bot0 |
| **Conversation / ref** | Bot0 `conv_039432ce` (clinical-research starting point) |
| **Conjecture-class?** | yes (delivery leaf + multi-turn bind) |

## Symptom (what the user saw)

- User asked the system to invent a **first multi-step sketch** for a named domain
  (little or no process paste yet).
- Host answered as if they had asked to **structure empty material** ("paste more
  process…") or forgot the prior open on a short re-ask ("give me something to
  start with").
- Optional packaging contradiction: card listed steps yet claimed stages missing,
  or "improve" ideas named steps not on the sketch (host packaging leaf).

Planted bug id (mini-app): `cold_system_suggest_miss`.

## Portable law (vocabulary-independent)

**Cold open for a new multi-step activity where the user asks the system to invent
or sketch a first structure for a named domain (little or no body yet) must:**

1. Enter the **collaborative-authoring leaf** for that activity (not "finalize /
   structure empty seed").
2. **Produce a first structured sketch** when the ask is system-suggest.
3. On a **short re-ask** without restating the domain, **bind the prior open**
   (domain pin / authoring owner) — not amnesia / front door.
4. Packaging must not contradict the artifact (host extension; not required of
   this mini-app seed).

Product verbs ("create workflow", "draft_help", …) are **host examples**, not the law.

## Layer trace (earliest wrong layer)

UI → stream → router cognition (`structure empty` / wrong enum) → **authority
failed to force authoring leaf** → thin-structure refuse **or** history not bound
on insist.

Not owner steal. Not hollow inventory pin. **Wrong delivery leaf + multi-turn bind.**

## Classification

- [x] Plausible while delivery / bind law was wrong
- [x] Expressible as `exclusive_owner` + `active_kind` + `sketch_produced` + domain pin
- [x] Cognition pin-driven (`read_kind=system_suggest_open|system_suggest_insist`)
- [x] Host path seals product vocabulary separately

## Expected law (observation)

| Field | Expected (healthy) | Observed (bug) |
|-------|--------------------|----------------|
| exclusive_owner | `authoring` | `front_door` |
| active_kind | `authoring` | null |
| extras.sketch_produced | true | false |
| pin `domain_label` | set and sticky on re-ask | missing after insist |

## Twists (scenario steps)

1. User opens: system-suggest first sketch for a domain (cognition: `system_suggest_open`).
2. Host must open authoring + produce sketch + pin domain.
3. User short re-ask without domain (cognition: `system_suggest_insist`).
4. Host keeps authoring + domain + sketch — not front-door amnesia.

## Artifacts

- [x] `script.json` (required)
- [x] Red: `MiniChatApp(bug="cold_system_suggest_miss")`
- [x] Green: healthy mini-app
- [x] `CATALOG.md` row
- Host path seal: monorepo `test_greenfield_system_suggest_leaf_matrix` (product openers)

## Fix notes (portable)

- Shape / authority: cold system-suggest → authoring leaf, not structure-empty
- History bind: bare re-ask after open rebinds domain pin
- Host packaging: artifact-faithful gaps/ideas (host-only)

## Notes

Demo uses generic `authoring` kind and `domain_label` pin. Hosts map to drafting /
planning / campaign authoring as needed. Do not bake product wordlists into the seed.
