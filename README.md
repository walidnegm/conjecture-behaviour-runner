# Conjecture Behaviour Runner

**Catch the agent bugs that still look fine in chat.**

Multi-turn agents fail *quietly*: the reply still sounds fine, but the system dropped
who owns the turn, lost the locked record, or restarted finished work. Conjecture makes
CI go red on **state law**, not wording — with cognition **pinned/frozen** so runs stay
cheap and identical every PR.

MIT · **0.1.4** · [Bot0.ai](https://bot0.ai)

---

## Install & first run

```bash
git clone https://github.com/walidnegm/conjecture-behaviour-runner.git
cd conjecture-behaviour-runner
pip install -e ".[dev]"

conjecture path-faithful --prove-bugs   # healthy PASS + 3 planted FAILs
conjecture ui                           # browser UI → http://127.0.0.1:8765
pytest tests/ -q
```

### Minimal golden (15 lines)

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

### Planted bugs (the signature claim)

| Run | Result | What broke |
|-----|--------|------------|
| Healthy continue | **PASS** | Mid-flight owner + pin hold |
| Dual owner | **FAIL** | Steal to front door |
| Drop pin | **FAIL** | Lost `workflow_id` |
| Illegal restart | **FAIL** | Task wiped mid-flight |

### Five concepts (that’s the public model)

| | |
|--|--|
| **Script** | Multi-turn golden with expected rules |
| **Turn** | Stimulus + optional pin + invariants |
| **Driver** | How you Act on the app (`handle`, HTTP, …) |
| **Observation** | Projected state after the turn |
| **Invariant** | Rule that must hold (owner, pin, …) |

Deeper architecture (Scenario, ODD, multi-runner, Verdict): [`docs/SPEC.md`](docs/SPEC.md) — **optional** for first contributions.

---

## HTTP Driver (portable hosts)

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

Your app returns JSON with owner/pins; Conjecture checks invariants. No Python protocol
required to try. More: [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Why not just LangSmith / DeepEval?

Those own traces and LLM-as-judge. Conjecture owns **“reply fine, ledger wrong”** under
freeze-safe CI. Use **alongside** quality tools — not instead.

---

## Contribute

See **[CONTRIBUTING.md](CONTRIBUTING.md)** (matrix, sized issues, five-minute path).

| Integration | Driver | Example |
|-------------|--------|---------|
| Path-faithful mini-app | ✅ | ✅ planted bugs |
| HTTP/JSON | ✅ adapter | ⬜ host sample |
| LangGraph / Temporal / Playwright | ⬜ | ⬜ |

---

## License

MIT · Copyright © Bot0.ai / contributors.
