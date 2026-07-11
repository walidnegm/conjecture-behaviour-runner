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
| **License** | MIT · **Status** | Alpha **0.1.2** |

### How to read the docs

| Doc | Type | Role |
|-----|------|------|
| **This README** | Project face | Why, green bar, script language, quickstart |
| **[CBR-SPEC](docs/SPEC.md)** | **Specification** | Normative claim, architecture, IR fields, ecosystem, roadmap |

On conflict: **SPEC wins** for contracts; update the README.

---

## Finalized claim

We differentiate by **what we assert** (the green bar), not by vendor bake-offs.

| | |
|--|--|
| **Product** | **IR + runner + verifier** — multi-turn **control-plane contracts** under pin/freeze |
| **Green bar** | Owner, pins, legal landings, mid-flight law hold — **expected state must be declared** |
| **Works with** | **LangGraph · Crew · Temporal · HTTP · Playwright** as hosts/drivers (they orchestrate; we gate law) |
| **Not our product** | Model quality scores, preference data, built-in user-sim worlds, hypothesis-only scripts |
| **Commercial** | Optional **Verdict** (hosted / faster / different) — separate from OSS **Verifier** |

Normative: **[CBR-SPEC §0](docs/SPEC.md#0-finalized-product-claim-normative)**.

```text
  specs / agents / humans / optional path seeds
                    │
                    ▼
         ┌──────────────────────────┐
         │  CONJECTURE              │
         │  IR → RUNNER → VERIFIER  │
         └───────────┬──────────────┘
                     │ Driver plugin
                     ▼
    App · LangGraph · Temporal · Crew · HTTP · Playwright
                     │
              pytest / CI (process host only)
```

**Always core:** IR + runner + verifier.  
**Never core:** user-sim worlds, quality scoreboards, proprietary “creative” engines.

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

A **script** is multi-turn steps + optional pins + **expected contracts** (invariants /
allowed outcomes). The **runner** plays it; the host **adapter** observes; the
**verifier** judges. Reply wording is not the pass criterion.

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

```text
  ConjectureScript (turns · pins · expected contracts)
              │
              ▼
        run_script(...)
    CognitionProvider: stub | freeze | record
              │
              ▼
     Host adapter (Driver + Observer)
    apply_effect (arrange) · observe_turn (Act→Observe)
              │
              ▼
     Verifier: step + outcome + trajectory invariants
              │
              ▼
     RunResult · JSON/JUnit · CI exit code
```

Adapters map **your** host (ledger, graph state, workflow status) into `TurnObservation`.

---

## What ships (0.1.2)

| Area | Status |
|------|--------|
| IR (`ConjectureScript`, scope, load JSON/YAML) | ✅ |
| Runner (`run_script`, CognitionProvider, FreezeStore) | ✅ |
| Verifier (standard + temporal + outcome-specific) | ✅ |
| CLI (`conjecture run`, `path-faithful`, JSON/JUnit) | ✅ |
| Path-faithful mini-app + planted bugs | ✅ |
| Optional CCP stream goldens | ✅ (`[control-plane]`) |
| Scenario → script → Trajectory bridge | ✅ experimental |
| LangGraph / Crew / Temporal / HTTP / Playwright adapters | ⬜ roadmap (contract locked) |
| Agent synthesizer requiring expected | ⬜ roadmap |
| Domain ground-truth plugins | ⬜ roadmap |

Companion reference domain: [conversation-control-plane](https://github.com/walidnegm/conversation-control-plane).

---

## Quickstart

```bash
git clone https://github.com/walidnegm/conjecture-behaviour-runner.git
cd conjecture-behaviour-runner
pip install -e ".[dev]"
pytest tests/ -q
conjecture path-faithful --prove-bugs
# clean passes; dual_owner / drop_pin / illegal_restart each fail
```

```bash
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
