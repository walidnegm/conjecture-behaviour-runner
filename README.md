# Conjecture Behaviour Runner

*Behaviour-based multi-turn evaluation* for agentic systems — **invariants and allowed outcomes**, not string equality.

Reference implementation by [Bot0.ai](https://bot0.ai) · companion to the [Conversation Control Plane](https://github.com/walidnegm/conversation-control-plane)

| | |
|---|---|
| **GitHub** | [github.com/walidnegm/conjecture-behaviour-runner](https://github.com/walidnegm/conjecture-behaviour-runner) |
| **PyPI (future)** | `conjecture-behaviour-runner` |
| **Import** | `conjecture_behaviour_runner` |
| **CLI** | `conjecture` / `python -m conjecture_behaviour_runner` |

> **Pairing:** control plane = *who owns the turn*; Conjecture = *prove it across turns*.

### Quickstart

```bash
git clone https://github.com/walidnegm/conjecture-behaviour-runner.git
cd conjecture-behaviour-runner
pip install -e ".[dev]"
pytest tests/ -q
python examples/minimal_script.py               # null adapter (shape only)
# or: python -m conjecture_behaviour_runner.cli --demo
```

**Prove real behaviour** against the companion control plane (no DB, CI-safe):

```bash
pip install -e ".[dev,control-plane]"   # + conversation-control-plane
python examples/control_plane_goldens.py
# [PASS] sole_continue_owns_the_turn   — continue stays owned; no re-resolve
# [PASS] detour_supersedes_stream      — a detour hands the turn to the front door
# [PASS] pin_survives_ambient_last_read — ledger pin beats ambient last_read_* (A15)
```

```python
from conjecture_behaviour_runner import (
    LlmMode,
    CognitionPin,
    DialogueTurn,
    InvariantSpec,
    ConjectureScript,
    run_script,
    NullControlPlaneAdapter,
)

script = ConjectureScript(
    script_id="demo_continue",
    description="sole-continue owns the turn",
    conversation_id="conv_demo",
    turns=[
        DialogueTurn(
            user_text="continue with the estimate",
            pin=CognitionPin(task_intent="continue", reason="stub"),
            invariants=[
                # Use always_true with NullControlPlaneAdapter.
                # Real hosts check exclusive_owner / pins via ControlPlaneAdapter.
                InvariantSpec(kind="always_true"),
            ],
        ),
    ],
)
result = run_script(script, adapter=NullControlPlaneAdapter(), llm_mode=LlmMode.STUB)
assert result.passed, result.failures
```

Contract notes: [docs/conjecture-behaviour-runner.md](docs/conjecture-behaviour-runner.md)

---

## Why this exists

LLM and agentic evals fail when they pin **prose**. Real failures live in **behaviour**:

- Wrong turn owner (a detour steals an in-flight multi-turn task)
- Lost entity pin across turns
- Detour vs continue vs capability vs adversarial probe

Conjecture pins **required invariants** + **allowed outcomes** (and later, distributions over live cognition).

### First cut (Slice 0)

Multi-turn **control-plane** invariant testing — stub/freeze cognition by default (CI-safe). Hosts bind a `ControlPlaneAdapter` to their ledger or to the [Conversation Control Plane](https://github.com/walidnegm/conversation-control-plane) package.

Later slices: path-faithful chat drivers, optional UI surface, corpus generation, distribution monitoring.

---

## Architecture

```text
        Conjecture Behaviour Runner
     scripts · modes · trajectories
                 │
     ┌───────────┼───────────┐
     ▼           ▼           ▼
  stub/freeze  host LLM    later: chat/SSE / UI
     │
     ▼
  ControlPlaneAdapter  ──►  conversation-control-plane
                            (or your host’s ledger)
```

---

## Public API (0.1)

| Symbol | Role |
|---|---|
| `LlmMode` | `stub` / `freeze` / `record` / `local` / `cloud` |
| `CognitionPin` | Portable cognition labels (`task_intent`, …); host flags in `extras`; entity ids on `TurnObservation.pins` |
| `ConjectureScript` / `DialogueTurn` / `InvariantSpec` | Multi-turn script model |
| `ControlPlaneAdapter` | Protocol hosts implement |
| `NullControlPlaneAdapter` | Packaging smoke only |
| `BaseControlPlaneAdapter` / `check_standard_invariant` | Built-in invariant library (owner, pin, extras, …) |
| `run_script` | Portable pin-driven loop |
| `contrib.control_plane.ControlPlaneStreamAdapter` | Optional CCP binding (extra `[control-plane]`) |
| `contrib.control_plane.control_plane_golden_scripts` | Three portable sole-continue / detour / pin goldens |

See `examples/` and `adapters/README.md`.

---

## Companion runtime

- [conversation-control-plane](https://github.com/walidnegm/conversation-control-plane) — turn ownership, sole-continue, multi-turn stream contract

```bash
pip install conjecture-behaviour-runner[control-plane]
# or editable: pip install -e ".[dev,control-plane]"
# experimental YAML scenarios only:
# pip install -e ".[scenarios]"
```

### Experimental (not stable 0.1 API)

`conjecture_behaviour_runner.experimental` — Scenario YAML models + trajectory
shapes (quarantined so they are not a second public scenario framework). May
change without a major version bump.

---

## Status

**Alpha.** MIT. Portable surface is intentional and small. Slice 0 includes a
real invariant library, a CCP-binding adapter with portable goldens, a **generic**
`CognitionPin` (product flags → `extras`), and quarantined experimental
scenario/trajectory modules. Host product-private scripts stay out of this package.
