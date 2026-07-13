# Conjecture Behaviour Runner

**Catch state-law breaks that still look fine in chat.**

In multi-turn agents, the reply can sound correct while the **conversation machine**
underneath is wrong: the wrong specialist owns the turn, the locked record silently
changed, or a mid-flight task was illegally restarted. Those failures are **ledger and
handoff bugs**, not “bad writing.” Ordinary unit tests and LLM-as-judge evals usually
miss them.

The design principle is **LLM proposes · code enforces**. The model may emit
labels—continue, detour, new task, abandon—but **deterministic code** (your rule-set)
must decide exclusive owner, pin identity, and when ownership may yield. If that
enforcement is soft, the model can **steal or hijack** the path and still produce a
helpful-looking answer. Conjecture is regression for the **enforce** half: after each
scripted turn it checks that owner · pin · handoff law still hold.

**Owners and kinds are yours, not Conjecture’s.** The package does not ship a fixed
catalog of agents or task types. Whatever **type** your ledger defines—
`cost_out`, `invoice_intake`, `claim_review`, `onboarding`, a Temporal activity name,
a LangGraph node id—is what you assert as `exclusive_owner` / `active_kind`. The
same for pins: `workflow_id`, `claim_id`, `invoice_id`, … — host vocabulary projected
into Observation. Demos below use **`cost_out` + `workflow_id` only as a concrete
stand-in** from the path-faithful mini-app (Conversation Control Plane dogfood). Swap
the strings for your ledger; the invariants stay the same shape.

**Parameterized templates** (shareable shapes, not product goldens):  
`sole_continue_script(...)` · `reorient_keeps_owner_script(...)` · docs in
[`templates/README.md`](templates/README.md). Example:
`python examples/parameterized_templates.py`.  
CCP host law (reorient ≠ COMPLETE, every result names a transition):
[Host transition discipline](https://github.com/walidnegm/conversation-control-plane/blob/main/docs/host-transition-discipline.md).

CI needs a **fixed classification** (pin or freeze), not a live model roll every
run—so the same golden fails for the same state break on every PR. That is deliberate:
this package does **not** prove the classifier was right. Pair it with separate
classifier tests for cognition drift; use Conjecture for “given these labels, did code
still seal the ledger?”

The ledger can live anywhere (session DB, LangGraph, Temporal, Vercel AI session, …).
If you can project **your** owner/kind/pins after Act, you can import a Driver and get
a **verdict**.

MIT · **0.1.5** · [Bot0.ai](https://bot0.ai)

---

## What this is (plain English)

**Not** “did steps run in the right order?” (ordinal / unit tests).  
**Not** “did the bot write a good sentence?” (LLM eval).

**Yes:** after each user message, do the **deterministic ledger + handoff rules** still hold —
the coded rule-set that says who owns the turn, what is pinned, and when ownership may
yield — even when an LLM *proposes* something that would steal or hijack if code did not
enforce?

That is the principle:

> **LLM proposes · code enforces.**  
> Conjecture regression-tests the **enforce** half under **pinned** labels so CI is
> repeatable. If application logic is soft (fall-through to chat, keyword routing,
> missing sole-continue), a model can fool the path; Conjecture is built to fail those
> steals.

| Check | Meaning (host-defined values) |
|-------|---------|
| **Who owns this turn?** | Your ledger’s exclusive owner / kind string vs front door / idle |
| **What is locked?** | Your pin map (whatever ids the host freezes for this task) |
| **Mid-flight / handoff law** | No illegal restart, no silent pin drop; handoff only when *your* rules allow |

**Demo shape only** (mini-app vocabulary — not the only kind Conjecture knows):

```text
# Host example vocabulary: kind=cost_out, pin key=workflow_id
# (could just as well be claim_review + claim_id, invoice_intake + invoice_id, …)

User: "start <your mid-flight task> on record R"
User: "change a field mid-flight"     ← reply can still sound fine

Unit / ordinal tests:  ✅ something returned
LLM eval:              ✅ text looks helpful
Conjecture:            ✅ exclusive_owner still equals the kind your ledger started
                       ✅ pin still equals the same record id
                       ❌ FAIL if continue stole to front_door or dropped the pin
```

In the shipped mini-app that kind string is `cost_out` and the pin is `workflow_id=wf_1`
— convenient dogfood, **not** a product enum.

**One line:** regression for multi-turn **state law** (owner · pin · handoff) under
**pinned cognition** — *looks fine in chat, broken underneath* — against the principle
that **code, not the model, owns enforcement**.

### Who “deserves to go next”?

In a control-plane style app, that is **not** “parse the last chat line for keywords.”
It is roughly:

1. **Ledger state** — what **kind** is mid-flight?  
   (`active_task.kind` / `exclusive_owner` — **any string your rule-set defines**)  
2. **Entity pin** — which record is locked?  
   (**any** pin keys your host freezes: workflow, claim, ticket, …)  
3. **This turn’s classification** (pinned for CI) — `continue` vs `detour` vs `new_task` / `abandon`

If the ledger says kind **K** is active and the turn is **continue**, **K** owns
delivery even if the user text *looks* like a detour (glossary, FAQ, another product
surface). If the turn is **detour** / **abandon**, ownership **yields** per your rules.

Conjecture asserts those rules still held **after** Act for the **expected strings you
wrote in the golden**. Ordinary ordinal tests do not model exclusive owner or pins.

### Where the ledger lives (does not matter)

Conjecture does **not** require a specific product stack for the ledger. The durable
state may live in:

- a custom DB / JSON session blob  
- **LangGraph** / LangChain checkpoint state  
- **Temporal** workflow state  
- **Vercel AI SDK** / other session stores  
- any control plane that projects **owner · pins · outcome** after a turn  

**What matters:** you have a **rule-set** (coded handoff / sole-continue / pin law) and a
**Driver** that runs Act and returns an **Observation** Conjecture can check. Import
your adapter (or HTTP JSON paths), pin the labels, run the script → **verdict**
(PASS/FAIL + which invariant broke). No need to rewrite the ledger into Conjecture’s
types beyond that projection.

---

## The pain (real, not only synthetic)

In multi-turn control planes, the reply can look fine while **exclusive owner**, **entity
pin**, or **handoff law** breaks — classic **steal/hijack** when the model’s proposal was
not sealed by code. Dogfood on the Conversation Control Plane hit this class with one
particular mid-flight kind (`cost_out`): discovery-shaped turns mid-flight looked
helpful while sole-continue still owned the stream. The failure class is the same for
**any** sole-continue kind your ledger defines. Evals score prose; they miss the
rule-set.

Conjecture freezes the classification for CI, runs the real Act path (or HTTP), and fails
the build when **state law** breaks.

> **Honest scope:** this gates **enforcement** given a pin/freeze — not “the classifier
> was wrong.” Test cognition separately; use Conjecture for owner/pin/handoff regression.

---

## 30-second proof (two paths)

### A. In-process mini-app (fastest)

```bash
git clone https://github.com/walidnegm/conjecture-behaviour-runner.git
cd conjecture-behaviour-runner
pip install -e ".[dev]"

conjecture path-faithful --prove-bugs   # PASS + 3 planted FAILs
# optional local demo UI (not a product — just a viewer):
conjecture ui --port 8765
```

### B. External HTTP app (true portability)

The strongest claim: the **system under test does not import Conjecture**.

```text
proofs/external_http_app/   ← independent SUT (no conjecture imports)
        ↓ HTTP only
HttpJsonAdapter + portable golden + verifier
```

```bash
PYTHONPATH=src python proofs/run_external_http_proof.py --prove-bugs
```

That spawns four independent HTTP processes (healthy + `owner_steal` / `drop_pin` /
`illegal_restart`) and proves the same contracts under **pinned cognition** (`LlmMode.STUB`).

---

## Minimal golden

The mini-app’s mid-flight kind is hard-coded to `cost_out` for the proof path.
On **your** host, replace `cost_out` / `workflow_id` with whatever owner and pin
keys your ledger emits in Observation.

```python
from conjecture_behaviour_runner import (
    ConjectureScript, DialogueTurn, InvariantSpec, CognitionPin,
    run_script, LlmMode,
)
from conjecture_behaviour_runner.path_faithful import MiniAppAdapter, MiniChatApp

# Demo vocabulary only — your golden uses YOUR ledger strings:
#   exclusive_owner / active_kind  e.g. "cost_out" | "invoice_intake" | "claim_review"
#   pin keys                       e.g. "workflow_id" | "invoice_id" | "claim_id"
script = ConjectureScript(
    script_id="demo",
    description="continue keeps host owner and pin",
    conversation_id="conv_1",
    turns=[
        DialogueTurn(
            user_text="cost out the onboarding workflow",
            pin=CognitionPin(task_intent="new_task", read_kind="cost_out"),
            invariants=[
                InvariantSpec(kind="exclusive_owner", expected="cost_out"),
                InvariantSpec(kind="pin_present", expected="workflow_id"),
            ],
        ),
        DialogueTurn(
            user_text="make the volume 10k",
            pin=CognitionPin(task_intent="continue"),
            invariants=[
                InvariantSpec(kind="exclusive_owner", expected="cost_out"),
                InvariantSpec(
                    kind="pin_equals",
                    expected={"key": "workflow_id", "value": "wf_1"},
                ),
            ],
        ),
    ],
)
result = run_script(
    script, adapter=MiniAppAdapter(MiniChatApp()), llm_mode=LlmMode.STUB
)
assert result.passed
```

### Wire your own HTTP app

```python
from conjecture_behaviour_runner.contrib.http_json import HttpJsonAdapter

adapter = HttpJsonAdapter(
    endpoint="http://localhost:8000/chat",
    owner_path="debug.owner",
    pins_path="debug.pins",
    outcome_path="debug.outcome",
)
# result = run_script(script, adapter=adapter, llm_mode=LlmMode.STUB)
```

---

## Five concepts (public model)

**Script · Turn · Driver · Observation · Invariant**

Everything else (Scenario, ODD, multi-runner, Verdict) is advanced — [`docs/SPEC.md`](docs/SPEC.md).

Local browser UI (`conjecture ui`) is a **demo viewer**, not a second product.

---

## Planted-bug table (machinery)

| Run | Result | Break |
|-----|--------|--------|
| Healthy | **PASS** | — |
| Owner steal | **FAIL** | Continue reports `front_door` while task active |
| Drop pin | **FAIL** | Lost `workflow_id` |
| Illegal restart | **FAIL** | Task wiped mid-flight |

---

## Contribute

[CONTRIBUTING.md](CONTRIBUTING.md) — matrix, sized issues, five-minute path.

Help wanted: real host samples (HTTP), LangGraph/Temporal adapters, **incident patterns**.

### Learning loop (bugs → patterns)

When an agent submits the wrong type into the ledger or skips the ledger contract,
and the **SDK is already complete**, that is often a **Conjecture-class** bug.
Classify → Scenario → Script → catalog:

- **Patterns inventory (list + describe):** [`incidents/CATALOG.md`](incidents/CATALOG.md)  
- Playbook: [`incidents/README.md`](incidents/README.md)  
- Template: [`incidents/_template/`](incidents/_template/)  
- Patterns: [`incidents/patterns/`](incidents/patterns/)

### Where to go (docs map)

| Need | Path |
|------|------|
| Hero demo / planted bugs | this README (above) |
| **Failure-class inventory** | [`incidents/CATALOG.md`](incidents/CATALOG.md) |
| How to land a pattern | [`incidents/README.md`](incidents/README.md) |
| Package unit tests | [`tests/`](tests/) — **not** the inventory |
| Demos / E2E scripts | [`examples/`](examples/) |
| Script shapes (any host kind) | [`templates/README.md`](templates/README.md) |
| Normative spec | [`docs/SPEC.md`](docs/SPEC.md) |
| Agent coder files-first | [`AGENTS.md`](AGENTS.md) §7 |

---

## License

MIT · Copyright © Bot0.ai / contributors.
