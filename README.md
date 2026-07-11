# Conjecture Behaviour Runner

**Contract testing for the conversational control plane** —  
**behavioral envelopes** (allowed outcomes + invariants) over **authoritative state**,  
under **pinned or replayed cognition**.

Not “one golden sentence.” Not a new universal testing paradigm.  
The wedge: **authoritative control-plane conformance under probabilistic cognition.**

Built by [Bot0.ai](https://bot0.ai). MIT open source.

| | |
|---|---|
| **GitHub** | [github.com/walidnegm/conjecture-behaviour-runner](https://github.com/walidnegm/conjecture-behaviour-runner) |
| **Import** | `conjecture_behaviour_runner` |
| **Specification (`CBR-SPEC`)** | [docs/SPEC.md](docs/SPEC.md) — full design, IR, Collinear, contributions |
| **License** | MIT · **Status** | Alpha — 0.1.1 |

### How to read the docs

| Doc | Role | Length |
|-----|------|--------|
| **This README** | Why it exists, how to run, script language in plain English | Short face |
| **[Specification (`CBR-SPEC`)](docs/SPEC.md)** | Normative pipeline, architecture, field tables, Collinear, OSS/Verdict, roadmap | Full design |

If the README and the spec disagree, **the spec wins** for contracts; fix the README next.

### The valuable idea (what we actually claim)

Probabilistic multi-turn systems should be tested against a **behavioral envelope**:

| Ingredient | Role |
|------------|------|
| **Cognition pins** | Separate probabilistic *interpretation* from deterministic *execution* checks |
| **Allowed outcomes** | Multiple conversational landings can be correct |
| **Invariants** | What must remain true over **authoritative state** regardless of wording or path |
| **Focus** | Ownership, active work identity, routing, terminals, ledger integrity — failures answer-quality metrics often miss |

Individually none of that is new. The combination applied to **control-plane conformance
with frozen/sampled cognition** is the defensible framing.

> **Slice 0 (honest):** hand-authored multi-turn scripts + pin-driven cognition + host
> adapter observing projected state. Reference goldens exercise **pure control-plane
> contracts** (injected pins/effects). That is a **unit-level** vertical — useful, not yet
> path-faithful chat through a deployed app. See [Slice 0 honesty](#slice-0-honesty)
> and the [Specification](docs/SPEC.md).

### Positioning (compose with existing tools — do not replace them)

```text
  Conjecture scenario + verifier (behavioral envelope)
             ↓
  Driver: Playwright / HTTP / SSE / WebSocket / in-process / …
             ↓
  Real application + Observer (ledger, tools, events)
```

| Related work | What it is | How Conjecture relates |
|--------------|------------|-------------------------|
| **Playwright** | Full execution substrate (assertions, fixtures, traces, isolation, …) | **Driver candidate**, not a straw-man “fixed DOM text” tool. We do **not** rebuild Playwright’s runner. |
| **Cucumber / Gherkin** | Readable scenarios bound to **arbitrary** step code (DB, API, state — not only strings) | Scenario *language* + bindings. Conjecture is specialized **agent/control-plane semantics**; a Cucumber integration is possible later, not a claim that Cucumber = exact output. |
| **Hypothesis stateful** | Action sequences + preconditions + invariants + **shrinking** to minimal fail | **Closest methodological analogue.** Slice 0 is hand-authored transitions; generation + shrink is roadmap, not claimed done. |
| **Eval platforms** (LangSmith, Braintrust, DeepEval, Promptfoo, Inspect, Phoenix, …) | Multi-turn sims, traces, tool paths, custom scorers — often **score observed trajectories** | We narrow to: **all acceptable trajectories preserve explicit authoritative-state contracts** (ownership, pins, terminals). Overlap exists; “they only score text” is outdated. |
| **Collinear-class sim labs** | Simulated users/worlds, multi-turn data, verifiers, rubrics | Stronger on **simulation & data**. Our wedge today: **deterministic conformance of app control plane** when cognition is pinned/replayed — not “unrelated.” |
| **CARLA / Scenic** | Real scenario runtime in a simulated world + generators | **Aspiration** for generation/ODD later — **not** what ships today (no world model, scheduler, minimizer). |

**Tight one-liners we prefer:**

- *Stateful conformance testing for probabilistic workflows.*  
- *Contract testing for the conversational control plane.*

---

## What the product is (IR + runner + verifier)

**Not** “an open-source scenario script format.” Without **our runner** and **our verifier**,
the YAML would be only a schema. Conjecture is three cores:

| Core | Job | In-tree today |
|------|-----|----------------|
| **IR** | Portable contract language (`ConjectureScript`) | script model, load JSON/YAML, scope |
| **Runner** | Execute under pin/freeze; call Driver; collect observation | `run_script`, CognitionProvider, freeze store, CLI |
| **Verifier** | Pass/fail on **authoritative state** | standard + temporal invariants, outcome sets, fail-closed |

```text
  seeds (specs · sim · agent · human)
              │
              ▼
     ┌────────────────────────────┐
     │  CONJECTURE                │
     │  IR → RUNNER → VERIFIER      │
     └──────────┬─────────────────┘
                │ Driver plugin (HTTP / Playwright / in-process)
                ▼
         Real application          pytest/CI only *hosts* the run
```

**Pipeline:** author IR → our runner executes → our verifier judges → report/CI.  
Playwright is a **driver**, not the product. Collinear **seeds** paths; it does not replace the verifier.

Full ecosystem + Collinear: **[Specification §2](docs/SPEC.md#2-project-architecture)** · **[§2.1](docs/SPEC.md#21-pipeline-ecosystem-and-collinear)**.

| | Collinear-class | Conjecture |
|--|-----------------|------------|
| **Job** | Sim users/worlds, multi-turn **data**, rubrics | **Control-plane contracts** under pin/freeze |
| **Green bar** | Quality / task / preference scores | Owner · pin · terminal · refusal envelope |
| **Integrate** | Sim **seeds** scripts; failed contracts re-probe in sim | CI **gates** merge on *our* verifier |

**Smell test:** “sim scored 0.87” → their lane. “No dual owner, pin held” → ours.

**Never core:** built-in sim worlds, quality scoreboards, creative execution engines.  
**Always core:** IR + runner + verifier (if any one is missing, the claim collapses).

### Multi-actor scripts

Turns may be **user**, **agent**, **agent→agent**, or **system/completion**.  
Slice 0 API is user-centric (`user_text`); `actor` + experimental `Actor` expand later.  
Details: [Specification §1.1](docs/SPEC.md#11-behaviour-driven-testing-and-odd-full-objective).

---

## Why this exists (short)

Agentic apps fail as wrong **owner**, lost **pin**, illegal **restart** — while wording looks fine.  
We verify **authoritative-state contracts** under pinned/frozen cognition.

| Point | Role (0.1.1) |
|-------|----------------|
| **Driver** | Act on the system (mini-app + CCP adapter; HTTP/Playwright open) |
| **Observer** | `TurnObservation` (owner, pins, extras, outcome) |
| **Cognition** | Stub + FreezeStore record/replay; local/cloud host-supplied |
| **Verifier** | Step + outcome-specific + trajectory kinds |

**Honesty:** many goldens still **inject** pin + effects (contract unit path). Path-faithful mini-app proves Act-through-`handle` + planted bugs. Full host drivers next — [Specification](docs/SPEC.md).

ODD/scope, scenario seed sources, delivery slices: **[Specification §1–2](docs/SPEC.md)**.

---

## What ships today (0.1.1)

- **Script IR** + `run_script` · scope · outcome-specific + trajectory verifiers  
- **CognitionProvider** + freeze/record store · standard + temporal invariants  
- **CLI** `run` / `path-faithful` · JSON + JUnit · path-faithful mini-app + planted bugs  
- Optional **CCP** goldens · experimental Scenario → script → Trajectory bridge  

Companion reference domain: [conversation-control-plane](https://github.com/walidnegm/conversation-control-plane).

---

## Script language (what you write)

A **script** is a multi-turn recipe: steps, optional cognition **pins**, and **invariants**
(and later **allowed outcomes**). The runner plays it; the host **adapter** observes state;
Conjecture checks the contracts. Wording of the assistant reply is **not** the pass criterion.

### Building blocks

| Piece | Role |
|-------|------|
| **`ConjectureScript`** | Named golden: `script_id`, conversation id, ordered `turns` |
| **`DialogueTurn`** | One step: stimulus text, optional pin, effects, invariants |
| **`CognitionPin`** | Fixed labels for this step under stub/freeze (e.g. `task_intent=continue`) — so CI does not need a live model |
| **`InvariantSpec`** | A rule that **must hold after the turn** — independent of reply wording |
| **`allowed_outcomes`** | Optional envelope of legal landings (more than one is fine) when cognition is live |

Slice 0 is **user-centric** (`user_text` on each turn). The broader design also includes **agent**,
**agent-to-agent**, and **system/completion** steps later (`actor` on the turn; experimental
scenario `Actor`: `user` · `agent` · `system`).

### What is an invariant?

An **invariant** is a **behaviour rule that must still be true after the turn**, no matter
how the assistant *phrased* the reply.

| Not this | This |
|----------|------|
| “The bot must say: *Continuing your cost-out…*” | “After ‘continue’, **cost-out still owns** the turn” |
| Screenshot of the chat bubble | “The **workflow id is still the same** one we started with” |

Everyday analogy: mid-checkout you click Continue — you must **still be in checkout**, your
**cart id must still match**, and the site must **not re-ask “which cart?”** from random
cookies. Those are invariants; the toast copy can vary.

```python
InvariantSpec(kind="exclusive_owner", expected="cost_out")
# After this step: exclusive owner must be cost_out — or the script fails.
```

### Standard invariant kinds (portable)

Implemented in `BaseControlPlaneAdapter` / `check_standard_invariant`. Unknown kinds
**fail closed** (never silently pass).

| Kind | Plain English | Typical `expected` |
|------|---------------|--------------------|
| **`exclusive_owner`** | Who is driving this turn? Must be exactly this owner | `"cost_out"`, `"front_door"` |
| **`owner_not`** | Must **not** still be owned by this (e.g. after a detour stole) | `"cost_out"` |
| **`active_kind`** / **`kind_equals`** | Active task/kind label equals this | `"cost_out"` |
| **`pin_present`** | Pin key has a **usable** bound value (not missing/null/empty/`False`) | `"workflow_id"` |
| **`pin_absent`** | Pin missing or null | `"project_id"` |
| **`pin_key_missing`** | Key not in the pins map at all | `"project_id"` |
| **`pin_equals`** | Bound identity is still **this** value (strict `==`) | `{"key": "workflow_id", "value": "wf_1"}` |
| **`observed_outcome`** | Adapter-reported outcome code | host-defined string |
| **`extra_true`** / **`extra_false`** | Key **present** and value is strictly `True` / `False` (missing ≠ false) | `"blocks_resolve"` |
| **`extra_missing`** | Key not in extras | `"foo"` |
| **`extra_equals`** | Host extra equals a value | `{"key": "preferred_workflow_id", "value": "wf_1"}` |
| **`always_true`** | Smoke only (null adapter) | — |

If a turn declares **`allowed_outcomes`**, the adapter **must** set `observed_outcome`
(no vacuous pass when outcome is `None`).

**Three load-bearing examples:**

1. **`exclusive_owner`** — *Who is driving?*  
   User is mid cost-out and says “continue.” Must still be `cost_out`, not glossary or a new task.

2. **`pin_equals`** — *Same thing as before?*  
   Workflow pin must stay `wf_1`. Ambient “last read” must not silently swap the entity.

3. **`extra_true` / `blocks_resolve`** — *Don’t re-resolve mid-flight*  
   Sole-continue has sealed identity: do not re-run entity resolve from ambient context.  
   Detour / front-door flows often use **`extra_false`** so resolve is allowed again.

### Mini story (all three)

**Script idea:** open cost-out on `wf_1` → user says “continue”.

| After the turn… | Invariant | Fail means |
|-----------------|-----------|------------|
| Cost-out still owns the thread | `exclusive_owner` → `cost_out` | Front door / detour / new task stole the turn |
| Still the same workflow | `pin_equals` → `workflow_id = wf_1` | Pin dropped or swapped |
| Resolve sealed mid-flight | `extra_true` → `blocks_resolve` | Entity resolve ran again |

```python
from conjecture_behaviour_runner import (
    CognitionPin, DialogueTurn, InvariantSpec, ConjectureScript,
)

script = ConjectureScript(
    script_id="cost_out_continue_keeps_owner_and_pin",
    description="Continue mid cost-out: owner, pin, and blocks_resolve hold",
    conversation_id="conv_demo",
    turns=[
        DialogueTurn(
            user_text="cost out the onboarding workflow",
            pin=CognitionPin(task_intent="new_task", read_kind="cost_out"),
            invariants=[
                InvariantSpec(kind="exclusive_owner", expected="cost_out"),
            ],
        ),
        DialogueTurn(
            user_text="continue",
            pin=CognitionPin(task_intent="continue"),
            invariants=[
                InvariantSpec(kind="exclusive_owner", expected="cost_out"),
                InvariantSpec(kind="active_kind", expected="cost_out"),
                InvariantSpec(kind="pin_present", expected="workflow_id"),
                InvariantSpec(kind="extra_true", expected="blocks_resolve"),
            ],
        ),
    ],
)
```

Real end-to-end goldens (with the control-plane adapter) live in
`contrib.control_plane` and `examples/control_plane_goldens.py` — sole-continue owns,
detour supersedes, pin beats ambient last_read.

Adapters map **your** host state into a `TurnObservation` (`exclusive_owner`, `pins`,
`extras`, …). The script language stays the same; only the adapter binding changes.

**Formal field tables, multi-turn patterns, mini-ODD `scope`, mid-flight diagram, full golden:**  
[docs/SPEC.md §4.1](docs/SPEC.md#41-script-structure-slice-0--multi-turn-design) ·  
examples: [`sole_continue_golden.json`](examples/sole_continue_golden.json) / [`.yaml`](examples/sole_continue_golden.yaml).

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

More: [docs/SPEC.md](docs/SPEC.md) ·
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

- Teams shipping **agentic / LLM-shaped applications** that grow by generation and iteration  
- Anyone whose **output looks fine** while **flow, identity, or legal outcomes** fail  
- Codebases where **scope is incomplete** and new paths keep appearing  
- Hosts that need a **CI-safe behaviour contract layer** (reference goldens are examples, not the ceiling)

---

## Explicit non-goals

- Replacing Playwright, pytest, or Cucumber as general runners  
- Rebuilding sim/world platforms (Collinear-class) as the core mission  
- Live LLM on every PR by default  
- Claiming CARLA-class generation/runtime **today**  
- Phrase laundry lists as “understanding” (cognition stays label-based / pinned)  

---

## Status

**Alpha.** MIT open source.

| Horizon | Intent |
|---------|--------|
| **Defensible wedge** | Control-plane conformance under pinned/replayed cognition |
| **0.1.1 foundations** | CognitionProvider + freeze/record store · temporal + outcome-specific verifiers · Scenario→script→Trajectory bridge · CLI `run` / JSON+JUnit · **path-faithful mini-app** + planted-bug proof |
| **Still open** | Host HTTP/SSE/Playwright drivers · full CognitionProvider for local/cloud models · richer temporal ops · generation/shrink · agent script-synthesizer · production-scale CLI (shards/retries) |

### Quick: path-faithful credibility demo

```bash
pip install -e ".[dev]"
conjecture path-faithful --prove-bugs
# clean app passes; dual_owner / drop_pin / illegal_restart each fail the same golden
```

```bash
conjecture run examples/ --adapter path-faithful --json-report /tmp/out.json --junit /tmp/out.xml
```

---

## Contribute · Verdict · foundations

**MIT:** portable PRs welcome — drivers, observers, providers, verifier kinds, agent
synthesizer, Collinear bridges, CLI, docs. Host-private goldens stay in *your* repo.

**Verdict** (planned commercial): may **host**, move **faster**, or **reimplement**
product surfaces (studio, SSO, managed freeze, private corpus, SLA). OSS and commercial
do not block each other.

**Full contribution map, OSS vs Verdict table, foundational ideas:**  
**[Specification §8](docs/SPEC.md#8-contributions-verdict-and-foundational-ideas)**.

---

Copyright © Bot0.ai / contributors. MIT.
