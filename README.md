# Conjecture Behaviour Runner

**Prove multi-turn behaviour under messy, auto-generated software** —  
not “did the assistant say this exact sentence?”

Vibe-coded and auto-coded programs don’t fail like classical apps. They accrete
**unknown pathways**: probabilistic specs, half-scoped features, dynamic scope,
shifting requirements, and code nobody deliberately designed. Chat and agents
make that worse across turns. **Conjecture** is a harness for pinning what
*must* stay true when you cannot inventory every path in advance.

Built by [Bot0.ai](https://bot0.ai). First cut ships with a deep pairing to the  
[Conversation Control Plane](https://github.com/walidnegm/conversation-control-plane)  
(turn ownership / pins) — but the *idea* is broader than one product surface.

| | |
|---|---|
| **GitHub** | [github.com/walidnegm/conjecture-behaviour-runner](https://github.com/walidnegm/conjecture-behaviour-runner) |
| **Import** | `conjecture_behaviour_runner` |
| **CLI** | `conjecture` / `python -m conjecture_behaviour_runner` |
| **License** | MIT · **Status** | Alpha (0.1) |

---

## Why we created this

### The world Conjecture assumes

Modern agentic products are rarely a closed, fully-specified state machine:

| Reality of vibe / auto coding | What that does to testing |
|-------------------------------|---------------------------|
| Specs are **probabilistic** (“make it handle handoff”) | Paths appear that no ticket named |
| **New requirements** land mid-build | Old happy-path tests still green |
| **Weak or dynamic scoping** | Features reach states authors never mapped |
| **Changing requirements** week to week | String goldens rot or get rewritten to pass |
| Code **generated faster than reviewed** | Unknown branches, silent fallthroughs, dual writers |
| Multi-turn chat on top | Failures show up as *wrong owner*, *lost pin*, *wrong outcome* — not typos |

You cannot unit-test “everything” when you do not know the full path set. You
*can* script **behaviour envelopes**: after these turns, with this cognition
pinned, **these invariants must hold** and **these outcomes are allowed**.

### What string-match and snapshot evals miss

| What users hit | What “exact reply” tests miss |
|----------------|------------------------------|
| A detour steals an in-flight multi-turn task | Reply still “sounds helpful” |
| Identity flips mid-dialogue (ambient pin hijack) | No golden sentence fails |
| Continue restarts a flow instead of staying mid-flight | One-turn snapshot still passes |
| Unknown branch after a generated refactor | No test ever named that branch |
| Scope drift (“it also does X now”) | Prose tests update; contracts don’t |

Those failures live in **behaviour, ownership, and allowed outcomes** — not
prose. Pinning assistant text is brittle and **does not** catch them.

### What we built

**Conjecture** scripts **turns + structured cognition pins**, runs them through
a **host adapter** (your control plane / ledger / system under test), and checks
**invariants** (owner, pin present/equals, extras, allowed outcomes, …).
Cognition can be **stubbed or frozen** so CI stays deterministic while the
system under test still has to behave correctly.

The first deep binding is the **Conversation Control Plane** (sole-continue,
detour supersede, pin-over-ambient). That is a *reference domain*, not the
whole thesis.

> **One-line reason:** *When code and scope are generated and incomplete, you
> cannot prove “all paths.” You prove the behaviour that must not break when
> paths appear anyway — across turns, without string-matching chat.*

---

## What it is (and is not)

### It is

- A **portable multi-turn behaviour harness** for agentic / auto-coded systems
- A way to pin **invariants and allowed outcomes** when path inventories are incomplete
- A **standard invariant library** so adapters prove real checks, not only `always_true`
- An optional binding to the **Conversation Control Plane** with three **portable goldens**
- A **host adapter protocol** so *your* ledger or app control layer can plug in

### It is not

- A claim that every product must use Bot0’s control plane (that pairing is the first cut)
- A full product suite or private monorepo goldens
- A free live-LLM soak on every PR (default is stub/freeze)
- A complete path-coverage tool (it does not discover unknown code; it **guards contracts** when unknowns appear)
- A second agent runtime — it **evaluates** behaviour; it does not replace your agents

---

## How it works

```text
  You write a ConjectureScript
       (turns · CognitionPins · invariants · allowed outcomes)
                    │
                    ▼
              run_script(...)
                    │
     stub / freeze pin  ──►  no free LLM required
                    │
                    ▼
         ControlPlaneAdapter
           apply_effect  ·  observe_turn  ·  check_invariant
                    │
                    ▼
     Pass / fail with structured failures (not string diff)
```

| Piece | Role |
|-------|------|
| **Script** | Multi-turn dialogue recipe: what the user says, what cognition is pinned, what must hold |
| **Cognition pin** | Portable labels (`task_intent`, …) — **not** free-text NL; host product flags go in `extras` |
| **Adapter** | Your bridge to a real control plane or ledger |
| **Invariants** | e.g. `exclusive_owner`, `pin_equals`, `extra_true` (`blocks_resolve`) |

**Cognition modes:** `stub` (default) · `freeze` · `record` · `local` · `cloud`  
Slice 0 focuses on **stub/freeze** so the suite stays CI-safe.

---

## Quickstart

```bash
git clone https://github.com/walidnegm/conjecture-behaviour-runner.git
cd conjecture-behaviour-runner
pip install -e ".[dev]"
pytest tests/ -q
python examples/minimal_script.py    # shape smoke (null adapter)
# or: python -m conjecture_behaviour_runner.cli --demo
```

### Prove real control-plane behaviour (recommended)

```bash
pip install -e ".[dev,control-plane]"
python examples/control_plane_goldens.py
```

Expected:

```text
[PASS] sole_continue_owns_the_turn   — continue stays owned; no re-resolve
[PASS] detour_supersedes_stream      — a detour hands the turn to the front door
[PASS] pin_survives_ambient_last_read — ledger pin beats ambient last_read_*
```

Those three goldens are the **credibility demo**: the package evaluates a real companion contract, not only packaging smoke.

### Minimal script shape

```python
from conjecture_behaviour_runner import (
    LlmMode,
    CognitionPin,
    DialogueTurn,
    InvariantSpec,
    ConjectureScript,
    run_script,
    NullControlPlaneAdapter,  # smoke only — use a real adapter to prove ownership
)

script = ConjectureScript(
    script_id="demo_continue",
    description="sole-continue owns the turn",
    conversation_id="conv_demo",
    turns=[
        DialogueTurn(
            user_text="continue with the estimate",
            pin=CognitionPin(task_intent="continue", reason="stub"),
            invariants=[InvariantSpec(kind="always_true")],  # null adapter
        ),
    ],
)
result = run_script(script, adapter=NullControlPlaneAdapter(), llm_mode=LlmMode.STUB)
assert result.passed, result.failures
```

For real checks, subclass `BaseControlPlaneAdapter` or use  
`contrib.control_plane.ControlPlaneStreamAdapter` (extra `[control-plane]`).

---

## First deep pairing: ownership + proof

Slice 0’s deepest example is conversational **turn ownership** — because that is
where vibe-coded multi-agent products fail most loudly. The same harness shape
applies anywhere you can **observe** structured state after a turn.

| Package | Question it answers |
|---------|---------------------|
| [conversation-control-plane](https://github.com/walidnegm/conversation-control-plane) | **Who owns this turn?** (ledger, sole-continue, pins, gates) |
| **conjecture-behaviour-runner** (this repo) | **Did the behaviour contract still hold after N turns?** (scripts + invariants) |

```text
        Conjecture Behaviour Runner
     scripts · pins · invariants
     (broader: any multi-turn behaviour contract)
                 │
                 ▼
        ControlPlaneAdapter  (or your host adapter)
                 │
                 ▼
     conversation-control-plane  ·  your ledger  ·  your app state
```

Install both for the reference goldens:

```bash
pip install conjecture-behaviour-runner[control-plane]
# or: pip install -e ".[dev,control-plane]"
```

---

## Public API (0.1)

| Symbol | Role |
|--------|------|
| `LlmMode` | How cognition is obtained (`stub` / `freeze` / …) |
| `CognitionPin` | Portable turn labels; product flags → `extras` |
| `ConjectureScript` / `DialogueTurn` / `InvariantSpec` | Multi-turn script model |
| `ControlPlaneAdapter` | Protocol hosts implement |
| `NullControlPlaneAdapter` | Packaging smoke only |
| `BaseControlPlaneAdapter` / `check_standard_invariant` | Built-in invariant library |
| `run_script` | Pin-driven runner loop |
| `contrib.control_plane.ControlPlaneStreamAdapter` | Optional CCP binding |
| `contrib.control_plane.control_plane_golden_scripts` | Three portable goldens |

Details: [docs/conjecture-behaviour-runner.md](docs/conjecture-behaviour-runner.md) · [adapters/README.md](adapters/README.md) · [examples/](examples/)

### Experimental (not stable 0.1)

`conjecture_behaviour_runner.experimental` — scenario YAML / trajectory shapes for later surface drivers.  
May change without a major version bump. YAML loading needs:

```bash
pip install conjecture-behaviour-runner[scenarios]   # PyYAML
```

---

## Who this is for

- Teams shipping **agentic or LLM-shaped products** that grow by generation and iteration
- Anyone watching **evals pass** while **routing, ownership, or mid-flow state** fails in real chat
- Codebases where **scope is incomplete** and new paths keep appearing — and you need **contracts**, not full path inventories
- Hosts that use (or want) a **turn-ownership ledger** and a **CI-safe proof layer** (CCP goldens are the reference)

If your only test is “the assistant said something nice,” or your only defense is “we’ll write a unit test once we know the paths,” this package is the next step up.

---

## Status

**Alpha.** MIT. Surface is intentionally small.

The **thesis** (behaviour contracts under incomplete, auto-grown systems) is broader
than Slice 0. The **shipping surface** starts where we hurt most: multi-turn
control-plane invariants with stubbed cognition.

| Included | Meaning |
|----------|---------|
| Invariant library + base adapter | Real checks, fail-closed on unknown kinds |
| CCP stream adapter + 3 goldens | Reference pairing demonstrated in code |
| Generic cognition pin | Product flags stay in `extras` |
| Experimental scenario models | Quarantined; not the main 0.1 path |

**Not yet:** full path-faithful chat/SSE driver, distribution-over-N-runs monitoring,
Playwright-first corpus, non-conversation adapters as first-class examples (later slices).

---

## Contributing / monorepo note

This public tree is a **sanitized extract**. Deep product goldens and host-private scripts stay in the Bot0 application monorepo. PRs that keep the surface portable and leak-free are welcome.

---

Copyright © Bot0.ai / contributors. MIT.
