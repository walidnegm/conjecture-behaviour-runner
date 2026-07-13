# Incident: drop pin mid continue (portable seed)

| Field | Value |
|-------|--------|
| **Slug** | `drop_pin_mid_continue` |
| **Date** | 2026-07-11 |
| **Host** | path-faithful mini-app (public demo) |
| **Conjecture-class?** | yes |

## Symptom

Continue turn mid-flight can still sound fine while the **entity pin** is gone
(`workflow_id` missing). Owner may still look correct — identity is the break.

Planted bug id: `drop_pin`.

## Expected law

| Field | Expected | Observed (bug) |
|-------|----------|----------------|
| exclusive_owner | host mid-flight kind (demo: `cost_out`) | may still be `cost_out` |
| pin | present and stable (demo: `workflow_id` = `wf_1`) | missing / cleared |
| task_intent pin | `continue` | `continue` |

## Notes

Demo vocabulary only. Port by replacing `cost_out` / `workflow_id` with your ledger
types. Prove FAIL with `MiniChatApp(bug="drop_pin")`; PASS with healthy app.

See also: `conjecture path-faithful --prove-bugs`.
