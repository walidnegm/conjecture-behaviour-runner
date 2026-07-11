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

### Where this sits (not LLM-feedback labs, not Playwright)

Conjecture is closer to **scenario construction in autonomous driving** (e.g. **CARLA** /
SOTIF-style ODD work) than to **LLM feedback / model-quality eval products** or browser E2E tools.

We are **careful not to compete** as “the company that scores LLM replies / trains models from
simulated users.” That market already exists. We pin **host-system behaviour contracts**
when code and multi-turn ownership are incomplete.

| Approach | What it optimizes for | How Conjecture differs |
|----------|----------------------|-------------------------|
| **Playwright / Cypress-style E2E** | Deterministic UI: click → wait → assert fixed text/DOM | UI can be *one driver later*. The product is **behaviour contracts** (outcomes + invariants), not click-assert-text as the definition of “pass.” |
| **LLM feedback / model-eval labs** (rubrics, preference data, synthetic users, RL signal, leaderboards) | Score or improve the **model** | **Out of scope as a product.** We do not ship “was the answer good?” as the primary verdict. We check **who may own the turn, what must stay pinned, which landings are legal** on the *host*. |
| **CARLA-style scenario building** | Scenarios + edge cases under an **ODD**; ground truth from the world / maps / sensors; generate stress and out-of-domain probes | **Closest analogy.** Declare the claimed domain (ODD/scope), author scenarios from **ground truth** (code contracts, real traffic, explorer), generate **edge conditions**, pin **what must hold** when the world is nondeterministic. |
| **Conjecture (this package)** | Multi-turn **behaviour envelopes** for agentic products built under vibe/auto coding | Scenario + trajectory + optional edge generation from ground-truth collection; first sealable surface is control-plane mid-flow contracts. |

**In short:** Playwright automates the browser. LLM-feedback companies evaluate **model quality**.  
Conjecture is for **scenario- and edge-driven behaviour contracts** on systems whose path set
is incomplete — the same *kind of problem* AV stacks face with ODD and edge cases, applied
to agentic product control flow.

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
**user-centric first surface** — not a claim that only humans exist in the product.

**Phasing (intentional):**

1. **Now — user-centric.** Author and play back scripts as human-led multi-turn flows
   (stub/freeze cognition). Highest pain today; easiest to seal.
2. **Next — agent-initiated and completion.** Turns that fire without a new human message
   (async job complete, mid-flight continue, system cancel/timeout).
3. **Later — agent-to-agent.** Multi-agent handoffs and completion chains under the same
   invariant envelope — still **host contracts**, not model-feedback scoring.

Same product idea the whole way: **behaviour envelopes**, not “grade this LLM reply.”

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

### Where scenarios and use-cases come from (important distinctions)

Scenarios are not only “someone wrote a Playwright test.” They are **seeded from
different ground truths**. Mixing them without labels confuses trust and triage.

| Source | What you read / write | What you get | Build status |
|--------|----------------------|--------------|--------------|
| **Specs** | Epics, ODD/scope, product contracts, acceptance intent | *Intended* use-cases — what the design claims | **Partial** (authored by hand today) |
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
That generation and curation stack is still the product roadmap.

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

Slice 0 is **user-centric** (`user_text` on each turn). Product scope also includes **agent**,
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
| **`pin_present`** | An identity pin is still bound | `"workflow_id"` |
| **`pin_absent`** | This pin is empty / missing | `"project_id"` |
| **`pin_equals`** | Bound identity is still **this** value (not ambient last_read) | `{"key": "workflow_id", "value": "wf_1"}` |
| **`observed_outcome`** | Adapter-reported outcome code | host-defined string |
| **`extra_true`** | Host flag in observation extras is true | `"blocks_resolve"` |
| **`extra_false`** | Host flag is false | `"blocks_resolve"` |
| **`extra_equals`** | Host extra equals a value | `{"key": "preferred_workflow_id", "value": "wf_1"}` |
| **`always_true`** | Smoke only (null adapter) | — |

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
