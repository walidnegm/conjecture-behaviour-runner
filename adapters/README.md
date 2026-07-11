# Adapters (Driver + Observer)

Adapters are **Driver plugins** under a **runner**. They do not replace Conjecture Scenario,
Conjecture Script, or the Verifier. Full stack: [docs/README.md](../docs/README.md).

```text
  Conjecture Script
        │  control-plane runner (run_script) today
        ▼
  Adapter (Driver + Observer)  ──►  Real application
        │
        ▼
  TurnObservation  ──►  VERIFIER  ──►  pass/fail
        │
  OBSERVED TRAJECTORY (evidence of this run)
```

The public harness talks to a host through `ControlPlaneAdapter`
(`conjecture_behaviour_runner.protocol`).

| Binding | Status |
|---|---|
| **Null** (`NullControlPlaneAdapter`) | Packaging smoke — does not verify host invariants |
| **Conversation Control Plane** (`contrib.control_plane.ControlPlaneStreamAdapter`) | **Shipped** — multi-turn stream contract (sole-continue, phase-gated resolve, pin identity), no DB. Needs `pip install conjecture-behaviour-runner[control-plane]` |
| **Path-faithful mini-app** (`path_faithful.MiniAppAdapter`) | **Shipped** — Act via `handle()`; planted bugs for E2E |
| **Your own ledger / LangGraph / Temporal / Crew** | Subclass `BaseControlPlaneAdapter`; implement `apply_effect` + `observe_turn` |

Built-in verifier kinds (`conjecture_behaviour_runner.invariants`, free via
`BaseControlPlaneAdapter`):

- `exclusive_owner` / `owner_not` — who owns this turn  
- `active_kind` / `kind_equals` — active task kind  
- `pin_present` / `pin_absent` / `pin_equals` / `pin_key_missing` — entity identity  
- `observed_outcome` — landing code (required if Script declares `allowed_outcomes`)  
- `extra_equals` / `extra_true` / `extra_false` / `extra_missing` — host flags (e.g. `blocks_resolve`)  
- `always_true` — no-op (null adapter demos)  

Trajectory-level kinds: see `temporal.py` / CBR-SPEC §4.1.

### Cognition pin vs entity pin

- **`CognitionPin`** — portable turn labels (`task_intent`, …). Host-private flags in **`extras`**.  
- **`TurnObservation.pins`** — ledger **entity identity** after arrange/Act (e.g. `workflow_id`).  

### Arrange vs Act

- `apply_effect` — **arrange** seed state for the test  
- `observe_turn` — **Act** on the real host surface, then project observation  

Do not publish host-private goldens into this repository. Keep host-specific Scripts in
your app repo; depend on this package for harness + verifier only.

See: [AGENTS.md](../AGENTS.md) · [examples/e2e_multi_turn.py](../examples/e2e_multi_turn.py) · [CBR-SPEC](../docs/SPEC.md).
