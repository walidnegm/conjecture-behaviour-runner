# Conjecture Behaviour Runner

**Freeze-safe regression gates for control-plane state law.**

We do **not** care if your agent uses a different adjective today.  
We care that it did **not** violate core legal state, drop session pins, or rewrite
ledger identity mid-flight — even when the reply still looks fine.

Built by [Bot0.ai](https://bot0.ai). MIT · Alpha **0.1.3**

| | |
|---|---|
| **GitHub** | [github.com/walidnegm/conjecture-behaviour-runner](https://github.com/walidnegm/conjecture-behaviour-runner) |
| **Import** | `conjecture_behaviour_runner` |
| **Spec** | [`docs/SPEC.md`](docs/SPEC.md) (**CBR-SPEC**) |
| **Agent guide** | [`AGENTS.md`](AGENTS.md) |
| **Inspiration / pattern** | [Conversation Control Plane](https://github.com/walidnegm/conversation-control-plane) |

---

## Watch the bar turn red (start here)

In multi-turn agents, **silent failure** is the failure mode: the text still looks fine
to a human or an LLM evaluator while **owner / pin / terminal law** is broken.

This repo ships a tiny real Act surface (`MiniChatApp.handle()`) and three planted bugs.
Replies can still look fine. **Conjecture goes red.**

```bash
git clone https://github.com/walidnegm/conjecture-behaviour-runner.git
cd conjecture-behaviour-runner
pip install -e ".[dev]"
python examples/e2e_multi_turn.py
# or: conjecture path-faithful --prove-bugs
```

| Run | Result | What broke (state law) |
|-----|--------|-------------------------|
| Healthy continue | **PASS** | Mid-flight contracts hold under freeze |
| Continue steals to front door | **FAIL** | Dual owner — reply can still look fine |
| Continue drops `workflow_id` | **FAIL** | Lost entity pin |
| Continue wipes the task | **FAIL** | Illegal restart mid-flight |

That demo is the value prop. Ontology and vision live in the [spec](docs/SPEC.md).

---

## What this is (claim hierarchy)

### 1. Face — sell this

> **Freeze-safe regression gates for control-plane state law**  
> (turn ownership · entity pins · mid-flight / terminal boundaries).  
> Goldens go red when state breaks — even when the reply looks fine.  
> Cognition is **pinned or frozen** so CI is cheap and repeatable (no live LLM on every PR).

### 2. Technical definition — sticky mechanism (under the face)

> **Contract testing for the conversational control plane** —  
> **behavioral envelopes** (allowed outcomes + invariants) over **authoritative state**,  
> under **pinned or replayed cognition**.  
>  
> Not “one golden sentence.” Not a new universal testing paradigm.

This is how green is defined. It does **not** replace the face claim or imply a full
multi-surface behaviour platform.

### 3. Architecture gloss — scoped, not the pitch

> Authoritative control-plane conformance under probabilistic cognition —  
> **when** the host is [CCP](https://github.com/walidnegm/conversation-control-plane)-shaped
> (or isomorphic) and Act is under a real Driver.  
> Not “every LangGraph app / free live discovery today.”

Normative hierarchy: [CBR-SPEC §0](docs/SPEC.md#0-finalized-product-claim-normative).

| Today (backed by code) | Not today (vision / roadmap) |
|------------------------|------------------------------|
| Path-faithful mini-app + planted bugs | Emergent bug *discovery* under free live classify→route→tools |
| Goldens: Script + verifier kinds + freeze | Full multi-runner “behaviour platform” |
| Portable kinds for **CCP-shaped** hosts | First-party LangGraph/Crew packages as turnkey products |
| Optional CCP stream unit goldens | Generation / shrink / N-run hold-rate dashboards |

**First adopter:** dogfood for [Conversation Control Plane](https://github.com/walidnegm/conversation-control-plane)
and hosts that **follow the same format** (single-writer ownership, pins, sole-continue /
terminal discipline). That pattern is the **inspiration and primary application** —
not “every chatbot.”

---

## Why it exists

### Silent failure (the problem)

LLM evaluators and screenshot tests score **prose**. Multi-turn systems fail in **state**:

- A detour or ambient question **hijacks** a locked workflow mid-approval  
- A sub-agent **drops** an entity lock while the reply stays polite  
- A terminal task is **illicitly re-activated** by a later message  
- Two writers claim the turn (**dual owner**) after a handoff  

The reply can still look fine. Conjecture locks onto **deterministic state enforcement**.

### CI-friendly determinism

| Layer | Who owns it |
|-------|-------------|
| Probabilistic cognition (intent / route labels) | **Pinned or frozen** for the golden |
| State transitions + pass/fail | **Code** — adapter observation + verifier |

Teams get **fast, cheap, repeatable** regression in GitHub Actions without paying for
thousands of live LLM calls on every PR.

---

## Where it is most useful

```text
                    [ High stakes / transactional ]
                    FinTech · supply chain · healthcare · ops ledgers
                                  ▲
                                  │   ◄── Conjecture sweet spot
                                  │       (state enforcement)
                                  │
[ Low stakes / creative ] ────────┼──────────► [ Exploratory / open chat ]
 Marketing copy · drafts          │            General Q&A bots
                                  ▼
```

**Sweet spot:** engineering teams building **transactional, high-stakes** multi-turn agents
that already (or will) model **turn ownership, entity pins, and terminal states**.

**High-utility scenarios:**

| Scenario | What you pin |
|----------|----------------|
| **Context & entity locking** | Mid sensitive workflow (e.g. $10k invoice approval), ambient chat must **not** change `invoice_id` / workflow pin |
| **State-machine compliance** | Terminal task must not be illicitly re-activated; no mutate-after-complete |
| **Handoff integrity** | Agent A → Agent B: exclusive owner shifts safely — **no dual writer** |

**Apt for Conjecture:** apps that follow a **control-plane format** like the
[Conversation Control Plane](https://github.com/walidnegm/conversation-control-plane)
(or an isomorphic ledger: single writer, pins, mid-flight vs front door, terminals).  
**Not apt:** pure creative chat with no authoritative mid-flight state to protect.

LangGraph / Crew / Temporal hosts fit **when** they project that shape into
`TurnObservation` — the orchestrator is a **Driver surface**, not a free pass to use
the vocabulary without modeling ownership and pins.

---

## Critical trap — do not become a chat validator

| Do | Do not |
|----|--------|
| Assert owner, pin, terminal, legal landing | Assert prose style, tone, “good answer” |
| Freeze cognition for CI | Require live LLM on every PR |
| Fail closed on unknown kinds | Soft-pass “looks mostly fine” |

If you use Conjecture to grade adjectives, the framework will feel **restrictive, clunky,
and brittle**. That is out of scope by design.

**Winning pitch:** *AI agents are software systems that must obey laws — not creative
writing projects that only need a quality score.*

---

## How FAIL is decided

After each turn: **Act** → `TurnObservation` (authoritative projection) → **Verifier**
checks the golden’s expected contracts.

`passed = (failures == [])`. Unknown kinds fail closed.  
Not a model score. See [CBR-SPEC §4.1](docs/SPEC.md#41-script-structure-slice-0--multi-turn-design).

---

## Examples (same sole-continue path)

| Shape | File |
|-------|------|
| **E2E (hero)** | [`examples/e2e_multi_turn.py`](examples/e2e_multi_turn.py) |
| **Script golden** | [`examples/trajectory_authored_sole_continue.json`](examples/trajectory_authored_sole_continue.json) |
| **Observed PASS / FAIL** | [`trajectory_observed_pass.json`](examples/trajectory_observed_pass.json) · [`…_fail_dual_owner.json`](examples/trajectory_observed_fail_dual_owner.json) |
| **Scenario** (experimental description) | [`scenario_sole_continue.yaml`](examples/scenario_sole_continue.yaml) · [`scenario_compile_and_run.py`](examples/scenario_compile_and_run.py) |
| **CCP unit goldens** | [`control_plane_goldens.py`](examples/control_plane_goldens.py) (`pip install -e ".[control-plane]"`) |

Face vocabulary for day-to-day work: **golden (Script) · run · verifier**.  
Richer names (Scenario, multi-runner, seeds) are in the [spec](docs/SPEC.md) — not required to get value.

---

## What ships (0.1.3)

| **Do this today** | Status |
|-------------------|--------|
| Path-faithful mini-app + planted bugs | ✅ |
| Script + freeze/stub + standard + temporal verifiers | ✅ |
| CLI (`conjecture run`, `path-faithful`, JSON/JUnit) | ✅ |
| Optional CCP stream goldens | ✅ |

| **Useful scaffolding** | Status |
|------------------------|--------|
| Scenario models + compile bridge | ✅ experimental |
| Agent prompt seed / AGENTS.md | ✅ |

| **Vision (not the value prop yet)** | Status |
|-------------------------------------|--------|
| First-party LangGraph/Crew/Temporal packages | ⬜ |
| Generation / shrink / N-run distributions | ⬜ |
| Non-toy Driver on a production host (e.g. full chat path) | ⬜ next dogfood |

---

## Quickstart

```bash
pip install -e ".[dev]"
pytest tests/ -q
python examples/e2e_multi_turn.py
```

Host integration: implement `ControlPlaneAdapter` / `BaseControlPlaneAdapter` (project
your ledger → `TurnObservation`), or start from `path_faithful.MiniAppAdapter` /
`contrib.control_plane.ControlPlaneStreamAdapter`. Details: [`AGENTS.md`](AGENTS.md).

---

## Contribute · Verdict

**MIT:** portable drivers, providers, kinds, docs — no host-private goldens.  
**Verdict** (commercial, optional): hosted/studio/SSO — may diverge; does not block OSS.  
Maps: [CBR-SPEC §8](docs/SPEC.md#8-contributions-verdict-and-foundational-ideas).

Copyright © Bot0.ai / contributors. MIT.
