# Conjecture Behaviour Runner

**Behaviour-based evaluation for agentic, multi-turn systems** —  
**invariants and allowed outcomes**, not “the assistant said this exact sentence.”

Built by [Bot0.ai](https://bot0.ai).

Vibe-coded and auto-coded programs **don’t fail like classical apps**. They accrete
**unknown pathways**. Chat and agents make that worse across turns. **Conjecture** is
a harness for pinning what **must stay true** when you **cannot inventory every path
in advance**.

| What accrues in vibe / auto-coded systems | Why classical tests miss it |
|-------------------------------------------|------------------------------|
| **Probabilistic specs** (“make it handle handoff”) | Paths appear that no ticket named |
| **Half-scoped features** | Code reaches states the Epic never closed |
| **Dynamic / shifting scope** | Requirements move while code is still generating |
| **Changing requirements** week to week | String goldens rot or get rewritten to “pass” |
| **Code nobody deliberately designed** | Unknown branches, dual writers, silent fallthroughs |
| **Chat + multi-turn agents on top** | Failures = wrong *owner*, lost *pin*, illegal *outcome* — not typos |

| What Conjecture pins instead | Meaning |
|------------------------------|---------|
| **Required invariants** | Must hold after the turn regardless of wording |
| **Allowed outcomes** | Envelope of legal landings — not one golden sentence |
| **Optional distribution** | Rates over N runs when cognition is live (later slices) |

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
> **Objective is not skinned down** because the first phase is simpler — we still build out
> ODD/scope, modalities, drivers, and distribution.

### Where this sits (not Collinear, not Playwright)

Conjecture is closer to **scenario construction in autonomous driving** (e.g. **CARLA** /
SOTIF-style ODD work) than to LLM product-eval platforms or browser E2E tools.

| Approach | What it optimizes for | How Conjecture differs |
|----------|----------------------|-------------------------|
| **Playwright / Cypress-style E2E** | Deterministic UI: click → wait → assert fixed text/DOM | UI can be *one driver later*. The product is **behaviour contracts** (outcomes + invariants), not click-assert-text as the definition of “pass.” |
| **LLM eval / simulation labs** (e.g. multi-turn agent sandboxes for model improvement) | Score or train the **model**: task success, rubrics, synthetic users, RL signal | We evaluate the **host system’s contracts** (ownership, pins, refusal, mid-flow state) under incomplete, auto-grown code — not primarily model leaderboard quality. |
| **CARLA-style scenario building** | Scenarios + edge cases under an **ODD**; ground truth from the world / maps / sensors; generate stress and out-of-domain probes | **Closest analogy.** Declare the claimed domain (ODD/scope), author scenarios from **ground truth** (code contracts, real traffic, explorer), generate **edge conditions**, pin **what must hold** when the world is nondeterministic. |
| **Conjecture (this package)** | Multi-turn **behaviour envelopes** for agentic products built under vibe/auto coding | Scenario + trajectory + optional edge generation from ground-truth collection; first sealable surface is control-plane mid-flow contracts. |

**In short:** Playwright automates the browser. Many eval platforms stress the **model**.  
Conjecture is for **scenario- and edge-driven behaviour contracts** on systems whose path set
is incomplete — the same *kind of problem* AV stacks face with ODD and edge cases, applied
to agentic product control flow.

---

## Why this product exists

### The software under test is not a closed machine

The table above is the core claim. In short: **prose tests score wording; production
breaks in behaviour.** String equality and one-shot snapshots answer the wrong question.

### What evaluation must pin instead

String match and one-shot snapshots miss **control flow, state identity, and legal
landings** — even when the wording looks fine. So evaluation pins:

1. **Required invariants** — what must still be true after the turn  
2. **Allowed outcomes** — envelope of legal landings (not one golden string)  
3. **Optionally distribution** — rates over N runs when cognition is live  

That is the full **behaviour-runner** product idea (scenario + trajectory + modes +
generation + monitoring). Conjecture is that product. Slice 0 is the first sealable
vertical — not a redefinition as “browser click-assert-text” or “one product’s unit tests.”

**Slice 0 is simpler. The product objective is not.** We still build out ODD/scope,
modalities, UI drivers, corpus generation, and N-run distribution.

### Behaviour-driven testing and ODD (methodology we keep)

Classical tests often pin **exact outputs**. Behaviour-driven evaluation pins:

| Idea | Meaning |
|------|---------|
| **Allowed outcomes** | Legal landings for a step/turn (more than one is fine) |
| **Required invariants** | Must hold **no matter which** allowed outcome occurred |
| **Trajectory** | One observed run of a scenario under one profile |
| **Distribution** (later) | Rates across N trajectories when cognition is live |

Without those, you cannot tell “happy path passed” from “happy path passed by accident.”

**ODD (Operational Design Domain)** — from ISO 21448 / SOTIF practice — is the
**claimed input boundary** for a scenario class: what the system says it handles.
It is **metadata on the claim**, not a single test case.

| Field (plain language) | Role |
|------------------------|------|
| `in_scope` | Supported — should handle |
| `out_of_scope` | Unsupported — refuse / degrade gracefully |
| `expected_refusal` | Probes that must be rejected |

**ODD vs adversarial** (do not conflate):

- **ODD / scope** = specification of the boundary  
- **Adversarial generation** = technique that *uses* the boundary (in-scope stress + out-of-scope refusal)  

Four **corpus modalities** still belong to the product: code-based · user-watching ·
agent-plays-the-game · adversarial. Slice 0 is mostly code-based control-plane contracts;
the rest is **build-out**, not cancelled vision.

Full write-up: [docs/conjecture-behaviour-runner.md](docs/conjecture-behaviour-runner.md) §1.1.

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
- Anyone whose **output looks fine** while **flow, identity, or legal outcomes** fail  
- Codebases where **scope is incomplete** and new paths keep appearing  
- Hosts that need a **CI-safe behaviour contract layer** (reference goldens are examples, not the ceiling)

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
