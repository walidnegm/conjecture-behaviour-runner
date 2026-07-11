# Documentation index

| Document | Type | Path |
|----------|------|------|
| **Conjecture Behaviour Runner Specification** | **Specification** (`CBR-SPEC`) | [SPEC.md](./SPEC.md) |
| Project face | README | [../README.md](../README.md) |
| **Agent coder guide** | Integration + golden authoring | [../AGENTS.md](../AGENTS.md) |
| **Script author prompt seed** | Trajectory + ODD → Conjecture Script | [../prompts/conjecture_script_author.seed.md](../prompts/conjecture_script_author.seed.md) |

## Canonical stack (all docs use this)

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

| Noun | Meaning |
|------|---------|
| **Authored trajectory** | Twists that can break state law |
| **Conjecture Scenario** | Flexible description language for that trajectory |
| **Conjecture Script** | Runnable play-back form (usual CI golden) |
| **Observed trajectory** | Evidence of one run |
| **Runner** | Who executes the Script (`run_script` = control-plane runner today) |
| **Verifier** | Expected envelopes vs observed trajectory |
| **Verdict** | Optional commercial product name — not the open-source judge |

**Maturity:** control-plane Script + `run_script` + verifier is usable now; full Scenario multi-runner stack is early. Collinear and peers are **seeds**, not rivals we out-feature.

- **CBR-SPEC §0** finalized claim · **§2** architecture · **§4.1** Script fields  
- **AGENTS.md** host adapter + agent workflow  
- **Prompt seed** STEP A (trajectory + ODD) → STEP B (Script JSON)  
- **Examples:** [Scenario YAML](../examples/scenario_sole_continue.yaml) · [authored Script trajectory](../examples/trajectory_authored_sole_continue.json) · [observed PASS/FAIL](../examples/)  

Legacy URL `conjecture-behaviour-runner.md` → [SPEC.md](./SPEC.md).
