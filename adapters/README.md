# Adapters

The public harness talks to a host through `ControlPlaneAdapter`
(`conjecture_behaviour_runner.protocol`).

| Binding | Status |
|---|---|
| **Null** (`NullControlPlaneAdapter`) | Packaging smoke — does not verify host invariants |
| **Conversation Control Plane** (`contrib.control_plane.ControlPlaneStreamAdapter`) | **Shipped** — runs the real CCP multi-turn stream contract (sole-continue ownership, phase-gated resolve, pin identity) with no DB. Needs `pip install conjecture-behaviour-runner[control-plane]` |
| **Your own ledger** | Subclass `BaseControlPlaneAdapter`, implement `apply_effect` + `observe_turn`; `check_invariant` is inherited |

Built-in invariant kinds (`conjecture_behaviour_runner.invariants`, free via
`BaseControlPlaneAdapter`):

- `exclusive_owner` / `owner_not` — who owns this turn
- `active_kind` / `kind_equals` — active task kind
- `pin_present` / `pin_absent` / `pin_equals` — typed entity id still bound
- `observed_outcome` — landed in an allowed outcome
- `extra_equals` / `extra_true` / `extra_false` — adapter-projected facts (e.g. `blocks_resolve`, `preferred_workflow_id`)
- `always_true` — no-op (null adapter demos)

Worked binding + three golden scripts: `examples/control_plane_goldens.py`
(`control_plane_golden_scripts()`), ratcheted in `tests/test_control_plane_adapter.py`.

### Cognition pin vs entity pin

- **`CognitionPin`** — portable turn labels (`task_intent`, `discovery_kind`, …).
  Host-specific router flags go in **`extras`** (do not add host-private fields to the
  public dataclass).
- **`TurnObservation.pins`** — ledger **entity identity** after `apply_effect`
  (keys are host/control-plane defined; CCP uses e.g. `workflow_id`).

Do not publish host-private goldens into this repository. Keep host-specific
scripts in your application repo; depend on this package for the harness only.
