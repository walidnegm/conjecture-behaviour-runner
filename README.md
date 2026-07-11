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
python examples/minimal_script.py
# or: python -m conjecture_behaviour_runner.cli --demo
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
| `CognitionPin` | Structured router/classifier labels for a turn |
| `ConjectureScript` / `DialogueTurn` / `InvariantSpec` | Multi-turn script model |
| `ControlPlaneAdapter` | Protocol hosts implement |
| `NullControlPlaneAdapter` | Packaging smoke only |
| `run_script` | Portable pin-driven loop |

See `examples/` and `adapters/README.md`.

---

## Companion runtime

- [conversation-control-plane](https://github.com/walidnegm/conversation-control-plane) — turn ownership, sole-continue, multi-turn stream contract

Optional extra (when both are on PyPI): `pip install conjecture-behaviour-runner[control-plane]`

---

## Status

**Alpha.** MIT. Portable surface is intentional and small. Product-specific goldens and host adapters are not part of this package until published as portable examples.
