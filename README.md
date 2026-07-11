# Conjecture Behaviour Runner

**Catch the agent bugs that still look fine in chat.**

Multi-turn agents fail *quietly*: the reply still sounds fine, but the system dropped
who owns the turn, lost the locked record, or restarted finished work. Conjecture is a
small **Script → Driver → Observation → Invariant** kit so CI goes red on **state law**,
not on wording — with cognition **pinned/frozen** so runs stay cheap and identical.

MIT · Alpha **0.1.4** · [Bot0.ai](https://bot0.ai)

---

## 30-second start

```bash
git clone https://github.com/walidnegm/conjecture-behaviour-runner.git
cd conjecture-behaviour-runner
pip install -e ".[dev]"

# Browser UI — story, healthy run, planted bugs
conjecture ui
# → http://127.0.0.1:8765

# Or CLI only
conjecture path-faithful --prove-bugs
```

### Minimal code (this is the whole public model)

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
    script,
    adapter=MiniAppAdapter(MiniChatApp()),  # your Driver
    llm_mode=LlmMode.STUB,
)
assert result.passed
```

Five concepts: **Script · Turn · Driver · Observation · Invariant**.  
Deeper model (Scenario, ODD, multi-runner, Verdict) lives in
[`docs/SPEC.md`](docs/SPEC.md) — **not required to contribute**.

---

## Watch the bar turn red

In-repo mini-app with a real `handle()` and three planted bugs:

| Run | Result | What broke |
|-----|--------|------------|
| Healthy continue | **PASS** | Mid-flight owner + pin hold |
| Dual owner | **FAIL** | Steal to front door — reply can still look fine |
| Drop pin | **FAIL** | Lost `workflow_id` |
| Illegal restart | **FAIL** | Task wiped mid-flight |

```bash
conjecture path-faithful --prove-bugs
# or: conjecture ui  →  “Prove planted bugs”
```

---

## Why this is not another eval platform

LangSmith / DeepEval / Phoenix / etc. own **traces and LLM-as-judge**.  
Nobody owns: *“the reply sounded fine but we lost the locked workflow / dual-wrote /
restarted completed work.”*

Use Conjecture **alongside** quality tools as the **cheap state-law CI gate** — not as a
replacement for trajectory scoring. Best fit: high-stakes multi-turn systems with
ownership + pins (see [Conversation Control Plane](https://github.com/walidnegm/conversation-control-plane)
as inspiration). Skip pure creative chat with no authoritative mid-flight state.

---

## Local UI (OSS)

```bash
conjecture ui --port 8765
```

Stdlib HTTP server (no Flask). Shows the planned story, healthy timeline
(must-hold vs measured), and planted-bug proof cards.

*(Bot0 monorepo also has a superadmin console at `/account/admin/conjecture` for
in-product dogfood — same idea, host-specific.)*

---

## Contribute

See **[CONTRIBUTING.md](CONTRIBUTING.md)** — contribution matrix, contributor-sized
issues, and what *not* to ask first-time contributors to build.

**Highest-leverage next community package:** generic **HTTP/JSON Driver + Observer**
(configure endpoint + JSON paths for owner/pins) so hosts need not implement Python
protocols first.

| Help wanted | Status |
|-------------|--------|
| HTTP driver / observer | Planned |
| LangGraph · Temporal · OpenAI Agents · Playwright | Needed |
| Example packs with planted bugs | Needed |

---

## Docs map

| Start here | Deeper |
|------------|--------|
| This README | [docs/SPEC.md](docs/SPEC.md) architecture |
| [CONTRIBUTING.md](CONTRIBUTING.md) | [AGENTS.md](AGENTS.md) host adapter notes |
| `conjecture ui` | [examples/](examples/) |

---

## License

MIT · Copyright © Bot0.ai / contributors.
