# Incident: mid cost-out + recommend grammar without Stay/Leave

| Field | Value |
|-------|--------|
| **Slug** | `cost_out_recommend_no_leave` |
| **Date** | 2026-07-21 |
| **Host** | Bot0 monorepo (`conv_019aae41`) |
| **Conjecture-class?** | yes |

## Symptom

User mid **agent pricing** (`active_task.kind=cost_out`, phase `sizing`) says
**“any recommendations?”**. Host either:

1. Silent re-loop of sizing (same estimate card), or  
2. Free-form tip list (product voice failure),

instead of **Stay / Leave** on the cost stream.

## Expected law (SDK §2.1 + A18)

| Field | Expected |
|-------|----------|
| exclusive_owner (offer turn) | `cost_out` (sole-continue holds) |
| host leaf | `cost_out_recommend_fork` (Stay/Leave chips) |
| Stay | cost_out remains; fork pending clear |
| Leave | abandon cost_out (`active_task` cleared) then recommend entry |

## Host seal

| Artifact | Role |
|----------|------|
| `host: cost_out recommend fork leaf` | Stay/Leave product leaf |
| Conjecture script `cost_out_recommend_fork_stay_leave` | Multi-turn golden |
| `host unit ratchet for cost_out recommend fork` | Unit ratchet |

## Prove

```bash
conjecture --script <host_script_id>  # host golden for stay/leave fork
```

Port: replace `cost_out` / recommend grammar with your sole-continue kind +
competing product leaf; require explicit leave before foreign stream open.
