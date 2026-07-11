# Conjecture Behaviour Runner — public contract

| Field | Value |
|---|---|
| **Status** | Alpha (0.1) — **product vision** full; **Slice 0** portable surface shipping |
| **Product one-liner** | Behaviour-based evaluation for agentic multi-turn systems — **invariants and allowed outcomes**, not string equality |
| **Why it exists** | Vibe-coded / auto-coded systems accrete **unknown pathways** (probabilistic specs, weak or dynamic scope, changing requirements). You cannot inventory every path; you pin **behaviour contracts** that must hold when paths appear. |
| **Slice 0 (now)** | Multi-turn **control-plane** invariant testing (stub/freeze cognition) + optional CCP goldens |
| **Package** | `conjecture-behaviour-runner` · import `conjecture_behaviour_runner` |
| **Companion (reference domain)** | [Conversation Control Plane](https://github.com/walidnegm/conversation-control-plane) |

This document is the **public contract**. It states the full product shape first; Slice 0 is the first implementation cut, not a redefinition of the product as “only CCP tests.”

---

## 1. Problem (behaviour, not strings)

LLM and agentic systems — especially those grown by generation and iteration — fail in
**behaviour space**, not wording space.

| What goes wrong | Why string / snapshot checks miss it |
|---|---|
| **Wrong control flow** mid-task | Reply still “looks fine” |
| **Identity or state lost** across turns | No fixed sentence fails |
| **Illegal landing** (restart, wrong mode, silent degrade) | Snapshot of one turn still green |
| **Unknown pathway** after generated code | No test ever named that branch |
| **Scope drift** (feature reaches unmapped states) | Goldens updated to match, contracts not |

Exact reply text and frozen screenshots answer a different question. They do not pin
**who may act**, **what must stay bound**, or **which outcomes are legal**.

Evaluation must pin:

1. **Required invariants** (always true after a turn)  
2. **Allowed outcomes** (envelope of legal behaviours)  
3. Optionally **distribution** (outcome rates over N runs when cognition is live)  

That is the load-bearing idea of the **behaviour runner**. Conjecture is that product.
Slice 0 implements a first vertical on multi-turn control-flow contracts (stub/freeze
cognition) — not a claim that the product *is only* one domain’s unit tests.

The **objective is not skinned down** because the first phase is simpler. We still
build out ODD/scope, generation modalities, trajectories, UI drivers, and
distribution. Slice 0 is a thin vertical through a larger programme.

---

## 1.1 Behaviour-driven testing and ODD (full objective)

### Behaviour pinning

Agentic and auto-grown systems need **behaviour envelopes**, not exact reply text:

1. Declare **scope** of the claim (what inputs the system says it handles).  
2. Per step/turn: **`allowed_outcomes`** — legal landings (more than one is fine).  
3. **`required_invariants`** — must hold no matter which allowed outcome occurred.  
4. Run under an **execution profile** (stub cognition, live cognition, desktop/mobile, …).  
5. Capture a **trajectory**. Across *N* trajectories of the same (scenario, profile),
   pin **distributions** when cognition is live.

Without invariants + allowed outcomes, “happy path passed” cannot be told from
“happy path passed by accident.”

| Concept | Meaning |
|---|---|
| **Route network** | Map of transitions in the product (grows over time) |
| **Scenario** | One goal-directed route with contracts filled |
| **Trajectory** | One observed run of a scenario under one profile |

### Analogy: CARLA / AV scenarios — not Playwright, not LLM-feedback labs

Conjecture is methodologically closer to **scenario construction for autonomous
systems** (e.g. CARLA scenario runner, SOTIF edge-case work) than to:

- **Playwright-class E2E** — click → assert fixed UI text (UI may later be *a driver*, not the product);
- **LLM feedback / model-eval products** — score reply quality, preference data, synthetic users,
  RL signal, leaderboards. **We deliberately do not compete there.** Our primary verdict is
  **host behaviour contracts** (ownership, pins, legal landings, honest terminals), not
  “was the model’s answer good?”

Like AV scenario work: declare an **ODD**, collect **ground truth** (maps/sensors ↔ here:
code contracts, session traffic, explorer), build **scenarios**, generate **edge conditions**,
and pin **invariants / allowed outcomes** when the world is nondeterministic. Edge generation
from ground-truth collection is a later slice; Slice 0 seals the first contracts mid-flow.

### Scripts are multi-actor (user → agent → agent-to-agent)

A script is **not only a human chat transcript**. Turns may be:

| Actor / kind | Role in the script |
|---|---|
| **User** | Human message, chip, finite confirm |
| **Agent** | Specialist step, tool-backed continue, agent-initiated progress |
| **Agent → agent** | Handoff, subagent completion into parent, multi-agent pipeline |
| **System / completion** | Job complete, stream terminal, timeout, cancel, scheduled tick |

Experimental YAML already models this (`Actor`: `user` · `agent` · `system`).
Slice 0’s `DialogueTurn.user_text` is the **user-centric first API**, not the product ceiling.

**Product phasing:**

1. **User-centric (Slice 0+)** — human-led multi-turn scripts; pin-driven cognition.  
2. **Agent-initiated + completion** — steps with no new human utterance (async finish, mid-flight).  
3. **Agent-to-agent** — multi-agent handoffs under the same invariant envelope.  

Throughout: evaluate the **host system’s contracts**, not LLM feedback quality.

### ODD (Operational Design Domain)

**ODD** (ISO 21448 / SOTIF lineage) = specification of the **input space the system
claims to handle** — conditions under which intended function is in scope. It is
**metadata on the scenario class**, not a scenario and not a probe generator.

Portable scenario models use the same idea in plain language:

| Field | Meaning |
|---|---|
| `in_scope` | Supported — handle |
| `out_of_scope` | Unsupported — refuse / degrade gracefully |
| `expected_refusal` | Probes that must be rejected |

### ODD vs adversarial (do not conflate)

| | ODD / scope | Adversarial generation |
|---|---|---|
| **What** | Spec of the claimed boundary | Technique that *uses* the boundary |
| **In-scope stress** | — | “You claimed this — prove under load” |
| **Out-of-scope** | Declared | Refusal / non-crash contracts |
| **Layer** | Scenario-class metadata | Concrete corpus entries |

Adversarial is never the sole CI green without human promote.

### Where use-cases / scenarios are seeded (distinct sources)

Do **not** collapse “generation” into one blob. Seed sources differ in trust and job:

| Source | Input | Output kind | Trust | Status |
|---|---|---|---|---|
| **Specs** | Epics, ODD/scope, design contracts | *Intended* use-cases | High for “claimed” behaviour | **Partial** — humans author; **spec→scenario tooling not built out** |
| **Codebase scan** | Routers, state machines, tools, prompts, existing tests | *Structural* use-cases the code admits | High for “reachable in code” | **Partial** — Slice 0 goldens hand-derived; **auto scan→draft scripts not built out** |
| **Raw scripts / ideas / edge lists** | Free-form seeds, “what if…”, incident notes, sticky edges | *Hypothesis* scenarios and **edge conditions** | Variable — needs curation | **Partial** — hand-written `ConjectureScript`; **idea→formal probe pipeline not built out** |
| **User-watching** | Sessions, transcripts, telemetry | *Empirical* routes | High for “what people do” | **Not built out** |
| **Explorer** | Deployed app drive | *Operational* reachability | High for runtime quirks | **Not built out** |
| **Adversarial from ODD** | Scope + threat generation | *Stress / refusal* probes | Separate triage (refusal ≠ success) | **Seed only**; formal generator **not built out** |

```text
  specs ──────────────┐
  codebase scan ──────┼──► curate / promote ──► scenario + invariants
  raw ideas / edges ──┘         │
                                ▼
                          play back → capture → diagnose
                                │
              later: traffic · explorer · adversarial gen
```

**Slice 0** proves the **play back** column: pinned scripts + real invariant checks.
Automated extractors from specs, code, and raw edge lists are **roadmap**, not
pretend-done.

### Pipeline (still the objective)

```text
extract → curate/learn → play back → capture → diagnose → live debug
   ^                                                         |
   +------------------------- feedback ----------------------+
```

Slice 0 = thin vertical on **play back** (script → pin-driven run → pass/fail).
Extract (specs / code / ideas), curator, capture store, explorer, and formal
adversarial generation remain **to build**.

---

## 2. Product architecture (full runner)

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
|---|---|
| **Script / scenario** | Multi-turn steps, pins, expected contracts, allowed outcomes |
| **Cognition mode** | How labels are obtained: `stub` · `freeze` · `record` · `local` · `cloud` |
| **Driver** | How a step is applied (adapter today; later chat/SSE; later UI) |
| **Trajectory** | Evidence of one run under one profile (distribution later) |
| **Corpus** | Goldens humans own; later bootstrap and adversarial generation |

**Scripts assert host contracts** (control plane, ledger, or other adapter-projected state). They do not invent a second product model out of thin air — but the **host is not required to be CCP**. CCP is the reference binding for Slice 0.

---

## 3. Slice plan

| Slice | What |
|---|---|
| **0 (now)** | Portable script model (**user-centric** first), pin-driven harness, adapter protocol, invariant library, optional CCP stream adapter + 3 goldens |
| **1** | Path-faithful host chat / SSE driver; **agent-initiated + completion** turns (no new human message) |
| **2** | Scenario YAML + multi-actor steps (`user` · `agent` · `system`); optional UI harness as *one* surface driver |
| **3** | **Agent-to-agent** handoff scripts + corpus generation (code seed, styles, detours, adversarial / OOD) |
| **4** | Distribution monitoring when cognition is live |

Not in scope as a product line: **LLM feedback scoring** / preference datasets / model leaderboards.

Deterministic “click → assert fixed text” UI tests can remain outside this framework; UI is an optional **driver** for behaviour contracts, not the product definition.

---

## 4. Cognition modes

| Mode | Cognition | Proves |
|---|---|---|
| `stub` (default) | Pin on the turn | Behaviour contracts under fixed labels — CI-safe |
| `freeze` / `record` | Recorded pin JSON | Replay / capture |
| `local` / `cloud` | Host routes a real bounded classifier | Enum parity + same invariants |

The portable core is **pin-driven**. It does not call your LLM factory; hosts supply pins or a richer driver.

---

## 5. Public API (0.1 / Slice 0)

```python
from conjecture_behaviour_runner import (
    LlmMode,
    CognitionPin,
    DialogueTurn,
    InvariantSpec,
    LedgerEffect,
    ConjectureScript,
    ControlPlaneAdapter,   # Protocol
    NullControlPlaneAdapter,
    BaseControlPlaneAdapter,
    check_standard_invariant,
    run_script,
)
```

Implement `ControlPlaneAdapter` (or subclass `BaseControlPlaneAdapter`) against your ledger or the Conversation Control Plane package. The null adapter is packaging smoke only.

**Optional CCP binding:**

```python
from conjecture_behaviour_runner.contrib.control_plane import (
    ControlPlaneStreamAdapter,
    control_plane_golden_scripts,
)
```

Requires `pip install conjecture-behaviour-runner[control-plane]`.

**Experimental** (not stable 0.1 API): `conjecture_behaviour_runner.experimental` — scenario YAML models and trajectory shapes for later surface drivers. YAML loading needs `pip install conjecture-behaviour-runner[scenarios]` (PyYAML).

---

## 6. Explicit non-goals

- Replacing all unit tests with multi-turn scripts  
- Live LLM on every PR by default  
- Browser as the *only* truth for ownership / mid-flow bugs  
- Phrase laundry lists as scenario generators (cognition stays label-based; scripts pin outcomes and owners)  
- Claiming Conjecture *is* the Conversation Control Plane (it **proves** contracts; CCP **is** one contract surface)

---

## 7. License & status

MIT. Alpha.

| Horizon | Intent |
|---|---|
| **Product** | Full behaviour runner: scenarios, trajectories, drivers, generation, distribution |
| **Slice 0** | Control-plane multi-turn invariants + portable package + CCP goldens |
| **Next** | Path-faithful chat · scenario/UI surface · corpus · N-run distribution |

Host adapters and product-private goldens stay in host repos; this package keeps a portable, leak-free surface.
