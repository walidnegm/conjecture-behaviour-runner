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
| **Implementation spec** | [`docs/SPEC.md`](docs/SPEC.md) — **CBR-SPEC** (normative) |
| **Agent coder guide** | [`AGENTS.md`](AGENTS.md) — integrate host; agent output **is** the golden |
| **Prompt seed** | [`prompts/conjecture_script_author.seed.md`](prompts/conjecture_script_author.seed.md) — trajectory + ODD worksheet → Conjecture Script |
| **License** | MIT · **Status** | Alpha **0.1.2** |

### How to read the docs

| Doc | Type | Role |
|-----|------|------|
| **This README** | Project face | Why, E2E demo, script language, quickstart |
| **[CBR-SPEC](docs/SPEC.md)** | **Specification** | Normative claim, architecture, Scenario/Script, ecosystem |
| **[AGENTS.md](AGENTS.md)** | Agent coder contract | Host adapter checklist, golden rules, workflow |
| **[Prompt seed](prompts/conjecture_script_author.seed.md)** | LLM/coding-agent prompt | Emit valid `ConjectureScript` JSON with expected state |

On conflict: **SPEC wins** for contracts; **AGENTS.md** for agent workflow; update the README.

---

## Finalized claim

We differentiate by **what we assert** (the green bar), not by vendor bake-offs.

| | |
|--|--|
| **Trajectory (authored)** | Load-bearing **twists & turns** that can stress state law — the story of the path |
| **Conjecture Scenario** | Flexible **description language** for that trajectory + envelopes (not tied to one driver) |
| **Conjecture Script** | **Runnable play-back** of a trajectory for a chosen runner (usual CI golden today) |
| **Who runs it** | A **runner** + **Driver** (control-plane `run_script` today; others later) |
| **Observed trajectory** | Evidence of **one** execution under one profile — input to the verifier |
| **Verifier** | Expected envelopes vs **observed trajectory** |
| **Green bar** | State law under pin/freeze — not reply wording |
| **Commercial** | Optional **Verdict** — separate from OSS **Verifier** |

**Mnemonic:** Scenario *describes* the trajectory of twists; Script *plays* it; observed trajectory *is what happened*; Verifier *judges*.

**Maturity (honest):** the **control-plane Script + `run_script` + verifier** path is what we can run today (E2E mini-app, CCP goldens). Full **Scenario** language, multi-runner play-back, and rich observed-trajectory tooling are **earlier** — useful shapes, not a finished platform. We are not as mature as a full behaviour-runner stack would imply.

**Seeds welcome:** specs, humans, coding agents, **and** multi-turn tools (e.g. Collinear-class sims, session exports, explorers). Their output is **path material** we curate into Scenario/Script + **expected** state — not something we replace.

Normative: **[CBR-SPEC §0](docs/SPEC.md#0-finalized-product-claim-normative)**.

```text
  seeds (specs · Collinear/other multi-turn tools · agent · human)
              │  curate + attach expected envelopes
              ▼
  authored TRAJECTORY of twists  (load-bearing path story)
              │
              ▼  described as
  Conjecture Scenario  and/or  Conjecture Script
              │  who runs it? (explicit — file does not run itself)
     ┌────────┴────────┐
     ▼                 ▼
  control-plane    other runners
  runner           (roadmap)
  (run_script)
     └────────┬────────┘
              │ Driver plugin (HTTP · Playwright · LangGraph ·
              │               Temporal · Crew · in-process · …)
              ▼
       Real application
              │
     OBSERVED TRAJECTORY → VERIFIER → pass/fail
              │
       pytest / CI only *hosts* the run
```

**Always core:** trajectory envelopes (expected) + at least one runner + verifier.  
**Never core:** “we are the only multi-turn tool,” quality scoreboards, “the file runs itself.”

---

## End-to-end example (try this first)

A **multi-turn agentic conversation** against our in-repo mini control plane
(`MiniChatApp` — real `handle()` Act path). Reply wording is irrelevant; **state law** is not.

### The conversation

| Turn | User says | Pin (frozen) | Expected after the turn |
|------|-----------|--------------|-------------------------|
| 1 | `cost out the onboarding workflow` | `new_task` | owner `cost_out` · pin `workflow_id` |
| 2 | `make the volume 10k` | `continue` | still `cost_out` · same pin · `blocks_resolve` |

```text
  seeds / author ──► Conjecture Script (this E2E golden)
                            │
                            ▼  control-plane runner (run_script)
              Driver: MiniChatApp.handle() ──► observation
                            │
                            ▼
                       VERIFIER ──► PASS/FAIL
```

### Run it

```bash
git clone https://github.com/walidnegm/conjecture-behaviour-runner.git
cd conjecture-behaviour-runner
pip install -e ".[dev]"

python examples/e2e_multi_turn.py
# or: conjecture path-faithful --prove-bugs
```

### What you should see

| Scenario | Result | Why it helps |
|----------|--------|--------------|
| Healthy continue | **PASS** | Mid-flight contracts hold under freeze |
| Bug: continue steals to front door | **FAIL** | Dual owner — reply can still look fine |
| Bug: continue drops `workflow_id` | **FAIL** | Lost identity pin |
| Bug: continue wipes the task | **FAIL** | Illegal restart mid-flight |

That is one **runner** (control-plane `run_script`) playing a **ConjectureScript** (play-back form)
against a Driver (`handle`). The same envelopes can later be described in full
**Scenario** language and run by other runners — **who runs it** stays explicit.

---

## What scenarios actually test

| Assert (control-plane ground truth) | Do not assert (default wedge) |
|-------------------------------------|--------------------------------|
| Who **owns** the turn after this step | “The reply was good” |
| **Pin** identity still bound / unchanged | Exact assistant wording |
| **Legal landing** (`allowed_outcomes`) | Preference / rubric scores |
| Mid-flight law (`blocks_resolve`, no illegal restart) | Full product domain math (unless host projects it) |

A CI golden is **probe + expected result**. Scripts with no expected state are sketches, not merge gates.

---

## Script language (what you write)

### Load-bearing trajectory: twists → invariants

This is the script we care about: a **trajectory of twists and turns** that can stress
the control plane, with **invariants / allowed outcomes** bound at those landings — not
a novel of every chat line.

```text
  twists & turns (path)
       continue · detour · handoff · complete · ambient noise
              │
              ▼  at critical landings
  allowed outcomes + invariants  (state law that must hold)
              │
              ▼
  verifier checks those — wording free to vary
```

| You write | Meaning |
|-----------|---------|
| Load-bearing **turns** | Which twist are we probing? |
| **Allowed outcomes** | Legal landings after that twist |
| **Invariants** | State that must hold across those landings |
| Pins / freeze | Cognition fixed so CI is reproducible |

Path without invariants = a tour. **Twists with invariants = a test.**

**Conjecture Scenario** = full flexible language (`experimental/Scenario` + `schema.json`).  
**Conjecture Script** = control-plane play-back form for today’s runner (`ConjectureScript` below).  
Same twists→invariants idea; Script is what most goldens are today.

A **Script** is multi-turn steps + pins + **expected contracts**. The **runner** you choose
plays it; the host **adapter** observes; the **verifier** judges.

### Conjecture Scenario example (the cool description language)

Scenario is **not** “Script with a different name.” It is a richer **description** of the
trajectory: scope/ODD, execution profiles, multi-actor steps, waits, nondeterminism
envelopes, evidence pointers, and terminal buckets. It is **not tied to one driver**.
Today you can **validate + compile → Script → control-plane runner**.

| File | What |
|------|------|
| [`examples/scenario_sole_continue.yaml`](examples/scenario_sole_continue.yaml) | Full sole-continue **Scenario** (YAML, comments) |
| [`examples/scenario_sole_continue.json`](examples/scenario_sole_continue.json) | Same Scenario as JSON (schema-shaped) |
| [`examples/scenario_compile_and_run.py`](examples/scenario_compile_and_run.py) | Load → validate → compile → PASS + dual_owner FAIL |

```bash
pip install -e ".[dev,scenarios]"
python examples/scenario_compile_and_run.py
```

Abbreviated Scenario (see YAML for full cool bits):

```yaml
scenario_id: sole_continue_mid_flight
scenario_class: control_plane_sole_continue
scope:
  in_scope: [mid-flight sole-continue on a pinned workflow]
  expected_refusal: [illegal restart mid continue, dual-owner steal]
goal_state: [cost_out_still_owns_turn, workflow_pin_stable]
execution_profiles:
  - { id: desktop_stub_cognition, device: desktop, network: low_latency }
steps:
  - id: open_cost_out
    actor: user
    control_point: chat_input
    maneuver: start_sole_continue_task
    wait: { type: stream_wait, settle_condition: agent_turn_complete, timeout_ms: 15000 }
    nondeterminism:
      type: agentic
      allowed_outcomes: [continue_owned]
      required_invariants: [exclusive_owner_is_cost_out_when_continue_owned]
    payload:   # executable bridge → Script
      user_text: "cost out the onboarding workflow"
      pin: { task_intent: new_task, read_kind: cost_out }
      invariants:
        - { kind: exclusive_owner, expected: cost_out }
  - id: continue_volume
    actor: user
    control_point: chat_input
    maneuver: continue_mid_flight
    wait: { type: stream_wait, settle_condition: agent_turn_complete, timeout_ms: 15000 }
    nondeterminism:
      type: agentic
      allowed_outcomes: [continue_owned]
    payload:
      user_text: "make the volume 10k"
      pin: { task_intent: continue }
      invariants:
        - { kind: exclusive_owner, expected: cost_out }
        - { kind: pin_equals, expected: { key: workflow_id, value: wf_1 } }
        - { kind: extra_true, expected: blocks_resolve }
terminal_states:
  expected: [continue_owned_with_stable_pin]
  failure:
    - state: dual_owner_steal
      required_graceful_handling: [fail_closed_to_verifier]
```

**Maturity:** Scenario models + schema + compile bridge are **experimental**. The everyday
CI golden is still **Script JSON**. Scenario is the language we grow into for multi-runner
description; do not claim full multi-surface play-back yet.

### Trajectory as JSON (authored vs observed)

There is no separate mystery format for “the trajectory.” In practice:

| Side | JSON you look at | Role |
|------|------------------|------|
| **Authored trajectory** | **Conjecture Script** file | Twists (`turns`) + expected envelopes (`invariants`, `allowed_outcomes`, `trajectory_invariants`) — **the golden** |
| **Observed trajectory** | **`RunResult.to_dict()`** after a run | Evidence: per-turn `observation` + what held/violated — **verifier input** |

**Full files (E2E sole-continue path):**

| File | What |
|------|------|
| [`examples/trajectory_authored_sole_continue.json`](examples/trajectory_authored_sole_continue.json) | Authored path: enter cost_out → continue volume; same golden as the E2E table |
| [`examples/trajectory_observed_pass.json`](examples/trajectory_observed_pass.json) | Observed trajectory when healthy (PASS) |
| [`examples/trajectory_observed_fail_dual_owner.json`](examples/trajectory_observed_fail_dual_owner.json) | Observed when continue steals to front_door (FAIL) |

Authored (abbreviated — see file for full `scope` + `trajectory_invariants`):

```json
{
  "script_id": "trajectory_e2e_sole_continue",
  "description": "open cost_out on wf_1 → continue; owner + pin + blocks_resolve",
  "conversation_id": "conv_traj_e2e",
  "trajectory_invariants": [
    { "kind": "pin_stable", "expected": "workflow_id" },
    { "kind": "eventually_exclusive_owner", "expected": "cost_out" }
  ],
  "turns": [
    {
      "actor": "user",
      "user_text": "cost out the onboarding workflow",
      "pin": { "task_intent": "new_task", "read_kind": "cost_out" },
      "invariants": [
        { "kind": "exclusive_owner", "expected": "cost_out" },
        { "kind": "pin_present", "expected": "workflow_id" }
      ],
      "allowed_outcomes": ["continue_owned"]
    },
    {
      "actor": "user",
      "user_text": "make the volume 10k",
      "pin": { "task_intent": "continue" },
      "invariants": [
        { "kind": "exclusive_owner", "expected": "cost_out" },
        { "kind": "pin_equals", "expected": { "key": "workflow_id", "value": "wf_1" } },
        { "kind": "extra_true", "expected": "blocks_resolve" }
      ],
      "allowed_outcomes": ["continue_owned"]
    }
  ]
}
```

Observed after turn 2 on the dual-owner bug (why that row is **FAIL**):

```json
{
  "passed": false,
  "failures": [
    "turn[1] exclusive_owner: exclusive_owner='front_door' != expected 'cost_out'"
  ],
  "turn_results": [
    {
      "index": 1,
      "user_text": "make the volume 10k",
      "observation": {
        "exclusive_owner": "front_door",
        "pins": { "workflow_id": "wf_1" },
        "observed_outcome": "continue_owned",
        "extras": { "blocks_resolve": true }
      },
      "invariants_violated": ["exclusive_owner"]
    }
  ]
}
```

Load and run the authored file:

```bash
python -c "
from conjecture_behaviour_runner import load_script_json, run_script, LlmMode
from conjecture_behaviour_runner.path_faithful import MiniAppAdapter, MiniChatApp
s = load_script_json('examples/trajectory_authored_sole_continue.json')
print(run_script(s, adapter=MiniAppAdapter(MiniChatApp()), llm_mode=LlmMode.STUB).passed)
"
```

### Building blocks

| Piece | Role |
|-------|------|
| **`ConjectureScript`** | Golden: id, conversation, turns, optional `scope`, trajectory invariants |
| **`DialogueTurn`** | Stimulus (`user_text`), `actor`, pin, effects, **expected** invariants / outcomes |
| **`CognitionPin`** | Frozen labels for the step (CI-safe cognition) |
| **`InvariantSpec`** | State rule after the turn (e.g. `exclusive_owner`) |
| **`allowed_outcomes`** | Envelope of legal landings (requires `observed_outcome` if set) |
| **`ScriptScope`** | Mini-ODD: in_scope / out_of_scope / expected_refusal |

Actors: `user` · `agent` · `system` (Slice 0 defaults to user-centric `user_text`).

### Expected result = ground truth

| Mechanism | Meaning |
|-----------|---------|
| `invariants` | Must hold after this step |
| `allowed_outcomes` | Legal landing class(es) |
| `outcome_invariants` | Extra rules **if** that outcome occurred |
| `trajectory_invariants` | Cross-turn law (e.g. pin stable, eventually owner) |

### What is an invariant?

A rule that must stay true **after the turn**, independent of wording.

| Not this | This |
|----------|------|
| “Bot must say *Continuing…*” | “**cost_out** still owns the turn” |
| Chat screenshot | “**workflow_id** is still `wf_1`” |

```python
InvariantSpec(kind="exclusive_owner", expected="cost_out")
```

### Common verifier kinds

| Kind | Plain English |
|------|----------------|
| `exclusive_owner` / `owner_not` | Who drives (or must not) |
| `active_kind` / `kind_equals` | Active task/kind |
| `pin_present` / `pin_equals` / `pin_absent` | Entity identity bound correctly |
| `extra_true` / `extra_false` | Host flags (e.g. `blocks_resolve`) — strict, missing ≠ false |
| `observed_outcome` | Adapter outcome code |

Unknown kinds **fail closed**. Full tables: [SPEC §4.1](docs/SPEC.md#41-script-structure-slice-0--multi-turn-design).

### Mini story

Open cost-out on `wf_1` → user says “continue”:

| Must hold | Kind |
|-----------|------|
| Cost-out still owns | `exclusive_owner` |
| Same workflow | `pin_equals` |
| No mid-flight re-resolve | `extra_true` → `blocks_resolve` |

```python
from conjecture_behaviour_runner import (
    CognitionPin, DialogueTurn, InvariantSpec, ConjectureScript,
)

script = ConjectureScript(
    script_id="cost_out_continue_keeps_owner_and_pin",
    description="Continue mid cost-out: owner, pin, blocks_resolve",
    conversation_id="conv_demo",
    turns=[
        DialogueTurn(
            user_text="cost out the onboarding workflow",
            pin=CognitionPin(task_intent="new_task", read_kind="cost_out"),
            invariants=[InvariantSpec(kind="exclusive_owner", expected="cost_out")],
        ),
        DialogueTurn(
            user_text="continue",
            pin=CognitionPin(task_intent="continue"),
            invariants=[
                InvariantSpec(kind="exclusive_owner", expected="cost_out"),
                InvariantSpec(kind="pin_present", expected="workflow_id"),
                InvariantSpec(kind="extra_true", expected="blocks_resolve"),
            ],
            allowed_outcomes=["continue_owned"],
        ),
    ],
)
```

Examples: [`sole_continue_golden.json`](examples/sole_continue_golden.json) ·  
[`control_plane_goldens.py`](examples/control_plane_goldens.py) ·  
path-faithful: `conjecture path-faithful --prove-bugs`.

---

## How a run works

Execution detail of the [canonical stack](#finalized-claim) (control-plane runner path today):

```text
  Conjecture Script    (turns · pins · expected contracts)
              │  who runs it: control-plane runner (run_script)
              ▼
    CognitionProvider: stub | freeze | record
              │
              ▼  Driver plugin
     Host adapter (observe_turn / handle / graph.invoke / …)
    apply_effect (arrange) · Act → Observe → TurnObservation
              │
              ▼
     VERIFIER (step + outcome + trajectory invariants)
              │
              ▼
     OBSERVED TRAJECTORY (RunResult) · JSON/JUnit
              │
       pytest / CI only *hosts* the run
```

Adapters map **your** host (ledger, graph state, workflow status) into `TurnObservation`.

---

## What ships (0.1.2)

| Area | Status |
|------|--------|
| Conjecture Scenario (`experimental/Scenario`, schema, `examples/scenario_sole_continue.*`) | ✅ experimental |
| Conjecture Script (`ConjectureScript`, scope, load JSON/YAML) | ✅ stable |
| Runner (`run_script`, CognitionProvider, FreezeStore) | ✅ |
| Verifier (standard + temporal + outcome-specific) | ✅ |
| CLI (`conjecture run`, `path-faithful`, JSON/JUnit) | ✅ |
| Path-faithful mini-app + planted bugs | ✅ |
| Optional CCP stream goldens | ✅ (`[control-plane]`) |
| Scenario → Script → observed trajectory bridge | ✅ experimental |
| LangGraph / Crew / Temporal / HTTP / Playwright adapters | ⬜ roadmap (contract locked) |
| Agent synthesizer requiring expected | ⬜ roadmap |
| Domain ground-truth plugins | ⬜ roadmap |

Companion reference domain: [conversation-control-plane](https://github.com/walidnegm/conversation-control-plane).

---

## Quickstart

Prefer the [E2E example](#end-to-end-example-try-this-first) first. Then:

```bash
pip install -e ".[dev]"
pytest tests/ -q

# optional CCP goldens
pip install -e ".[dev,control-plane]"
python examples/control_plane_goldens.py

conjecture run examples/ --adapter path-faithful \
  --json-report /tmp/out.json --junit /tmp/out.xml
```

```python
from conjecture_behaviour_runner import (
    LlmMode, CognitionPin, DialogueTurn, InvariantSpec,
    ConjectureScript, run_script, NullControlPlaneAdapter,
)

script = ConjectureScript(
    script_id="demo",
    description="null-adapter smoke",
    conversation_id="conv_demo",
    turns=[
        DialogueTurn(
            user_text="continue",
            pin=CognitionPin(task_intent="continue"),
            invariants=[InvariantSpec(kind="always_true")],
        ),
    ],
)
assert run_script(
    script, adapter=NullControlPlaneAdapter(), llm_mode=LlmMode.STUB
).passed
```

Real checks: implement `ControlPlaneAdapter` / `BaseControlPlaneAdapter`,  
`contrib.control_plane.ControlPlaneStreamAdapter`, or `path_faithful.MiniAppAdapter`.

---

## Who this is for

- Agentic / multi-turn apps (including **LangGraph / Crew / Temporal** hosts)  
- Teams where output “looks fine” but **owner / pin / terminal** law breaks  
- CI that needs **freeze-safe** control-plane gates  

## Non-goals

- Replacing Playwright, pytest, or orchestrators  
- Built-in multi-turn user-sim / world platforms  
- Live LLM on every PR by default  
- Model leaderboards / preference datasets  

---

## Contribute · Verdict

**MIT:** drivers, observers, providers, verifier kinds, orchestrator adapters, agent
synthesizer, CLI, docs — portable only; no host-private goldens in this repo.

**Verdict** (commercial, optional): hosted runs, studio, SSO, managed freeze, SLA —
may move faster or reimplement; does not block OSS.

Full maps: **[CBR-SPEC §8](docs/SPEC.md#8-contributions-verdict-and-foundational-ideas)**.

---

Copyright © Bot0.ai / contributors. MIT.
