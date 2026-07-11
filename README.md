# Conjecture Behaviour Runner

**Prove multi-turn agent behaviour** — who owns the turn, what stays pinned, what outcomes are allowed — **without** scoring chat by string match.

Built by [Bot0.ai](https://bot0.ai) as the **test kit** that pairs with the  
[Conversation Control Plane](https://github.com/walidnegm/conversation-control-plane)  
(*who owns the thread* → *prove it still holds across turns*).

| | |
|---|---|
| **GitHub** | [github.com/walidnegm/conjecture-behaviour-runner](https://github.com/walidnegm/conjecture-behaviour-runner) |
| **Import** | `conjecture_behaviour_runner` |
| **CLI** | `conjecture` / `python -m conjecture_behaviour_runner` |
| **License** | MIT · **Status** | Alpha (0.1) |

---

## Why we created this

We kept shipping multi-turn agents that *looked* fine in demos and still failed in production:

| What users hit | What string-match evals miss |
|----------------|------------------------------|
| A glossary answer steals an in-flight cost-out | Reply text still “sounds helpful” |
| Entity identity flips mid-dialogue (`last_read_*` hijacks the pin) | No golden sentence fails |
| “Continue” re-starts assessment instead of staying on VERIFY | Snapshot tests of one reply pass |
| Detour vs continue vs new task confused | Regex/keyword ladders accrete per incident |

Those bugs live in **behaviour and ownership**, not prose. Pinning exact assistant text makes evals brittle and **does not** catch them.

So we built **Conjecture**: a small runner that scripts **turns + cognition pins**, runs them against a **control-plane adapter**, and checks **invariants** (exclusive owner, pin present/equals, allowed outcomes, …). Cognition can be **stubbed or frozen** so CI stays deterministic — the control plane still has to behave correctly.

> **One-line reason:** *If the control plane is the authority for “who owns the turn,” Conjecture is how you prove that authority holds when the conversation gets messy.*

---

## What it is (and is not)

### It is

- A **portable multi-turn behaviour harness** (scripts, pins, modes, `run_script`)
- A **standard invariant library** so adapters prove real checks, not only `always_true`
- An optional binding to the **Conversation Control Plane** with three **portable goldens**
- A **host adapter protocol** so *your* ledger can plug in the same way

### It is not

- A full product test suite or Bot0 monorepo goldens (those stay private)
- A free live-LLM soak on every PR (default is stub/freeze)
- A Playwright/UI-first runner (optional later; Slice 0 is control-plane behaviour)
- A second agent runtime — it **evaluates** ownership/pins; it does not replace your agents

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

## Pairing: ownership + proof

| Package | Question it answers |
|---------|---------------------|
| [conversation-control-plane](https://github.com/walidnegm/conversation-control-plane) | **Who owns this turn?** (ledger, sole-continue, pins, gates) |
| **conjecture-behaviour-runner** (this repo) | **Did ownership still hold after N turns?** (scripts + invariants) |

```text
        Conjecture Behaviour Runner
     scripts · pins · invariants
                 │
                 ▼
        ControlPlaneAdapter
                 │
                 ▼
     conversation-control-plane  (or your host ledger)
```

Install both:

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

- Teams building **multi-turn agents** with explicit **task ownership** (continue vs detour vs new task)
- Anyone who has watched **evals pass** while **routing/ownership fails** in chat
- Hosts that already use (or want) a **turn-ownership ledger** and need a **CI-safe proof layer**

If your only test is “the assistant said something nice,” this package is the next step up.

---

## Status

**Alpha.** MIT. Surface is intentionally small.

| Included | Meaning |
|----------|---------|
| Invariant library + base adapter | Real checks, fail-closed on unknown kinds |
| CCP stream adapter + 3 goldens | Two-repo pairing demonstrated in code |
| Generic cognition pin | Product flags stay in `extras` |
| Experimental scenario models | Quarantined; not the main 0.1 path |

**Not yet:** full path-faithful chat/SSE driver, distribution-over-N-runs monitoring, Playwright-first corpus (later slices).

---

## Contributing / monorepo note

This public tree is a **sanitized extract**. Deep product goldens and host-private scripts stay in the Bot0 application monorepo. PRs that keep the surface portable and leak-free are welcome.

---

Copyright © Bot0.ai / contributors. MIT.
