# Conjecture Behaviour Runner

**Catch state-law breaks that still look fine in chat** — given a fixed classification
(pin/freeze). Pair with classifier tests for cognition drift.

MIT · **0.1.5** · [Bot0.ai](https://bot0.ai)

---

## The pain (real, not only synthetic)

In multi-turn control planes, the reply can look fine while **exclusive owner**, **entity
pin**, or **mid-flight law** breaks. Dogfood on the Conversation Control Plane repeatedly
hit this class (e.g. discovery/scorecards-shaped turns mid cost-out looking like a helpful
detour while sole-continue still owned the stream). Evals score prose; they miss the ledger.

Conjecture freezes the classification for CI, runs the real Act path (or HTTP), and fails
the build when **state law** breaks.

> **Honest scope:** this gates **execution** given a pin/freeze — not “the classifier was
> wrong.” Test cognition separately; use Conjecture for owner/pin/terminal regression.

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

```python
from conjecture_behaviour_runner import (
    ConjectureScript, DialogueTurn, InvariantSpec, CognitionPin,
    run_script, LlmMode,
)
from conjecture_behaviour_runner.path_faithful import MiniAppAdapter, MiniChatApp

script = ConjectureScript(
    script_id="demo",
    description="continue keeps owner and pin",
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

Help wanted: real host samples (HTTP), LangGraph/Temporal adapters, incident goldens.

---

## License

MIT · Copyright © Bot0.ai / contributors.
