# Conjecture Behaviour Runner

| Field | Value |
|---|---|
| **Status** | Alpha (0.1) — Slice 0 portable surface |
| **One line** | Behaviour-based multi-turn evaluation — **invariants and allowed outcomes**, not string equality |
| **First cut** | Multi-turn **conversation control-plane** invariant testing (stub/freeze cognition) |
| **Package** | `conjecture-behaviour-runner` · import `conjecture_behaviour_runner` |
| **Companion** | [Conversation Control Plane](https://github.com/walidnegm/conversation-control-plane) |

---

## 1. Problem

LLM and agentic systems fail in **behaviour space**:

- Wrong *owner* of the turn (a knowledge detour steals an in-flight multi-turn task)
- Lost *entity pin* / identity across turns
- Detour vs continue vs capability vs adversarial probe — different user styles, same contracts
- Pass/fail cannot be “assistant said exactly this sentence”

Evaluation must pin:

1. **Required invariants** (always true — e.g. exclusive turn owner, pin present, no phantom id)
2. **Allowed outcomes** (envelope of legal behaviours)
3. Optionally **distribution** (outcome rates over N runs when cognition is live)

---

## 2. Architecture

```text
        Conjecture Behaviour Runner
     scripts · modes · trajectories
                 │
     ┌───────────┼───────────┐
     ▼           ▼           ▼
  stub/freeze  host LLM    later: chat/SSE / UI drivers
     │
     ▼
  ControlPlaneAdapter  ──►  conversation-control-plane
                            (or your host ledger)
```

| Layer | Owns |
|---|---|
| **Script** | Multi-turn steps, pins, expected owner, allowed outcomes |
| **Cognition mode** | How labels are obtained: `stub` · `freeze` · `record` · `local` · `cloud` |
| **Adapter** | Host binding: apply ledger effects, observe exclusive owner / pins, check invariants |
| **Trajectory** (later UI surface) | Evidence of one run under one profile |

**Invariant:** scripts assert **control-plane contracts** (see companion SDK). They do not invent a second product model.

Companion runtime contract: [conversation-control-plane](https://github.com/walidnegm/conversation-control-plane) — multi-turn stream / sole-continue / turn ownership.

---

## 3. Slice plan

| Slice | What |
|---|---|
| **0 (now)** | Portable script model, pin-driven harness, `ControlPlaneAdapter` protocol, null adapter smoke, **standard invariant library** (`BaseControlPlaneAdapter`), **CCP stream adapter** + 3 portable goldens (`contrib.control_plane`) |
| **1** | Path-faithful host chat / SSE driver (host-supplied) |
| **2** | Optional scenario YAML + UI harness (Playwright or other) as *one* surface driver |
| **3** | Corpus generation (code seed, user styles, detours, adversarial / OOD) |
| **4** | Distribution monitoring when cognition is live |

Deterministic UI (click → assert text) stays outside this framework.

---

## 4. Cognition modes

| Mode | Cognition | Proves |
|---|---|---|
| `stub` (default) | Pin on the turn | Control-plane invariants only — CI-safe |
| `freeze` / `record` | Recorded pin JSON | Replay / capture |
| `local` / `cloud` | Host routes a real bounded classifier | Enum parity + same invariants (host provides pins or driver) |

The portable core is **pin-driven**. It does not call your LLM factory; hosts supply pins or a richer driver.

---

## 5. Public API (0.1)

```python
from conjecture_behaviour_runner import (
    LlmMode,
    CognitionPin,
    DialogueTurn,
    InvariantSpec,
    LedgerEffect,
    ConjectureScript,
    ControlPlaneAdapter,   # Protocol
    NullControlPlaneAdapter,
    run_script,
)
```

Implement `ControlPlaneAdapter` against your ledger (or the Conversation Control Plane package) to check real `exclusive_owner` / pin invariants. The null adapter is for packaging smoke only.

Scenario YAML models and trajectory shapes live under
`conjecture_behaviour_runner.experimental` (unstable; not part of the 0.1 API).
YAML loading needs `pip install conjecture-behaviour-runner[scenarios]` (PyYAML).
Slice 0 scripts do not use them.

---

## 6. Explicit non-goals

- Replacing all unit tests with multi-turn scripts  
- Live LLM on every PR by default  
- Browser as the only truth for control-plane bugs  
- Phrase laundry lists as scenario generators (cognition stays label-based; scripts pin outcomes and owners)

---

## 7. License & status

MIT. Alpha surface is intentional and small. Host adapters and product-specific goldens are out of scope for this package until documented as portable examples.
