# Adapters

The public harness talks to a host through `ControlPlaneAdapter`
(`conjecture_behaviour_runner.protocol`).

| Binding | Status |
|---|---|
| **Null** (`NullControlPlaneAdapter`) | Packaging smoke — does not verify product invariants |
| **Your ledger / Conversation Control Plane** | Implement `apply_effect`, `observe_turn`, `check_invariant` |

Typical invariant kinds hosts support:

- `exclusive_owner` — who owns this turn  
- `kind_equals` / `owner_not` — active task kind  
- `pin_present` — typed entity id still bound  
- `always_true` — no-op (null adapter demos)

Do not publish product-private goldens into this repository. Keep host-specific
scripts in your application repo; depend on this package for the harness only.
