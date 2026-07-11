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
| **Public contract (spec)** | [docs/conjecture-behaviour-runner.md](docs/conjecture-behaviour-runner.md) |
| **License** | MIT · **Status** | Alpha — Slice 0 |

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
> and the [public contract](docs/conjecture-behaviour-runner.md).

### Positioning (compose with existing tools — do not replace them)

```text
  Conjecture scenario + oracle (behavioral envelope)
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

### Scripts are multi-actor (not “user only”)

A script is a **sequence of turns that move system state**. Initiation is not limited to a human:

| Actor / turn kind | Examples | What we pin |
|-------------------|----------|-------------|
| **User** | Chat message, chip, confirm | Ownership, pin, legal outcome after the human act |
| **Agent** | Specialist continues, tool result applied, handoff | Same contracts when **an agent** drives the next step |
| **Agent → agent** | Handoff, subagent complete → parent, multi-agent pipeline | Exclusive owner, pin identity, no steal / no double-write |
| **System / completion** | Job done, SSE terminal, timeout, lease reclaim, scheduled tick | Terminal vs mid-flight, recovery honesty, cancel semantics |

The experimental scenario model already names actors: `user` · `agent` · `system`
(`Actor` in `experimental.scenario_models`). Slice 0’s `DialogueTurn.user_text` is the
**user-centric first surface** — not a claim that only humans exist in the design.

**Phasing (intentional):**

1. **Now — user-centric.** Author and play back scripts as human-led multi-turn flows
   (stub/freeze cognition). Highest pain today; easiest to seal.
2. **Next — agent-initiated and completion.** Turns that fire without a new human message
   (async job complete, mid-flight continue, system cancel/timeout).
3. **Later — agent-to-agent.** Multi-agent handoffs and completion chains under the same
   invariant envelope — still **host contracts**, not model-feedback scoring.

Same idea the whole way: **behavioral envelopes over authoritative state**.

---

## Why this project exists

Vibe/auto-coded agentic apps accrete **unknown pathways**. Production breaks as wrong
**owner**, lost **pin**, illegal **restart**, dual writers — while the reply still “looks fine.”
Answer-quality and many trajectory *scores* can stay green.

Conjecture aims to verify: **every acceptable path still preserves explicit
authoritative-state contracts** (with cognition pinned, frozen, or later sampled).

### Target architecture (four extension points)

| Point | Role | Slice 0 |
|-------|------|---------|
| **Driver** | Act on the real system (HTTP, SSE, Playwright, in-process, …) | In-process **adapter** only |
| **Observer** | Collect authoritative evidence (ledger, tools, events, ownership) | `TurnObservation` from adapter |
| **Cognition provider** | stub / freeze-replay / record / local / cloud | **Pins on the turn** (modes mostly labels until providers land) |
| **Oracle** | Allowed outcomes + invariants (+ later temporal / distributional) | Standard invariant kinds + outcome membership |

### Slice 0 honesty

| Green today means | Does **not** yet mean |
|-------------------|------------------------|
| Given **injected** pin + ledger effects, pure control-plane rules hold | User NL was classified by the real app |
| Adapter projects owner/pins/extras correctly under those inputs | Path-faithful chat/SSE through production |
| Multi-turn **script API** works with fail-closed checks | Full scenario IR → runner → trajectory → report pipeline |

**Arrange / Act / Observe / Assert** is the intended shape. Slice 0 goldens often
**arrange** mid-flight state via `LedgerEffect` and **supply** cognition via pin —
useful contract unit tests; the natural-language text is partly **documentary** until
a real Driver path lands.

**Next credibility milestone** (see public contract): drive a real example app,
freeze real cognition, observe real ledger mutations, catch three deliberate bugs,
deterministic CI replay.

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

### Where scenarios and use-cases come from (important distinctions)

Scenarios are **seeded from different ground truths**. Mixing them without labels
confuses trust and triage.

| Source | What you read / write | What you get | Build status |
|--------|----------------------|--------------|--------------|
| **Specs** | Epics, ODD/scope, design contracts, acceptance intent | *Intended* use-cases — what the design claims | **Partial** (authored by hand today) |
| **Codebase scan** | Routers, ledgers, state machines, tools, prompts, existing regs | *Structural* use-cases — transitions the code actually admits | **Partial** (Slice 0 goldens are hand-curated from contracts; **automated scan → draft scripts not built out**) |
| **Raw scripts / ideas / edge lists** | Free-form scenario seeds, “what if…”, sticky notes, incident notes | *Hypothesis* and **edge conditions** before they are formal ODD probes | **Partial** (humans write `ConjectureScript`s; **idea → scenario pipeline not built out**) |
| **User traffic** | Sessions, transcripts, telemetry | *Empirical* routes people actually drive | **Not built out** |
| **Explorer** (“agent plays the game”) | Deployed app exploration | *Operational* reachability | **Not built out** |
| **Adversarial from ODD** | Stress generation on/inside/outside scope | *Refusal* and stress contracts | **Seed only** (threat regs); formal generator **not built out** |

These are **different extractors into the same corpus**, not synonyms:

```text
  specs ──┐
  codebase scan ──┼──► curate / promote ──► scenario + invariants ──► play back
  raw ideas / edges ──┘
  (later: traffic · explorer · adversarial gen)
```

**Honest status:** Slice 0 proves we can **play back** pinned scripts with real
invariant checks. We have **not** fully built automated “scan the codebase →
draft use-cases,” “specs → scenario pack,” or “raw edge list → formal probes.”
That generation and curation stack is still on the **project roadmap**.

Full write-up: [docs/conjecture-behaviour-runner.md](docs/conjecture-behaviour-runner.md) §1.1.

---

## Full project shape (not only Slice 0)

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
- **Cognition pins** (portable labels; host-specific flags in `extras`)
- **Invariant library** (`BaseControlPlaneAdapter`, fail-closed unknown kinds)
- **Adapter protocol** — plug *your* control plane / ledger / app state
- Optional **Conversation Control Plane** binding + **3 portable goldens**
- **Experimental** scenario YAML / trajectory models (quarantined; later slices)

Companion for the ownership domain:  
[conversation-control-plane](https://github.com/walidnegm/conversation-control-plane)  
(*who owns the thread* — Conjecture *proves it still holds across turns*).

That pairing is the **reference domain**, not a claim that Conjecture *is only* a CCP test kit.

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
[docs/conjecture-behaviour-runner.md §4.1](docs/conjecture-behaviour-runner.md#41-script-structure-slice-0--multi-turn-design) ·  
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
| **Slice 0** | Script API · standard invariants · CCP reference goldens (contract unit path) |
| **Next milestone** | Path-faithful vertical: real app · freeze cognition · real ledger · catch planted bugs · CI replay |
| **Later** | Cognition providers · Driver/Observer split · temporal oracles · generation/shrink · richer runner CLI |

Contributions welcome — scripts, invariants, adapters, drivers, and docs that stay portable
(host-private goldens stay in *your* app repo).

---

Copyright © Bot0.ai / contributors. MIT.
