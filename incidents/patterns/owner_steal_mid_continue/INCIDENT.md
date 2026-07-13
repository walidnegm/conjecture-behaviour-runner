# Incident: owner steal mid continue (portable seed)

| Field | Value |
|-------|--------|
| **Slug** | `owner_steal_mid_continue` |
| **Date** | 2026-07-11 |
| **Host** | path-faithful mini-app (public demo) |
| **Conjecture-class?** | yes |

## Symptom

Continue turn mid-flight can still sound fine while `exclusive_owner` reports
`front_door` — classic steal. Planted bug id: `owner_steal`.

## Expected law

| Field | Expected | Observed (bug) |
|-------|----------|----------------|
| exclusive_owner | host mid-flight kind (demo: `cost_out`) | `front_door` |
| pin | present (demo: `workflow_id`) | may still hold — owner is the break |
| task_intent pin | `continue` | `continue` |

## Notes

Demo vocabulary only. Port by replacing `cost_out` / `workflow_id` with your ledger
types. Prove FAIL with `MiniChatApp(bug="owner_steal")`; PASS with healthy app.

See also: `conjecture path-faithful --prove-bugs`.
