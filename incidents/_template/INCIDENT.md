# Incident: \<short title\>

| Field | Value |
|-------|--------|
| **Slug** | `patterns/<slug>/` |
| **Date** | YYYY-MM-DD |
| **Host** | e.g. Bot0 / external app name |
| **Conversation / ref** | `conv_…` or ticket |
| **Conjecture-class?** | yes / no (if no, stop — fix elsewhere) |

## Symptom (what the user saw)

- Reply looked: …
- Broken underneath: wrong owner / dropped pin / illegal restart / wrong kind write / …

## Layer trace (earliest wrong layer)

UI → stream → chat entry → router → **ledger write / kind submit** → specialist → …

Mark where behavior first diverged from the **ledger contract**.

## Classification

- [ ] Looks fine in chat, state law wrong
- [ ] Expressible as owner · kind · pin · outcome invariants
- [ ] Cognition can be pinned/frozen for CI
- [ ] Ledger SDK already defines the correct rule (implementation bug, not missing SDK)

If the SDK is incomplete, fix/test the SDK first; do not only accumulate a soft golden.

## Expected law (host vocabulary)

| Field | Expected | Observed (bug) |
|-------|----------|----------------|
| exclusive_owner / active_kind | e.g. `invoice_intake` | e.g. `front_door` |
| pin key → value | e.g. `invoice_id` → `inv_1` | missing / wrong |
| blocks_resolve / phase | … | … |
| task_intent pin (CI) | `continue` | … |

## Twists (scenario steps)

1. …
2. …

## Artifacts

- [ ] `scenario.yaml` (optional)
- [ ] `script.json` (required)
- [ ] Red run (FAIL) on broken path
- [ ] Green run after fix
- [ ] `CATALOG.md` row

## Fix notes

What sealed the contract (code path, not copy-only): …
