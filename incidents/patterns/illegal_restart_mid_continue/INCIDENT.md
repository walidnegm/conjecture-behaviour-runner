# Incident: illegal restart mid continue (portable seed)

| Field | Value |
|-------|--------|
| **Slug** | `illegal_restart_mid_continue` |
| **Date** | 2026-07-11 |
| **Host** | path-faithful mini-app (public demo) |
| **Conjecture-class?** | yes |

## Symptom

Continue turn mid-flight can still sound fine while the **active task is wiped**
(greenfield restart) — owner and pin both gone.

Planted bug id: `illegal_restart`.

## Expected law

| Field | Expected | Observed (bug) |
|-------|----------|----------------|
| exclusive_owner | host mid-flight kind (demo: `cost_out`) | `front_door` / none |
| active_kind | still mid-flight kind | cleared |
| pin | present (demo: `workflow_id`) | missing |
| task_intent pin | `continue` | `continue` |

## Notes

Demo vocabulary only. Port by replacing `cost_out` / `workflow_id` with your ledger
types. Prove FAIL with `MiniChatApp(bug="illegal_restart")`; PASS with healthy app.

See also: `conjecture path-faithful --prove-bugs`.
