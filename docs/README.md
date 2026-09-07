# Documentation index

| Document | Type | Path |
|----------|------|------|
| **Conjecture Behaviour Runner Specification** | **Specification** (`CBR-SPEC`) | [SPEC.md](./SPEC.md) |
| Project face (harness + **Quality Console**) | README | [../README.md](../README.md) · [Quality Console](../README.md#quality-console--conversational-agentic-quality) · [SDK sibling pair](../README.md#sibling-of-the-control-plane-sdk-adopt--prove) |
| **Quality Console screenshots** | Gallery | [images/console/](./images/console/) |
| **Candidate discovery** (expand + invent) | Templates + env | [../templates/candidate_author/README.md](../templates/candidate_author/README.md) · SPEC §2.2 |
| **Discovery path diagram** | SVG ladder | [images/discovery-pipeline.svg](./images/discovery-pipeline.svg) |
| **Pipeline stage tracker** | Portable contract | `pipeline_tracker` — same strip shape as Prose → Draft IR → Save |
| **Golden-turn audit** (sibling SDK template) | After-Act stage lens (0–6 + 5b) | [main README](../README.md#golden-turn-audit-same-template-as-the-sdk) · [CATALOG](../incidents/CATALOG.md) · [CCP golden turn](https://github.com/walidnegm/conversation-control-plane/blob/main/docs/conversation-control-plane-sdk.md#the-golden-turn--one-correct-turn-end-to-end) |
| **Conversational Authority Quality** (portable) | Category thesis | [conversational-authority-quality.md](./conversational-authority-quality.md) |
| **Package maturity** | Readiness disclosure | [MATURITY.md](./MATURITY.md) |
| **Portable failure-mode registry** | Machine SoT | [../incidents/registry.yaml](../incidents/registry.yaml) |
| **Portable catalog** (failure modes) | Human index | [../incidents/CATALOG.md](../incidents/CATALOG.md) |
| **Lexicon** (optional depth) | Host monorepo vocabulary | Host path `docs/the-language-of-building-ai-products.md` — not vendored here |
| **Incident → pattern playbook** | Learning loop | [../incidents/README.md](../incidents/README.md) |
| **Agent coder guide** | Integration + golden authoring | [../AGENTS.md](../AGENTS.md) |
| **Script author prompt seed** | Trajectory + ODD → Conjecture Script | [../prompts/conjecture_script_author.seed.md](../prompts/conjecture_script_author.seed.md) |

**Start with five concepts:** Script · Turn · Driver · Observation · Invariant.  
**Quality Console:** `conjecture ui` — programs, CAQ laws, multi-lens laundry gaps,
How we run, Coverage battery, Author → Runner → Verdict (see main README).  
Contributor guide: [../CONTRIBUTING.md](../CONTRIBUTING.md).  
**Claim hierarchy (CBR-SPEC §0)** is advanced reading — not required for a first PR.

## Canonical stack (architecture — face README leads with the demo)

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

- **CBR-SPEC §0** finalized claim · **§2** architecture · **§2.2** expander + inventor · **§4.1** Script fields  
- **AGENTS.md** host adapter + agent workflow + candidate discovery  
- **Prompt seed** STEP A (trajectory + ODD) → STEP B (Script JSON)  
- **Candidate author:** [templates/candidate_author/](../templates/candidate_author/) — invent first, expand second  
- **Examples:** [Scenario YAML](../examples/scenario_sole_continue.yaml) · [authored Script trajectory](../examples/trajectory_authored_sole_continue.json) · [observed PASS/FAIL](../examples/)  

Legacy URL `conjecture-behaviour-runner.md` → [SPEC.md](./SPEC.md).
