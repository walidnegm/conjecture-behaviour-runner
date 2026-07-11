# Conjecture Behaviour Runner Specification

| Field | Value |
|---|---|
| **Document type** | **Specification** (normative) |
| **Document ID** | `CBR-SPEC` |
| **Canonical path** | [`docs/SPEC.md`](./SPEC.md) |
| **Title** | Conjecture Behaviour Runner Specification |
| **Version** | **0.1.2** (alpha) — claim + implementation surface aligned with code |
| **Status** | **Active** — authoritative for IR, runner, verifier, scope; foundations ship |
| **Audience** | Integrators, contributors, agent authors of goldens |
| **Companion face** | [README](../README.md) — project face (green bar, E2E, script language) |
| **Agent coder guide** | [AGENTS.md](../AGENTS.md) — integrate host + author goldens |
| **Prompt seed** | [prompts/conjecture_script_author.seed.md](../prompts/conjecture_script_author.seed.md) |
| **Implementation package** | `src/conjecture_behaviour_runner/` · version **0.1.2** |
| **One-liner (locked)** | Contract testing for the conversational control plane — behavioral envelopes over authoritative state under pinned or replayed cognition |
| **Package** | `conjecture-behaviour-runner` · import `conjecture_behaviour_runner` · **MIT** |
| **Reference domain** | [Conversation Control Plane](https://github.com/walidnegm/conversation-control-plane) |

**What “Specification” means here:** this document is the **normative source of truth** for
behaviour, contracts, and extension points. Code implements it; the README popularizes it.
It is **not** a marketing brief, ADR log, or epic backlog (those live elsewhere).

---

## 0. Finalized product claim (normative)

This section freezes the market/architecture decisions from design review. Later
slices implement; they do not redefine the wedge without a SPEC version bump.

### One-liner (locked)

> **Contract testing for the conversational control plane** —  
> **behavioral envelopes** (allowed outcomes + invariants) over **authoritative state**,  
> under **pinned or replayed cognition**.

Not “one golden sentence.” Not a new universal testing paradigm.  
**Wedge:** authoritative **control-plane conformance** under probabilistic cognition.

### What we test (and what we do not)

| We test | We do **not** primarily test |
|---|---|
| **Control-plane law:** exclusive owner, active kind, entity pins, mid-flight vs front door, detours, terminals, blocks_resolve / no illegal restart | Model wording quality, preference scores, leaderboards |
| **Behavioral envelopes:** legal landings + state that must hold | Single ideal trajectory only |
| **Ground truth on state:** expected outcomes + invariants (required for CI goldens) | Hypothesis-only scripts with no expected result |
| Optional later: domain facts *if* projected into observation + verifier kinds | Built-in full domain sim / world model |

**Default product scope = multi-turn control-plane contracts.**  
The *shape* (IR + runner + verifier over projected state) can host more, but we do not
market “test the whole agent” until domain ground truth is first-class.

### Product = language + who runs it + who judges (locked)

**Do not collapse these.** Recent docs over-narrowed “IR” to `ConjectureScript` (the
control-plane *driver form*). The original design is wider:

| Layer | What it is | Not the same as |
|---|---|---|
| **Trajectory / scenario description language** | Generalized **input**: actors, steps, scope/ODD, nondeterminism, **allowed_outcomes**, **required_invariants**, waits, evidence, execution profiles | A single Python harness or Playwright |
| **Who runs the trajectory** | A **runner** + **Driver**: control-plane adapter, HTTP/SSE, Playwright, LangGraph, Temporal, … | The description file itself |
| **Observed trajectory** | Evidence of **one** run under one profile (`Trajectory` / `RunResult`) | The authored scenario |
| **Verifier** | Judges envelopes vs observation (portable kinds) | The driver / orchestrator |

```text
  Scenario / trajectory DESCRIPTION (flexible language)
       │  actors · steps · scope · allowed_outcomes · required_invariants · waits
       │
       ▼  compile / bind for a runner
  Execution form (e.g. ConjectureScript for CP runner, or UI plan for Playwright)
       │
       ▼  WHO RUNS IT (pluggable)
  Runner + Driver ──► app / graph / browser / workflow
       │
       ▼  observed trajectory (evidence)
  Verifier ──► pass/fail on expected envelopes
```

| Core | Name | Role |
|---|---|---|
| **Description IR** | `Scenario` (+ related models) · portable envelopes | Flexible trajectory *language* — **input** |
| **Play-back form** | `ConjectureScript` (Slice 0 stable) | Thin compile target for the **control-plane runner** today |
| **Runner** | `run_script` / CLI / future UI runners | **Who executes** steps (one of several possible runners) |
| **Verifier** | invariants + temporal | Judge pass/fail (not Oracle Corp; not commercial **Verdict**) |

**Without a runner + verifier**, description files alone are inert YAML.  
**Without a generalized description language**, you only have an ad-hoc driver API.

`ConjectureScript` is the **first sealable play-back form** for control-plane mid-flight
law — **not** a replacement for the full scenario/trajectory language.

### Orchestration engines (LangGraph, Crew, Temporal, …)

**Compose — do not replace.** Engines orchestrate; Conjecture gates law.

```text
  LangGraph / CrewAI / Temporal / custom FSM / …
              │  owns graph, agents, workflows, activities
              ▼
     Driver + Observer adapter  ──►  Conjecture runner + verifier
              │                              ▲
              ▼                              │
        app / tools / ledger          freeze + expected contracts
```

| Engine | Typical fit |
|---|---|
| **LangGraph** | Driver: invoke/stream graph; Observer: checkpoint / thread state → owner, pins, outcome |
| **CrewAI / multi-agent** | Agent→agent turns; exclusive owner; pin across handoff; no dual writer |
| **Temporal** | System/completion turns; job done / cancel / timeout; no mutate-after-terminal |
| **Others** | Same adapter pattern: project runtime state → `TurnObservation` |

Shipping first-party packages for each engine is **roadmap**; the **extension contract** is finalized.

### How we sit in the stack (locked — differentiate by job, not brand tables)

We do **not** define Conjecture as “unlike Product X.” We define it by **job and green bar**.

| Layer | Examples | Relationship to Conjecture |
|---|---|---|
| **Orchestration** | LangGraph, Crew, Temporal, custom FSMs | **Hosts** — they run work; we gate state law via Driver/Observer |
| **UI / transport drivers** | Playwright, HTTP, SSE, WebSocket | **Plugins** called by *our* runner |
| **Process host** | pytest, CI, JUnit | Invokes `conjecture run` — not the verifier |
| **Exploration / sim / eval (optional)** | Multi-turn sim labs, trajectory scorers | May **seed** paths or score in parallel; **do not set our green bar** |
| **Commercial (optional)** | **Verdict** | Hosted/faster/different surface; may use or reimplement cores |

**Our green bar (differentiation):** declared control-plane (and projected) contracts hold
under pinned/frozen cognition. That is the product. Everything else is input or plugin.

### Ground truth (required for helpful goldens)

A CI golden is a **probe + expected result**, not a hypothesis sketch:

- **Expected:** `allowed_outcomes` and/or invariants (step and/or trajectory)  
- **Optional later:** observation snapshot, terminal bucket, domain asserts  
- **Exploratory** scripts (no expected) must not gate merge  

Authoring (human or agent) must emit expected contracts against the schema.

### What “green” means

| Green means | Green does **not** mean |
|---|---|
| Declared control-plane (and any projected) contracts held under pinned/frozen cognition | The model’s prose was good |
| Verifier passed on observations from the host adapter | Every orchestration edge was exhaustively explored |

### Doc balance (README vs this Specification)

| | **README** | **This Specification (`CBR-SPEC`)** |
|---|---|---|
| **Document type** | Project face / getting started | **Specification** (normative) |
| **Job** | Why / how to start / friendly script language | Design, tables, field contracts, scope |
| **Pipeline · ecosystem · scope** | Short face + links here | **Full** diagrams and extension map |
| **Script IR** | Intro + kinds + mini story | Field tables, multi-turn patterns, mid-flight state machine, golden JSON |
| **Contributions / Verdict** | One paragraph + link | **Full** maps and commercial boundary |
| **On conflict** | Follow **this Specification**; update README |

Claims below distinguish **what is true today** from **aspiration**.

---

## 1. Problem and claim

### What is genuinely valuable

Probabilistic conversational systems should be tested against a **behavioral envelope** —
**permitted outcomes** plus **invariants over authoritative state** — not against one exact
sentence or one ideal trajectory.

| Ingredient | Role |
|---|---|
| **Cognition pins** | Separate probabilistic semantic interpretation from deterministic execution testing |
| **Allowed outcomes** | Multiple conversational landings can be correct |
| **Invariants** | Must remain true regardless of wording or path |
| **Authoritative focus** | Ownership, active work identity, routing, terminals, ledger integrity |

None of those ingredients is novel alone. The defensible combination is:

> **Authoritative control-plane conformance under probabilistic cognition.**

Not “a completely new testing paradigm.”

### Failure modes that string / pure quality scores miss

| What goes wrong | Why wording checks miss it |
|---|---|
| **Wrong control flow** mid-task | Reply still “looks fine” |
| **Identity or state lost** across turns | No fixed sentence fails |
| **Illegal landing** (restart, wrong mode, silent degrade) | Snapshot of one turn still green |
| **Dual writers / steals** | Trajectory “score” can still be high |

### Slice 0 honesty (critical)

Reference goldens largely:

1. **Inject** a cognition pin  
2. **Inject** ledger effects (`begin_task`, pins, ambient)  
3. Run **pure** control-plane projection functions  
4. Assert owner / pin / extras  

That establishes:

> Given the state transition I injected and the classification I supplied, does the
> contract function return the expected owner / pin / blocks_resolve?

It does **not** yet establish:

> When a user sends this message to the **deployed application**, does classify → route →
> mutate → tools → respond while preserving the contract?

So Slice 0 is a **valuable unit-level contract harness**. NL on the turn is partly
**documentary** until a real **Driver** path exists. `LedgerEffect` should be used for
**arrange / environment** (and external stimuli), not as a substitute for the system’s
own Act side effects long-term.

**Arrange → Act → Observe → Assert** is the target run shape.

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
| **Route network** | Map of transitions in the system under test (grows over time) |
| **Scenario** | One goal-directed route with contracts filled |
| **Trajectory** | One observed run of a scenario under one profile |

### Related work (compose; do not straw-man)

| Related | Relation to Conjecture |
|---|---|
| **Playwright** | Complete execution substrate. Conjecture sits **above** it as verifier semantics; Playwright can be **a Driver** (fixtures, traces, isolation). Do not rebuild Playwright. |
| **Cucumber** | Readable scenarios + step defs that can assert **any** state. Not “exact string only.” Conjecture is specialized agent/control-plane verifiers; integration is possible. |
| **Hypothesis stateful** | Closest **method** analogue: actions → transitions → invariants → **shrink**. Without generation/shrink, Slice 0 is a **hand-authored** transition API. |
| **Eval platforms** (LangSmith, Braintrust, DeepEval, Promptfoo, Inspect, Phoenix, …) | Already multi-turn / trajectory / tools. Differentiation is **narrower**: verify **authoritative-state contracts** for all acceptable trajectories — not “they only score the model.” |
| **Sim / eval platforms** | Different job (explore or score trajectories). We may consume path seeds; our green bar remains **state contracts under freeze**. |
| **CARLA / Scenic** | Method aspiration for generation under ODD later — not claimed for current code. |

### Canonical pipeline (target — partial today)

```text
Scenario source → validated Scenario IR → ExecutionPlan
       → Runner (Driver + CognitionProvider + Observer)
       → Trajectory → Verifier results → Report
```

| Layer today (0.1.2) | Status |
|---|---|
| `ConjectureScript` / `run_script` / `RunResult` | **Stable** |
| CognitionProvider + FreezeStore (stub / freeze / record) | **Shipped** — local/cloud still host-supplied |
| Verifier: standard + temporal + outcome-specific | **Shipped** — richer temporal / domain kinds open |
| CLI: `run`, `path-faithful`, JSON/JUnit, discovery | **Shipped** — shards/retries/timeouts open |
| Path-faithful mini-app + planted bugs | **Shipped** (credibility vertical) |
| Experimental `Scenario` / `Trajectory` + compile bridge | **Partial** — compile + trajectory bridge; not full rich runner |
| LangGraph / Crew / Temporal / HTTP / Playwright adapters | **Roadmap** — extension contract locked in §0 |

Free-form experimental preconditions/postconditions as **strings** are **descriptions** until a
typed predicate registry or callables exist — do not treat them as executable truth.

### Scripts are multi-actor (user → agent → agent-to-agent)

A script is **not only a human chat transcript**. Turns may be:

| Actor / kind | Role in the script |
|---|---|
| **User** | Human message, chip, finite confirm |
| **Agent** | Specialist step, tool-backed continue, agent-initiated progress |
| **Agent → agent** | Handoff, subagent completion into parent, multi-agent pipeline |
| **System / completion** | Job complete, stream terminal, timeout, cancel, scheduled tick |

Experimental YAML already models this (`Actor`: `user` · `agent` · `system`).
Slice 0’s `DialogueTurn.user_text` is the **user-centric first API**, not the design ceiling.

**Roadmap phasing:**

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

## 2. Project architecture

### What Conjecture *is* (description language + runners + verifier)

Without **runners** and **verifier**, scenario/trajectory files are inert.  
Without a **generalized description language**, you only have a one-off driver API.

| Layer | Owns | Ships today (0.1.2) |
|---|---|---|
| **Description language** | Flexible trajectory input (`Scenario`, scope, nondeterminism, waits, evidence) | `experimental/scenario_models.py`, `schema.json` |
| **Play-back form** | CP-oriented compile target (`ConjectureScript`) | `script.py`, JSON/YAML load |
| **Runner(s)** | **Who executes** the trajectory via a Driver | **CP runner:** `run_script` + CLI; others roadmap |
| **Verifier** | Pass/fail on envelopes vs observation | `invariants.py`, `temporal.py` |
| **Observed trajectory** | Evidence of one run | `RunResult`; `experimental/trajectory.py` |

```text
   authors / seeds
        │
        ▼
   Scenario / trajectory DESCRIPTION  (generalized language)
        │
        ├── compile ──► ConjectureScript ──► CP runner (run_script) ──┐
        │                                                              │
        └── (later) UI / other plans ──► Playwright / other runners ──┤
                                                                       ▼
                                                              Driver → app
                                                                       │
                                                              observed trajectory
                                                                       │
                                                              VERIFIER (shared)
```

**Who runs the trajectory?** Explicit choice of runner + Driver — not implied by the file alone.

| Piece | Role |
|---|---|
| Specs, agents, humans, path seeds | Author **description** (+ expected envelopes) |
| CP runner / future UI runners | **Who runs** it |
| Playwright / HTTP / LangGraph / Temporal | **Driver** under a runner |
| pytest / CI | Process host |
| Verifier | Shared judge — independent of which runner drove Act |

### Four extension points (product boundary)

| Extension | Responsibility | Examples |
|---|---|---|
| **Driver** | Act on the actual system (**plugin**; runner owns the loop) | HTTP, SSE, WebSocket, Playwright, in-process, **LangGraph**, **Crew**, **Temporal**, … |
| **Observer** | Authoritative evidence | messages, routing, tool I/O, ledger, ownership, terminals, DB, events |
| **Cognition provider** | Probabilistic interpretation (**ours**: stub/freeze/record; host: local/cloud) | freeze store, record artifacts, host classifiers |
| **Verifier** | Evaluate envelopes (**ours**, not optional glue) | step asserts, trajectory/temporal invariants, allowed outcomes |

Slice 0 often collapses Driver+Observer into `ControlPlaneAdapter`. Cognition is no longer
“labels only”: stub + freeze/record providers ship; local/cloud remain host-supplied.

### Cognition provider (implementation status)

```python
class CognitionProvider(Protocol):
    def resolve(self, turn, state) -> CognitionDecision: ...
    def record(self, decision, evidence) -> FreezeArtifact: ...
    def replay(self, freeze_key) -> CognitionDecision: ...
```

| Mode | Status (0.1.2) |
|---|---|
| `stub` | ✅ `StubCognitionProvider` — pin on turn |
| `freeze` / `record` | ✅ `FreezeStore` + freeze/record providers (disk JSON) |
| `local` / `cloud` | ⬜ Host must supply provider (core does not call LLMs) |

Artifacts may carry model identity, prompt hashes, seed/temperature later. Core freeze
artifact today: pin + source + freeze_key + optional evidence.

### Delivery slices

| Slice | What | Status |
|---|---|---|
| **0** | Script model, pin-driven harness, standard invariants, optional CCP goldens | ✅ |
| **0.1.1–0.1.2** | CognitionProvider + freeze; temporal + outcome-specific verifiers; compile bridge; CLI run/JUnit; path-faithful mini-app + planted bugs; **§0 claim locked** | ✅ |
| **1 next** | HTTP/SSE/Playwright drivers; **LangGraph / Temporal / Crew adapters**; agent synthesizer **with required expected**; fail closed if golden has no expected | open |
| **2** | Richer temporal ops; observation/domain ground truth; generation + shrink; production runner (shards, retries) | open |
| **3** | ODD corpus / explorer / N-run **contract hold-rate** distributions | open |

### Module map (implementation package)

| Module | Role |
|---|---|
| `script.py` | IR: `ConjectureScript`, turns, scope, expected fields, load/dump |
| `harness.py` | `run_script` — cognition → effects → observe → verifier |
| `cognition.py` | `CognitionProvider`, `FreezeStore`, stub/freeze/record |
| `invariants.py` | Step verifier kinds (`STANDARD_INVARIANT_KINDS`) |
| `temporal.py` | Trajectory verifier kinds |
| `protocol.py` | `ControlPlaneAdapter`, `TurnObservation` |
| `path_faithful.py` | Mini-app Act path + planted-bug proof |
| `compile_scenario.py` | Scenario IR → script; `RunResult` → Trajectory |
| `discover.py` / `report.py` / `cli.py` | Discovery, JSON/JUnit, CLI |
| `contrib/control_plane.py` | Optional CCP binding + portable goldens |

---

## 2.1 Pipeline and ecosystem

Short face: [README](../README.md). **This section is normative (`CBR-SPEC`).**

Differentiation lives in **§0** (job + green bar). This section is **flow and plugins** —
not a feature bake-off against named sim/eval vendors.

### Pipeline (normative)

```text
  INPUTS: epic · ODD · incident · transcript · optional path seed
        → Author Scenario / trajectory DESCRIPTION
             (actors, steps, scope, allowed_outcomes, required_invariants, …)
        → Choose WHO RUNS IT (runner + Driver)
             e.g. compile → ConjectureScript → CP run_script
             or later: UI plan → Playwright runner
        → Observed trajectory (evidence of one run)
        → VERIFIER (envelopes vs observation)
        → Report / CI gate
```

| Stage | Owns | Rule |
|---|---|---|
| Spec / epic / story | Claimed scope | Humans own the claim |
| Description language | Flexible trajectory file | Envelopes + expected — not driver code |
| Runner selection | **Who executes** | Explicit; file does not imply runner |
| Driver | Act on host | Plugin under the chosen runner |
| Observed trajectory | Evidence | One run under one profile |
| Verifier | Pass/fail | Shared kinds; independent of runner |

### Ecosystem (seeds, description, runners)

```text
  specs / agents / humans / optional path seeds
                    │
                    ▼
         Scenario / trajectory DESCRIPTION
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
   CP play-back form     other plans (later)
   (ConjectureScript)    (e.g. UI)
         │                     │
         ▼                     ▼
   CP runner              other runners
   (run_script)           (e.g. Playwright)
         │                     │
         └──────────┬──────────┘
                    ▼
              Driver → application
                    │
           observed trajectory
                    │
                 VERIFIER
                    │
             pytest / CI (process host)
```

| Piece | Pattern |
|---|---|
| Path seeds | Feed **description** authoring; still need expected envelopes |
| Coding agents | Author description or ConjectureScript; use prompt seed |
| CP runner | Default **who runs** control-plane goldens today |
| Playwright / HTTP / LangGraph / Temporal | Drivers (and later alternate runners) |
| Trajectory scorers | Parallel scores; **not** our merge gate |

### Tempting features (scope pin — normative)

| Tempting feature | Decision |
|---|---|
| Happy/sad **quality** comparative scores | **Defer** — use `scope` / `expected_refusal` |
| Built-in **sim users / worlds** | **Never core** — optional external path seeds only |
| Proprietary “creative” **execution engine** | **Never core** — thin Driver |
| Logger-as-product | **Support only** — trajectory = verifier evidence |
| Agent script synthesizer (spec→IR + expected) | **In scope** (open) |
| Freeze / record / replay | **In scope** (shipped foundation) |
| Path-faithful HTTP/SSE/Playwright + orchestrator adapters | **In scope** (mini-app done; hosts next) |
| Generation + shrink | **Later** |
| N-run contract hold-rates | **Later** (contracts only) |
| Model leaderboards | **Out of scope** |

Not the mission: replace general runners or become a multi-turn user-sim platform.

### What would make the repo materially credible

One uncompromising vertical:

1. Start a **real** example application  
2. Send **actual** NL messages through its public interface  
3. **Record or freeze** real cognition decisions  
4. Observe **real** authoritative ledger mutations  
5. Evaluate **cross-turn** invariants  
6. Produce structured **trajectory + failure report**  
7. Plant **three** application bugs and prove Conjecture catches them  
8. Run under **pytest + CI** with deterministic replay  

Compelling demo line:

> “The wording changed, the model changed, and the route varied — but the conversation
> never created two active owners, never mutated completed work, and always returned to
> the suspended task.”

---

## 3. Implementation surface (aligned with 0.1.2 code)

Normative mapping of **product cores → modules**. If code drifts, fix code or bump SPEC.

| Product core | Primary modules | Public entry |
|---|---|---|
| IR | `script.py`, `pins.py` | `ConjectureScript`, `load_script_json` |
| Runner | `harness.py`, `cognition.py`, `cli.py` | `run_script`, `conjecture run` |
| Verifier | `invariants.py`, `temporal.py` | `check_standard_invariant`, trajectory kinds |
| Host binding | `protocol.py`, `path_faithful.py`, `contrib/*` | `ControlPlaneAdapter` |

**Arrange vs Act (path-faithful):** `LedgerEffect` / seeds **arrange**; Driver
`observe_turn` / `handle` is **Act**. Do not use effects to fake the SUT’s side effects
on the path-faithful path.

## 4. Cognition modes (status)

| Mode | Intended meaning | 0.1.2 reality |
|---|---|---|
| `stub` | Pin on the turn | ✅ Implemented |
| `freeze` / `record` | Replay / capture freeze artifacts | ✅ `FreezeStore` + providers |
| `local` / `cloud` | Host-routed real classifier | Host `CognitionProvider` required |

The portable core is **pin-driven**. It does not call an LLM factory.

---

## 4.1 Script structure (Slice 0 + multi-turn design)

Friendly intro + mini-story: [README — Script language](../README.md#script-language-what-you-write).  
This section is the **formal shape** and **why multi-turn needs more than a single assert**.

### Why multi-turn scripts (not one-shot checks)

Agentic systems fail **between** turns: ownership flips, pins drop, resolve re-runs,
detours steal mid-flight, completion lands without a human message. A single-turn
assert (“owner was X once”) does not prove the **stream** stayed legal.

A **script** is therefore an **ordered trajectory of steps** over one conversation
(or multi-agent pipeline). Each step may change host state; each step ends with
**invariants** (and optionally **allowed outcomes**) that must hold **after** that step.

```text
  initial_context
        │
        ▼
  turn 1  →  pin?  →  effects  →  observe  →  invariants ✓/✗
        │
        ▼
  turn 2  →  … (context carries forward) …
        │
        ▼
  turn N  →  … terminal / mid-flight contract …
```

What **must carry** across turns (host projection; adapter fills observation):

| Carries | Why multi-turn cares |
|---------|----------------------|
| **Conversation / session id** | Same thread; not a fresh greenfield each step |
| **Active task / kind** | Sole-continue vs new_task vs detour |
| **Exclusive owner** | Who may act next; dual-writer / steal detection |
| **Entity pins** | Same workflow/project/subject — not ambient last_read |
| **Phase / mid-flight flags** | e.g. `blocks_resolve` during sole-continue |
| **Pending / completion** | Job done, cancel, timeout as system turns later |

What **does not** need to match turn-to-turn: assistant wording, markdown layout.

### Formal types (portable core — Slice 0)

Implemented in `script.py` / `pins.py` / `protocol.py`.

#### `ConjectureScript`

| Field | Type | Role |
|-------|------|------|
| `script_id` | `str` | Stable golden id (CI / reports) |
| `description` | `str` | Human intent of the behaviour claim |
| `conversation_id` | `str` | Thread identity for the run |
| `turns` | `DialogueTurn[]` | Ordered steps (length ≥ 1 for real goldens) |
| `initial_context` | `dict` | Host projection seed (ledger-like facts) **before** turn 1 |
| `tags` | `str[]` | Optional corpus labels (`sole_continue`, `detour`, …) |
| `scope` | `ScriptScope?` | **Mini-ODD** — claimed input boundary for this script class |

#### `ScriptScope` (mini-ODD on the script)

Same plain language as experimental Scenario `Scope` / SOTIF-style ODD. Slice 0
treats scope as **metadata on the claim** (included in `RunResult.artifact`);
automated probe generation from scope is a later slice.

| Field | Role |
|-------|------|
| `in_scope` | Conditions / inputs the system **should** handle for this class |
| `out_of_scope` | Unsupported — refuse or degrade gracefully |
| `expected_refusal` | Probes that must be **rejected** (illegal restart, hijack, …) |

```python
from conjecture_behaviour_runner import ScriptScope, ConjectureScript, DialogueTurn

scope = ScriptScope(
    in_scope=["multi-turn sole-continue on a pinned entity"],
    out_of_scope=["free live model quality scoring"],
    expected_refusal=["entity re-resolve while blocks_resolve"],
)
```

#### `DialogueTurn` (one step)

| Field | Type | Role |
|-------|------|------|
| `user_text` | `str` | Primary stimulus (Slice 0 user-centric surface) |
| `actor` | `str` | `user` \| `agent` \| `system` — default `user`; multi-actor later |
| `pin` | `CognitionPin?` | Stub/freeze labels for this step (`task_intent`, kinds, …) |
| `effects` | `LedgerEffect[]` | Deterministic **arrange** mutations (not a substitute for Act) |
| `invariants` | `InvariantSpec[]` | **Expected ground truth** after this step |
| `allowed_outcomes` | `str[]` | Legal landing envelope; if set, `observed_outcome` required |
| `outcome_invariants` | `map[str → InvariantSpec[]]` | Expected rules **given** a specific outcome |
| `freeze_key` | `str` | Key for freeze/record cognition replay |

On `ConjectureScript` also: `trajectory_invariants` — cross-turn expected law (see `temporal.py`).

**CI rule (product):** a merge-gating golden must declare non-empty expected contracts
(step and/or trajectory). Exploratory scripts without expected must not gate CI
(enforcement hardening is slice 1).

#### `InvariantSpec`

| Field | Type | Role |
|-------|------|------|
| `kind` | `str` | Stable checker code (see below) |
| `expected` | any | Kind-specific target |
| `reason` | `str` | Optional human note for failures / docs |

#### `CognitionPin` (portable)

Portable cognition labels for the step. Host-specific router flags go in **`extras`** —
do not grow the public pin type with host-private fields.

Typical portable fields: task/read/discovery-style enums the host maps into ownership.
See `pins.py` and optional CCP adapter.

#### `LedgerEffect`

| Field | Type | Role |
|-------|------|------|
| `op` | `str` | Host-defined op (`ensure_task`, `set_pin`, `clear_task`, …) |
| `payload` | `dict` | Op arguments |

Effects let a script **set up** mid-flight state without a free live LLM (e.g. ensure
active task + pin already present before “continue”).

#### `TurnObservation` (adapter → harness)

| Field | Type | Role |
|-------|------|------|
| `exclusive_owner` | `str?` | Who owns this turn after apply |
| `active_kind` | `str?` | Active task/kind |
| `pins` | `dict` | Bound entity ids |
| `context` | `dict` | Updated host projection |
| `observed_outcome` | `str?` | Optional outcome code |
| `extras` | `dict` | Host facts (`blocks_resolve`, preferred ids, …) |

Invariants read **only** the observation (plus kind rules). Unknown kinds **fail closed**.

### Standard invariant kinds

| Kind | Multi-turn meaning |
|------|--------------------|
| `exclusive_owner` | After this step, owner is still (or now) X |
| `owner_not` | Owner must not remain X (e.g. detour superseded) |
| `active_kind` / `kind_equals` | Active kind matches |
| `pin_present` | Key has a **usable** bound value (not missing / null / empty / `False`) |
| `pin_absent` | Missing or null |
| `pin_key_missing` | Key not in the pins map |
| `pin_equals` | **Same** entity as earlier step — strict `==` |
| `extra_true` / `extra_false` | Key **present** and value is strictly `True` / `False` (**missing ≠ false**) |
| `extra_missing` | Key not in extras |
| `extra_equals` | Host extra equals value |
| `observed_outcome` | Adapter outcome code |
| `always_true` | Smoke only |

Full list: `STANDARD_INVARIANT_KINDS` in `invariants.py`.

**Shipped verifier surface:** standard step kinds; trajectory kinds
(`eventually_exclusive_owner`, `pin_stable`, `owner_changes_at_most`, …);
`outcome_invariants` per landing.

**Verifier gaps (roadmap):** richer temporal (`until`, `never before`), exactly-once
side effects, domain ground-truth plugins, first-class observation gold snapshots.

**Harness contracts (sealed in code):**

- If `allowed_outcomes` is non-empty, `observed_outcome` is **required** (no vacuous green).  
- `TurnObservation.context`: `None` = no update; `{}` = explicit clear; mapping = replace.  
- Pin/extra presence is **not** truthiness-collapsed (`extra_true` requires key present and `True`).

### Multi-turn script patterns (authoring guidance)

These are **scenario-class patterns**, not phrase lists. Use tags + turn sequences.

| Pattern | Shape of turns | Typical invariants |
|---------|----------------|--------------------|
| **Sole-continue** | Setup (new task + pin) → `continue` | `exclusive_owner`, `pin_present`/`pin_equals`, `extra_true` `blocks_resolve` |
| **Detour supersedes** | Mid-flow specialist → discovery/detour pin | `owner_not` specialist, `exclusive_owner` front_door (or detour owner), often `extra_false` `blocks_resolve` |
| **Pin beats ambient** | Pin set → stimulus that might re-resolve | `pin_equals` to pinned id; `blocks_resolve` or preferred id extras |
| **Illegal restart** | Mid-flight chip/text that must **not** re-start | `owner_not` reset path; kind still mid-flight (host-defined) |
| **Agent / completion** *(later)* | `actor=agent` or `system` with empty/minimal text | Same envelope: owner, pin, terminal honesty |
| **Agent → agent** *(later)* | Handoff + parent continue | Exclusive owner + pin identity; no double-write |

**Greenfield vs mid-flight:** greenfield scripts seed little `initial_context` and open a
task. Mid-flight scripts **seed or effect** active task + pins first, then probe continue /
detour / completion. Most production bugs live mid-flight — author there.

**Multi-actor (design):** experimental YAML already has `Actor`: `user` · `agent` ·
`system`. Slice 0 `DialogueTurn.actor` defaults to `user`. Same invariant language applies
when the stimulus is not a human chat line.

### Description language vs play-back form vs who runs it

| | **Scenario** (description language) | **ConjectureScript** (play-back form) | **Runner** (who executes) |
|--|-------------------------------------|----------------------------------------|---------------------------|
| Job | Flexible trajectory **description** | Thin form for CP mid-flight play-back | Applies steps via a Driver |
| Contains | actors, steps, scope, nondeterminism envelopes, waits, evidence, profiles | turns, pins, effects, expected kinds | cognition + adapter loop |
| Status | `experimental/` + `schema.json` | **Stable 0.1.x** | `run_script` + CLI today; other runners later |
| Who writes it | Humans, agents, path seeds | Author directly **or** compile from Scenario | Host/CI invokes |

**Observed trajectory** (`experimental.trajectory.Trajectory` or `RunResult`) is **output**
of a run — not the input description.

`compile_scenario_to_script` is the bridge: description → CP play-back form →
**Conjecture CP runner**. Other runners may consume Scenario without going through
`ConjectureScript` (e.g. future Playwright plan).

**Original load-bearing ideas (keep):**

- `nondeterminism.allowed_outcomes` + `required_invariants` on steps  
- Three terminal buckets: expected / tolerated_degraded / failure+graceful  
- Scope: in_scope / out_of_scope / expected_refusal  
- Trajectory-as-evidence across N runs under a profile  
- Separation of **description** from **who runs it**

### Run loop (harness contract)

For each turn, roughly:

1. Resolve cognition (stub pin / freeze / later live)  
2. Apply `effects` via adapter  
3. `observe_turn` → `TurnObservation`  
4. Evaluate each `InvariantSpec` (fail closed on unknown kind)  
5. Record turn result; abort or continue per runner policy  
6. Carry `context` into the next turn  

Result: `RunResult` (`passed`, `failures[]`, `turn_results[]`, `artifact` including
`scope` and `tags` when set).

### Mid-flight state machine (reference domain)

Reference scenario class: **multi-turn turn ownership** (sole-continue, detour,
pin continuity). Not the whole project ODD — the first sealable class.

```mermaid
stateDiagram-v2
  [*] --> FrontDoor: idle / no active stream

  FrontDoor --> MidFlight: new_task + pin entity\n(exclusive_owner = specialist)
  MidFlight --> MidFlight: continue\n(owner holds, pin holds,\nblocks_resolve = true)
  MidFlight --> FrontDoor: detour / supersede\n(owner_not specialist,\nblocks_resolve = false)
  MidFlight --> Terminal: complete / cancel / timeout\n(system actor — later)
  FrontDoor --> FrontDoor: discovery / refuse OOS
  Terminal --> [*]

  note right of MidFlight
    Illegal: re-start as greenfield
    Illegal: re-resolve from ambient last_read
    Pin identity must survive
  end note
```

ASCII (always renderable):

```text
                    ┌─────────────┐
         idle       │ front_door  │◄── detour supersedes
                    └──────┬──────┘     (blocks_resolve false)
                           │ new_task + pin
                           ▼
                    ┌─────────────┐
         continue   │ mid-flight  │──► continue (owner + pin + blocks_resolve)
         loop       │  specialist │
                    └──────┬──────┘
                           │ complete / cancel (system — later)
                           ▼
                    ┌─────────────┐
                    │  terminal   │
                    └─────────────┘

  Mid-flight must NOT: re-start assessment · drop pin · ambient last_read hijack
```

Map to script patterns:

| Transition | Script pattern | Typical invariants after step |
|------------|----------------|-------------------------------|
| Front door → mid-flight | Setup turn + `begin_task` / effects | `exclusive_owner` = specialist |
| Mid-flight → mid-flight | Sole-continue | owner + `pin_*` + `extra_true` `blocks_resolve` |
| Mid-flight → front door | Detour | `owner_not` specialist, often `extra_false` `blocks_resolve` |
| Ambient must not steal pin | Pin-beats-ambient | `pin_equals` + preferred id extras |

### Full sole-continue golden (JSON / YAML)

Canonical examples in the repo (same content):

- [`examples/sole_continue_golden.json`](../examples/sole_continue_golden.json)
- [`examples/sole_continue_golden.yaml`](../examples/sole_continue_golden.yaml)

Load without hard-coding Python:

```python
from conjecture_behaviour_runner import load_script_json, run_script, LlmMode
# YAML: load_script_yaml(...) needs pip install ...[scenarios]

script = load_script_json("examples/sole_continue_golden.json")
# result = run_script(script, adapter=your_adapter, llm_mode=LlmMode.STUB)
assert script.scope is not None
assert script.scope.in_scope
assert len(script.turns) == 2
```

Abbreviated JSON shape:

```json
{
  "script_id": "sole_continue_owns_the_turn",
  "description": "Continue mid cost-out: owner, pin, blocks_resolve",
  "conversation_id": "conv_sole_continue_demo",
  "tags": ["control-plane", "sole-continue"],
  "scope": {
    "in_scope": ["multi-turn sole-continue on a pinned entity"],
    "out_of_scope": ["free live model quality scoring"],
    "expected_refusal": [
      "entity re-resolve from ambient last_read while blocks_resolve"
    ]
  },
  "turns": [
    {
      "actor": "user",
      "user_text": "cost out the onboarding workflow",
      "pin": { "task_intent": "continue" },
      "effects": [{
        "op": "begin_task",
        "payload": {
          "kind": "cost_out",
          "pins": { "workflow_id": "wf_1" }
        }
      }],
      "invariants": [
        { "kind": "exclusive_owner", "expected": "cost_out" }
      ]
    },
    {
      "actor": "user",
      "user_text": "make the volume 10k",
      "pin": { "task_intent": "continue" },
      "invariants": [
        { "kind": "exclusive_owner", "expected": "cost_out" },
        { "kind": "pin_present", "expected": "workflow_id" },
        { "kind": "extra_true", "expected": "blocks_resolve" }
      ],
      "allowed_outcomes": ["continue_owned"]
    }
  ]
}
```

Play back with `ControlPlaneStreamAdapter` (`[control-plane]` extra) or any host
adapter that implements `begin_task` + the standard observation fields.

---

## 5. Public API (0.1.2)

```python
from conjecture_behaviour_runner import (
    LlmMode,
    CognitionPin,
    DialogueTurn,
    InvariantSpec,
    LedgerEffect,
    ConjectureScript,
    ScriptScope,
    ControlPlaneAdapter,   # Protocol
    NullControlPlaneAdapter,
    BaseControlPlaneAdapter,
    check_standard_invariant,
    run_script,
    script_from_dict,
    load_script_json,
    load_script_yaml,      # needs [scenarios] / PyYAML
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

- Replacing Playwright, pytest, or Cucumber as general-purpose runners  
- Rebuilding sim/world platforms as the core mission  
- Claiming CARLA-class generation/runtime **today**  
- Live LLM on every PR by default  
- Phrase laundry lists as cognition  
- Claiming Conjecture *is* the Conversation Control Plane (it **proves** contracts; CCP is one surface)  
- Claiming Slice 0 goldens are path-faithful production proofs  

---

## 7. License & status

MIT. Alpha.

| Horizon | Intent |
|---|---|
| **Wedge** | Control-plane conformance under pinned/replayed cognition |
| **Slice 0** | Script + invariants + optional CCP contract unit goldens |
| **Next** | Path-faithful vertical + planted-bug proof + CI freeze/replay |
| **Then** | Driver/Observer/CognitionProvider, Scenario→Trajectory join, temporal verifiers, shrink |

Host adapters and host-private goldens stay in host repos; this package keeps a portable, leak-free surface.

**Document type / ID:** Specification · `CBR-SPEC` · canonical path `docs/SPEC.md`.

---

## 8. Contributions, Verdict, and foundational ideas

Short face: [README — Contribute · Verdict](../README.md#contribute--verdict--foundations).  
**This section is the full map.**

### Where open-source contributions can go

MIT: **use, fork, ship** IR + verifier + thin runner. PRs stay **portable**.

| Area | Examples | Why |
|---|---|---|
| **Drivers** | HTTP/SSE, WebSocket, Playwright, LangGraph/Temporal | Path-faithful Act |
| **Observers** | Ledger / tools / events → `TurnObservation` | Authoritative evidence |
| **Cognition providers** | Local/cloud wrappers; freeze tooling | CI freeze/replay |
| **Verifier kinds** | Temporal packs, domain-neutral invariants | Deeper contracts |
| **Agent interface** | Spec → validated `ConjectureScript` + repair | Agentic golden authoring |
| **Ecosystem bridges** | Orchestrator adapters; optional path-seed import; trace → observation | Integrate, don’t clone |
| **Corpus** | Portable sole-continue / detour / pin-stable goldens | Shared language |
| **CLI / CI** | Sharding, timeouts, richer JUnit, rerun | Production runner |
| **Docs & examples** | Adapter tutorials, ODD recipes | First green run |
| **Schema / IR** | Versioned format, stronger validators | Stable agent surface |

**Norms:** one concept per PR; tests for new kinds/providers; fail closed; no host-private
goldens in this repo; do not reimplement Playwright, sim worlds, or eval platforms in core.

### Conjecture (OSS) vs Verdict (commercial)

| | **Conjecture (MIT)** | **Verdict (commercial — free to diverge)** |
|---|---|---|
| Mission | Portable contracts + community extensions | Hosted / enterprise experience |
| Ships | Schema, runner, verifier, freeze, CLI, examples | Whatever customers need (may use or reimplement) |
| Speed | Deliberate core | **Faster or different** (hosted runners, multi-tenant) |
| Hosting | You run it | **Fully hosted**, VPC, or hybrid |
| UI | Optional community tools | Studio, dashboards, SSO, audit |
| Corpus | Portable goldens only | Private corpora, fleets, sim-seed ops |
| Support | Best-effort issues | Commercial SLA |
| License | MIT stays MIT | Proprietary **around/beside** core — not silent relicense of PRs |

```text
  Community PRs ──► Conjecture MIT (IR · verifier · drivers · freeze)
                         ├── embed in any CI / product
                         └── Verdict (optional): hosted · UI · SSO · managed freeze · SLA
```

OSS and commercial **do not block each other**.

### Foundational ideas (community or Verdict)

| Idea | Sketch |
|---|---|
| Schema as agent API | Versioned JSON is what agents target |
| Arrange ≠ Act | Effects/seeds arrange; Driver Act is SUT |
| Freeze as CI law | Merge gates prefer freeze-replay |
| Mini-ODD on goldens | `scope` travels with the script |
| Trajectory as evidence | Not a second product |
| Outcome-specific contracts | Landing A ⇒ invariant set A |
| Temporal verifier pack | eventually / never / until / at-most-once |
| Path-seed bridge, not sim core | External exploration may seed; Conjecture gates law |
| Driver plugins | Same IR over in-process / HTTP / Playwright |
| Failure shrinking (later) | Minimal multi-turn counterexample |
| Contract hold-rates (later) | N-run *invariant hold*, not preference |
| Verdict-shaped ops | Multi-tenant history, RBAC, webhooks, fleets |
