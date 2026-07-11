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
| **Prompt seed** | [`prompts/conjecture_script_author.seed.md`](prompts/conjecture_script_author.seed.md) — emit runnable IR, not a test plan |
| **License** | MIT · **Status** | Alpha **0.1.2** |

### How to read the docs

| Doc | Type | Role |
|-----|------|------|
| **This README** | Project face | Why, E2E demo, script language, quickstart |
| **[CBR-SPEC](docs/SPEC.md)** | **Specification** | Normative claim, architecture, IR, ecosystem |
| **[AGENTS.md](AGENTS.md)** | Agent coder contract | Host adapter checklist, golden rules, workflow |
| **[Prompt seed](prompts/conjecture_script_author.seed.md)** | LLM/coding-agent prompt | Emit valid `ConjectureScript` JSON with expected state |

On conflict: **SPEC wins** for contracts; **AGENTS.md** for agent workflow; update the README.

---

## Finalized claim

We differentiate by **what we assert** (the green bar), not by vendor bake-offs.

| | |
|--|--|
| **Description language** | Flexible **trajectory/scenario** files: actors, steps, scope, allowed outcomes, required invariants (not tied to one driver) |
| **Who runs it** | A **runner** + **Driver** (CP `run_script` today; Playwright / LangGraph / Temporal / HTTP as plugins or alternate runners) |
| **Verifier** | Shared judge: expected envelopes vs **observed** trajectory |
| **Green bar** | Declared state law holds under pin/freeze — not reply wording |
| **Play-back form** | `ConjectureScript` = thin form for the **control-plane runner** (compile target) — not the whole language |
| **Commercial** | Optional **Verdict** — separate from OSS **Verifier** |

Normative: **[CBR-SPEC §0](docs/SPEC.md#0-finalized-product-claim-normative)**.

```text
  trajectory/scenario DESCRIPTION  (generalized language)
              │
              ▼  who runs it? (explicit)
     ┌────────┴────────┐
     ▼                 ▼
  CP runner      other runners (e.g. UI)
  (run_script)   (roadmap)
     │                 │
     └────────┬────────┘
              ▼
         Driver → app
              │
     observed trajectory → VERIFIER → CI
```

**Always core:** description envelopes + at least one runner + verifier.  
**Never core:** user-sim worlds, quality scoreboards, “the YAML file runs itself.”

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
  User messages ──► MiniChatApp.handle() ──► ledger observation
                            │
                            ▼
               Conjecture IR + runner + verifier
                            │
               PASS only if expected state holds
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

That is one **runner** (CP `run_script`) playing a **ConjectureScript** (play-back form)
against a Driver (`handle`). The same envelopes can later be described in full
**Scenario** language and run by other runners — **who runs it** stays explicit.

---

## Script language note

Section below documents the **CP play-back form** (`ConjectureScript`) used by today’s
runner and E2E. The **generalized trajectory description** (actors, waits, nondeterminism
envelopes, profiles) lives in `experimental/Scenario` + `schema.json` — see CBR-SPEC.

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
