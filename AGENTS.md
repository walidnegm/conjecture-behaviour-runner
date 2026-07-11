# AGENTS.md — Conjecture Behaviour Runner

**Audience:** coding agents (and humans) integrating a host app or authoring goldens.  
**Normative product claim:** [docs/SPEC.md](docs/SPEC.md) (**CBR-SPEC**).  
**Face demo:** [examples/e2e_multi_turn.py](examples/e2e_multi_turn.py) — path-faithful `handle()` + planted bugs.  
**Prompt seed:** [prompts/conjecture_script_author.seed.md](prompts/conjecture_script_author.seed.md).

**Claim hierarchy** (do not invert — CBR-SPEC §0):

1. **Face (plain):** catch agent bugs that **still look fine in chat** — CI fails on broken
   conversation **rules** (owner / locked record / illegal restart), not on wording.  
   *Precise:* freeze-safe state-law regression under pin/freeze.
2. **Technical (sticky):** contract testing — behavioral envelopes over authoritative state
   under pin/freeze. Not one golden sentence; not a prose grader.
3. **Architecture (scoped):** control-plane conformance under probabilistic cognition —
   **only** for CCP-shaped hosts with real Act under a Driver.

**Inspiration / apt hosts:** [Conversation Control Plane](https://github.com/walidnegm/conversation-control-plane)
and apps **isomorphic** to that format (single-writer ownership, entity pins, sole-continue /
terminal discipline). Transactional multi-turn systems — not pure creative chat.

---

## 0. What you are integrating

Day-to-day surface: **golden (Script) · run · verifier**. Richer names are architecture.

| Piece | Package surface | Your job |
|-------|-----------------|----------|
| **Conjecture Script** (usual golden) | `ConjectureScript`, `DialogueTurn`, `InvariantSpec` | Turns + **expected state** — this *is* the test case |
| **Runner** | `run_script(...)`, CLI `conjecture run` | Supply Driver + cognition (stub/freeze) |
| **Verifier** | standard + temporal kinds | `kind` + `expected`; never free-form prose rules |
| **Host binding** | `ControlPlaneAdapter` / `BaseControlPlaneAdapter` | Map **your** ledger/graph → `TurnObservation` (Act path preferred) |
| **Conjecture Scenario** (optional) | `experimental.Scenario` | Rich description; compile → Script. Example: `examples/scenario_sole_continue.yaml` |
| **Observed trajectory** | `RunResult` | Evidence of one run — **output** |

**Green bar:** owner, pins, legal landings, mid-flight law under pin/freeze — **not** reply wording.  
**Trap:** do not author goldens that assert adjectives / style.

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

**Trajectory is not optional vocabulary.** Scenario/Script *carry* an authored trajectory of
twists; the runner produces an **observed** trajectory; the verifier compares them to
expected envelopes.

**Maturity:** control-plane Script + `run_script` is what works end-to-end today. Full
Scenario multi-runner stack is earlier. Prefer honest scope over platform theater.

**Seeds:** Collinear-class and other multi-turn tools are **welcome path inputs** — attach
expected state, then run our verifier. Do not reimplement their sim inside this package.

Without a **runner + verifier**, Scenario/Script files are inert.

---

## 1. Non-negotiables (do not violate)

1. **Cognition ≠ execution.** Pins/labels come from stub/freeze (or host provider). Code owns state transitions and pass/fail.  
2. **Expected required for CI goldens.** Each gating script needs invariants and/or `allowed_outcomes` (and/or trajectory invariants). Path-only scripts are exploratory, not merge gates.  
3. **Arrange ≠ Act.** `LedgerEffect` seeds environment. Path-faithful Act goes through the real host surface (`handle` / graph invoke / Temporal signal).  
4. **Fail closed.** Unknown invariant kinds fail. `allowed_outcomes` set ⇒ `observed_outcome` must be set.  
5. **No phrase laundry lists** to decide what the user meant — pins carry structured labels.  
6. **Do not reimplement** Playwright, sim worlds, or eval scoreboards inside this package. Drivers are plugins.  
7. **Naming:** pass/fail engine is **Verifier** (not Oracle Corp). Commercial product may be **Verdict** — separate.  
8. **Not a chat validator.** Expected contracts are state law only — never prose quality as the green bar.

---

## 2. Integrate a host (adapter checklist)

```python
from conjecture_behaviour_runner import (
    BaseControlPlaneAdapter,  # or ControlPlaneAdapter protocol
    TurnObservation,
    run_script,
    LlmMode,
    load_script_json,
)

class MyHostAdapter(BaseControlPlaneAdapter):
    def apply_effect(self, context, effect):
        # ARRANGE only — seed pins/tasks for the test, not fake Act
        ...
        return context

    def observe_turn(self, *, context, user_text, pin):
        # ACT: call YOUR app / LangGraph / Temporal / Crew, then project state
        # result = my_app.handle(user_text, pin=pin)  # or graph.invoke(...)
        return TurnObservation(
            exclusive_owner=...,   # who owns mid-flight
            active_kind=...,
            pins={...},            # entity ids
            context=...,           # None = no update; {} = clear; dict = replace
            observed_outcome=...,  # required if script has allowed_outcomes
            extras={               # host flags, e.g. blocks_resolve
                "blocks_resolve": ...,
            },
        )
    # check_invariant inherited from BaseControlPlaneAdapter
```

| Host | Act surface | Project into observation |
|------|-------------|---------------------------|
| Plain Python / chat | `handle(message)` | ledger / session |
| **LangGraph** | `graph.invoke` / stream | checkpoint, thread state |
| **CrewAI** | kickoff / step | active agent, task status |
| **Temporal** | start / signal / query | workflow status, search attrs |
| **HTTP / SSE** | POST chat / stream events | response + server state read |

Reference path-faithful demo: `path_faithful.MiniAppAdapter` + `examples/e2e_multi_turn.py`.

---

## 3. Author a golden (human or agent)

**Load-bearing trajectory script:** describe the **twists and turns** that can stress the
control plane, then bind **invariants / allowed outcomes** at those landings.

1. Name the **scenario class** (sole-continue, detour, handoff, terminal) — not a full 30-turn transcript.  
2. List load-bearing **twists** (continue, detour, ambient, complete…) — that *is* the path story.  
3. Seed mid-flight if needed (`effects` / `initial_context`).  
4. For each critical twist, declare **expected**: `invariants`, optional `allowed_outcomes`, optional trajectory rules.  
5. Prefer **freeze** pins for CI (`CognitionPin` / freeze store).  
6. Prove the golden fails if law breaks (plant opposite bug once).  

Path without invariants = a tour. Twists **with** invariants = a test.

### Minimal Conjecture Script shape

```json
{
  "script_id": "my_sole_continue",
  "description": "continue keeps owner and pin",
  "conversation_id": "conv_x",
  "scope": {
    "in_scope": ["mid-flight sole-continue"],
    "out_of_scope": ["model quality scoring"],
    "expected_refusal": ["illegal restart mid-flight"]
  },
  "turns": [
    {
      "actor": "user",
      "user_text": "…",
      "pin": { "task_intent": "continue" },
      "invariants": [
        { "kind": "exclusive_owner", "expected": "my_kind" },
        { "kind": "pin_present", "expected": "workflow_id" }
      ],
      "allowed_outcomes": ["continue_owned"]
    }
  ]
}
```

Load: `load_script_json(path)` → `run_script(script, adapter=..., llm_mode=LlmMode.STUB)`.

### Standard verifier kinds (portable)

`exclusive_owner` · `owner_not` · `active_kind` · `kind_equals` ·  
`pin_present` · `pin_absent` · `pin_equals` · `pin_key_missing` ·  
`extra_true` · `extra_false` · `extra_equals` · `extra_missing` ·  
`observed_outcome` · `always_true`  

Trajectory: `eventually_exclusive_owner` · `never_exclusive_owner` · `pin_stable` ·  
`owner_changes_at_most` · … — see `temporal.py` / CBR-SPEC §4.1.

---

## 4. Agent-written artifacts *are* the test case

**Design fact:** what an agent (or human following the same schema) **writes into
`ConjectureScript` / Scenario description is more likely to *be* the golden** than
any free-form chat about “we should test sole-continue.”

| Agent writes… | Role |
|---------------|------|
| Valid Script + **expected** kinds/outcomes | **The test case** (merge-gate input) |
| Long NL “test plan” prose | Not executable — not the test |
| Path-only JSON, empty invariants | Sketch only — not a CI gate |

So agent-coding integration is not “help write docs about tests.” It is **emit the
artifact the runner already knows how to run.** The prompt seed exists so the agent
defaults to that artifact shape.

**Still human/product-owned:** *which* laws (owners, pins, refusals). Agents must not
invent product rules; they **encode** stated rules into a Script. If the law is unknown, ask.

## 5. Agent coder workflow (recommended)

```text
1. Read CBR-SPEC §0 (claim) + this AGENTS.md
2. Read host control-plane / ledger / graph state (what is authoritative)
3. Pick scenario class + expected laws (product rules, not model vibes)
4. Use prompts/conjecture_script_author.seed.md:
   STEP A — trajectory of twists + ODD/scope (ours or mapped from Collinear/others)
   STEP B — emit Conjecture Script JSON → that Script *is* the test case once validated
5. Validate: load_script_json / script_from_dict (fail closed on bad shape)
6. Implement or extend host adapter observe_turn (Act → TurnObservation)
7. run_script STUB or FREEZE; assert RunResult.passed
8. Plant one opposite bug; prove FAIL
9. Wire pytest / conjecture run + freeze dir in CI
```

**Do not:** generate long NL transcripts with empty invariants.  
**Do:** short probe + expected state at critical moments — **that file is the test.**

---

## 6. CLI cheatsheet

```bash
pip install -e ".[dev]"
python examples/e2e_multi_turn.py          # in-repo multi-turn demo
conjecture path-faithful --prove-bugs     # same story via CLI
conjecture run path/to/goldens/ --adapter path-faithful --json-report out.json
```

Modes: `stub` (default) · `freeze` / `record` need `--freeze-dir`.

---

## 7. Files to open first

| Path | Why |
|------|-----|
| [docs/SPEC.md](docs/SPEC.md) | Normative CBR-SPEC |
| [prompts/conjecture_script_author.seed.md](prompts/conjecture_script_author.seed.md) | Seed prompt for script authoring agents |
| [examples/e2e_multi_turn.py](examples/e2e_multi_turn.py) | Full E2E multi-turn conversation |
| [src/conjecture_behaviour_runner/protocol.py](src/conjecture_behaviour_runner/protocol.py) | Adapter + observation contract |
| [src/conjecture_behaviour_runner/path_faithful.py](src/conjecture_behaviour_runner/path_faithful.py) | Mini-app Act + planted bugs |
| [src/conjecture_behaviour_runner/invariants.py](src/conjecture_behaviour_runner/invariants.py) | Portable verifier kinds |

---

## 8. Out of scope for agent patches

- Vendor sim/eval platforms as core  
- Keyword routing on free-text user meaning  
- Softening fail-closed kinds “to make CI green”  
- Host-private product goldens committed to this public tree  
