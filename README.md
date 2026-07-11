# Conjecture Behaviour Runner

**Behaviour-based evaluation for agentic, multi-turn systems** —  
**invariants and allowed outcomes**, not “the assistant said this exact sentence.”

Built by [Bot0.ai](https://bot0.ai) for a world of **vibe-coded and auto-coded** products:
unknown pathways, probabilistic specs, incomplete scope, and requirements that move
while the code is still being generated. You cannot inventory every path. You *can*
pin the **behaviour that must not break** when paths appear anyway.

| | |
|---|---|
| **GitHub** | [github.com/walidnegm/conjecture-behaviour-runner](https://github.com/walidnegm/conjecture-behaviour-runner) |
| **Import** | `conjecture_behaviour_runner` |
| **CLI** | `conjecture` |
| **License** | MIT · **Status** | Alpha — Slice 0 shipping |

> **Product name:** Conjecture Behaviour Runner (“Conjecture”).  
> **Slice 0 (now):** multi-turn **control-plane** invariants (stub/freeze cognition) + optional
> [Conversation Control Plane](https://github.com/walidnegm/conversation-control-plane) goldens.  
> **Later slices:** path-faithful chat drivers, scenario YAML + UI surfaces, corpus generation,
> distribution monitoring over live cognition.

---

## Why this product exists

### The software under test is not a closed machine

Agentic apps and auto-generated codebases fail differently from classical apps:

| Reality | Testing consequence |
|---------|---------------------|
| Specs are **probabilistic** (“handle handoff”) | Paths appear that no ticket named |
| **New / changing requirements** mid-build | Happy-path tests stay green |
| **Weak, dynamic, or missing scope** | States authors never mapped |
| Code **generated faster than reviewed** | Unknown branches, dual writers, silent fallthroughs |
| Multi-turn chat / agents on top | Failures = wrong *owner*, lost *identity*, illegal *outcome* — not typos |

String equality and one-shot snapshots answer the wrong question. They score **prose**.  
Production breaks in **behaviour**.

### What evaluation must pin instead

1. **Required invariants** — always true after a turn (e.g. exclusive owner, pin present, no phantom id)  
2. **Allowed outcomes** — envelope of legal behaviours (not one golden string)  
3. **Optionally distribution** — outcome rates over N runs when cognition is live  

That thesis comes from the full **behaviour-runner** product idea (scenario + trajectory +
modes + generation + monitoring). Conjecture is that product. The first *runner
implementation* that ships is where agentic products hurt first: **turn ownership and
mid-flow contracts** — not “browser click-assert-text” as the MVP.

---

## The full product shape (not only Slice 0)

```text
                    ┌──────────────────────────────────────┐
                    │   Conjecture Behaviour Runner         │
                    │   Scripts · scenarios · trajectories  │
                    │   Cognition modes · drivers · corpus  │
                    └──────────────────────────────────────┘
           ┌────────────────┬─────────────────┬──────────────────┐
           ▼                ▼                 ▼                  ▼
     Slice 0 (now)    Slice 1             Slice 2            Slice 3+
     Control-plane    Path-faithful       Scenario YAML      Generation:
     multi-turn       chat / SSE          + optional UI      code seed,
     invariants       driver              surface driver     explorer,
     (stub/freeze)                        (e.g. Playwright)  adversarial /
                                                             OOD · N-run
                                                             distribution
```

| Layer | Owns |
|-------|------|
| **Script / scenario** | Multi-turn steps, pins, expected contracts, allowed outcomes |
| **Cognition mode** | How labels are obtained: `stub` · `freeze` · `record` · `local` · `cloud` |
| **Driver** | How a step is applied (in-process adapter today; later chat/SSE; later UI) |
| **Trajectory** | Evidence of one run under one profile (distribution later) |
| **Corpus** | Goldens humans own; later code-bootstrap and adversarial generation |

**Slice 0 does not erase Slices 1–4.** It is the first *sealable* surface: prove
behaviour contracts with **deterministic cognition** and a **host adapter**, without
requiring a browser or free live LLM on every CI run.

---

## What ships today (0.1 / Slice 0)

- Portable **script model** + **`run_script`**
- **Cognition pins** (portable labels; host/product flags in `extras`)
- **Invariant library** (`BaseControlPlaneAdapter`, fail-closed unknown kinds)
- **Adapter protocol** — plug *your* control plane / ledger / app state
- Optional **Conversation Control Plane** binding + **3 portable goldens**
- **Experimental** scenario YAML / trajectory models (quarantined; later slices)

Companion for the ownership domain:  
[conversation-control-plane](https://github.com/walidnegm/conversation-control-plane)  
(*who owns the thread* — Conjecture *proves it still holds across turns*).

That pairing is the **reference domain**, not a claim that Conjecture *is only* a CCP test kit.

---

## Quickstart

```bash
git clone https://github.com/walidnegm/conjecture-behaviour-runner.git
cd conjecture-behaviour-runner
pip install -e ".[dev]"
pytest tests/ -q
python examples/minimal_script.py
```

### Reference goldens (control-plane behaviour)

```bash
pip install -e ".[dev,control-plane]"
python examples/control_plane_goldens.py
# sole-continue owns · detour supersedes · pin beats ambient last_read
```

### Minimal shape

```python
from conjecture_behaviour_runner import (
    LlmMode, CognitionPin, DialogueTurn, InvariantSpec,
    ConjectureScript, run_script, NullControlPlaneAdapter,
)

script = ConjectureScript(
    script_id="demo",
    description="stub smoke",
    conversation_id="conv_demo",
    turns=[
        DialogueTurn(
            user_text="continue",
            pin=CognitionPin(task_intent="continue"),
            invariants=[InvariantSpec(kind="always_true")],  # null adapter only
        ),
    ],
)
assert run_script(
    script, adapter=NullControlPlaneAdapter(), llm_mode=LlmMode.STUB
).passed
```

For real checks: implement `ControlPlaneAdapter` / subclass `BaseControlPlaneAdapter`,  
or use `contrib.control_plane.ControlPlaneStreamAdapter`.

More: [docs/conjecture-behaviour-runner.md](docs/conjecture-behaviour-runner.md) ·
[adapters/README.md](adapters/README.md) · [examples/](examples/)

---

## How a run works (Slice 0)

```text
  ConjectureScript (turns · pins · invariants · allowed outcomes)
                         │
                         ▼
                   run_script(...)
            stub/freeze cognition  →  CI-safe
                         │
                         ▼
              ControlPlaneAdapter (host)
           apply_effect · observe_turn · check_invariant
                         │
                         ▼
              structured pass / fail  (not string diff)
```

---

## Who this is for

- Teams shipping **agentic / LLM-shaped** products that grow by generation and iteration  
- Anyone whose **string evals pass** while **routing, ownership, or mid-flow state** fails  
- Codebases where **scope is incomplete** and new paths keep appearing  
- Hosts that need a **CI-safe behaviour contract layer** (CCP goldens = reference, not the ceiling)

---

## Explicit non-goals

- Replacing every unit test with multi-turn scripts  
- Live LLM on every PR by default  
- Browser as the *only* truth for ownership bugs (UI is a later *driver*, not the product)  
- Phrase laundry lists as “understanding” (cognition stays label-based; scripts pin outcomes)

---

## Status

**Alpha.** MIT.

| Horizon | Intent |
|---------|--------|
| **Product** | Full behaviour runner: scenarios, trajectories, drivers, generation, distribution |
| **Slice 0** | Control-plane multi-turn invariants + portable package + CCP goldens |
| **Next** | Path-faithful chat driver · scenario/UI surface · corpus · N-run distribution |

---

Copyright © Bot0.ai / contributors. MIT.
