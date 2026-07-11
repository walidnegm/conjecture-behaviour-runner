# Conjecture Behaviour Runner

**Contract testing for the conversational control plane** —  
**behavioral envelopes** (allowed outcomes + invariants) over **authoritative state**,  
under **pinned or replayed cognition**.

Not “one golden sentence.” Not a new universal testing paradigm.  
The wedge: **authoritative control-plane conformance under probabilistic cognition.**

Built by [Bot0.ai](https://bot0.ai). MIT open source · Alpha **0.1.2**

| | |
|---|---|
| **GitHub** | [github.com/walidnegm/conjecture-behaviour-runner](https://github.com/walidnegm/conjecture-behaviour-runner) |
| **Import** | `conjecture_behaviour_runner` |
| **Spec (normative)** | [`docs/SPEC.md`](docs/SPEC.md) — **CBR-SPEC** |
| **Agent guide** | [`AGENTS.md`](AGENTS.md) |
| **Prompt seed** | [`prompts/conjecture_script_author.seed.md`](prompts/conjecture_script_author.seed.md) |

On conflict: **SPEC** wins for contracts; **AGENTS.md** for agent workflow.

---

## Claim and stack

| Noun | Meaning |
|------|---------|
| **Authored trajectory** | Load-bearing **twists** that can break state law |
| **Conjecture Scenario** | Flexible **description** of that trajectory (scope, profiles, waits, nondeterminism…) — not tied to one driver |
| **Conjecture Script** | **Runnable play-back** for a chosen runner (usual CI golden) |
| **Runner** | Who executes (today: control-plane `run_script`) |
| **Observed trajectory** | Evidence of one run → input to the **Verifier** |
| **Green bar** | State law under pin/freeze — **not** reply wording |
| **Verdict** | Optional commercial product — separate from OSS **Verifier** |

**Mnemonic:** Scenario *describes* · Script *plays* · observed *happened* · Verifier *judges*.

**Maturity:** control-plane Script + `run_script` + verifier is usable now (E2E mini-app, CCP goldens). Full Scenario multi-runner stack is **early**. Collinear-class tools are **path seeds**, not rivals.

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
              │ Driver plugin (HTTP · Playwright · LangGraph · …)
              ▼
       Real application
              │
     OBSERVED TRAJECTORY → VERIFIER → pass/fail
              │
       pytest / CI only *hosts* the run
```

Normative detail: **[CBR-SPEC §0](docs/SPEC.md#0-finalized-product-claim-normative)**.

---

## Try this first (E2E)

Same sole-continue path used everywhere: open cost-out → continue; assert **owner / pin / `blocks_resolve`**, not wording.

```bash
git clone https://github.com/walidnegm/conjecture-behaviour-runner.git
cd conjecture-behaviour-runner
pip install -e ".[dev]"
python examples/e2e_multi_turn.py
# or: conjecture path-faithful --prove-bugs
```

| Run | Result | Why |
|-----|--------|-----|
| Healthy continue | **PASS** | Mid-flight contracts hold under freeze |
| Bug: continue steals to front door | **FAIL** | Dual owner — reply can still look fine |
| Bug: continue drops `workflow_id` | **FAIL** | Lost identity pin |
| Bug: continue wipes the task | **FAIL** | Illegal restart mid-flight |

**FAIL** = `TurnObservation` violates the Script’s expected contracts (see Verifier in CBR-SPEC §4.1). Not a quality score.

---

## Examples (one path, three shapes — no repeats here)

All of these encode the **same** sole-continue trajectory. Prefer the files over pasting prose twice.

| Shape | File | Role |
|-------|------|------|
| **Scenario** (description) | [`examples/scenario_sole_continue.yaml`](examples/scenario_sole_continue.yaml) · [`.json`](examples/scenario_sole_continue.json) | Rich language: scope, profiles, waits, nondeterminism, evidence, terminals |
| **Script** (authored trajectory / golden) | [`examples/trajectory_authored_sole_continue.json`](examples/trajectory_authored_sole_continue.json) | Turns + expected envelopes the runner plays |
| **Observed** (run evidence) | [`trajectory_observed_pass.json`](examples/trajectory_observed_pass.json) · [`…_fail_dual_owner.json`](examples/trajectory_observed_fail_dual_owner.json) | What PASS / FAIL look like after Act |
| **Scenario → run** | [`examples/scenario_compile_and_run.py`](examples/scenario_compile_and_run.py) | validate → compile Script → PASS + dual_owner FAIL |
| **E2E driver** | [`examples/e2e_multi_turn.py`](examples/e2e_multi_turn.py) | MiniChatApp + planted bugs |
| **Portable Script** | [`examples/sole_continue_golden.json`](examples/sole_continue_golden.json) | Adapter-oriented effects variant |

```bash
pip install -e ".[dev,scenarios]"
python examples/scenario_compile_and_run.py
```

Index: [`examples/README.md`](examples/README.md).

---

## What we assert

| Assert (control-plane ground truth) | Do **not** assert (default wedge) |
|-------------------------------------|-----------------------------------|
| Who **owns** the turn | “The reply was good” |
| **Pin** identity bound / stable | Exact assistant wording |
| **Legal landing** (`allowed_outcomes`) | Preference / rubric scores |
| Mid-flight law (`blocks_resolve`, no illegal restart) | Full domain math (unless host projects it) |

A CI golden is **probe + expected result**. Path without expected envelopes is a tour, not a merge gate.

### Script building blocks

| Piece | Role |
|-------|------|
| `ConjectureScript` | Golden: turns, optional `scope`, `trajectory_invariants` |
| `DialogueTurn` | Stimulus + pin + **expected** invariants / outcomes |
| `CognitionPin` | Frozen cognition labels (CI-safe) |
| `InvariantSpec` | State rule after the turn |
| `allowed_outcomes` | Legal landings (requires `observed_outcome` if set) |
| `ScriptScope` | Mini-ODD: in / out / expected_refusal |

**Common verifier kinds:** `exclusive_owner` · `active_kind` · `pin_present` / `pin_equals` · `extra_true` / `extra_false` · `observed_outcome` · trajectory kinds in `temporal.py`. Unknown kinds **fail closed**. Full tables: [SPEC §4.1](docs/SPEC.md#41-script-structure-slice-0--multi-turn-design).

### How a run works

```text
  Conjecture Script
        │  control-plane runner (run_script)
        ▼
  CognitionProvider (stub | freeze | record)
        │  Driver / adapter Act → TurnObservation
        ▼
  VERIFIER → OBSERVED TRAJECTORY (RunResult) · JSON/JUnit
        │
  pytest / CI only *hosts*
```

---

## What ships (0.1.2)

| Area | Status |
|------|--------|
| Scenario (`experimental/`, schema, examples) | ✅ experimental |
| Script + scope + load JSON/YAML | ✅ stable |
| Runner + CognitionProvider + FreezeStore | ✅ |
| Verifier (step + temporal + outcome-specific) | ✅ |
| CLI (`run`, `path-faithful`, JSON/JUnit) | ✅ |
| Path-faithful mini-app + planted bugs | ✅ |
| CCP stream goldens (`[control-plane]`) | ✅ |
| Scenario → Script compile bridge | ✅ experimental |
| LangGraph / Crew / Temporal / HTTP / Playwright | ⬜ roadmap |

Companion domain: [conversation-control-plane](https://github.com/walidnegm/conversation-control-plane).

---

## Quickstart

```bash
pip install -e ".[dev]"
pytest tests/ -q
python examples/e2e_multi_turn.py

# optional
pip install -e ".[dev,control-plane,scenarios]"
python examples/control_plane_goldens.py
python examples/scenario_compile_and_run.py
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

Real checks: implement `ControlPlaneAdapter` / `BaseControlPlaneAdapter`, or use
`path_faithful.MiniAppAdapter` / `contrib.control_plane.ControlPlaneStreamAdapter`.

---

## Who this is for · Non-goals · Contribute

**For:** multi-turn / agentic apps (including LangGraph / Crew / Temporal hosts); teams
where replies “look fine” but owner/pin/terminal law breaks; freeze-safe CI gates.

**Not:** replace Playwright/pytest/orchestrators; built-in user-sim worlds; live LLM on
every PR by default; model leaderboards.

**MIT contributions:** drivers, providers, verifier kinds, adapters, docs — portable only;
no host-private goldens. **Verdict** (commercial, optional): hosted/studio/SSO/SLA — may
diverge; does not block OSS. Maps: [CBR-SPEC §8](docs/SPEC.md#8-contributions-verdict-and-foundational-ideas).

---

Copyright © Bot0.ai / contributors. MIT.
