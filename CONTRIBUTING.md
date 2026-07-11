# Contributing to Conjecture Behaviour Runner

Thanks for considering a contribution. **You do not need the full architecture
philosophy to land useful work.**

## Start here (5 minutes)

```bash
pip install -e ".[dev]"
conjecture path-faithful --prove-bugs   # CLI red bar
conjecture ui                           # browser story + planted bugs
pytest tests/ -q
```

### Five stable concepts only

| Concept | Meaning |
|---------|---------|
| **Script** | Multi-turn golden with expected rules |
| **Turn** | One step: stimulus + optional pin + invariants |
| **Driver** | How you Act on the real app (`handle`, HTTP, …) |
| **Observation** | Projected state after the turn (`TurnObservation`) |
| **Invariant** | Rule that must hold (owner, pin, …) |

Everything else (**Scenario**, **ODD**, multi-runner, distributions, shrinking,
**Verdict**, rich ontology) is **advanced / experimental** — see
[`docs/SPEC.md`](docs/SPEC.md). Do not block PRs on those.

### Tiny API shape

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
                InvariantSpec(kind="pin_equals", expected={"key": "workflow_id", "value": "wf_1"}),
            ],
        ),
    ],
)
result = run_script(script, adapter=MiniAppAdapter(MiniChatApp()), llm_mode=LlmMode.STUB)
assert result.passed
```

## What attracts early contributors

Prefer PRs that someone needs personally:

- A **Driver** / **Observer** (HTTP JSON is the highest leverage next)
- A new **invariant kind** with a test
- An **example** with planted bug → FAIL → one-line fix → PASS
- Report/CLI polish

### Contribution matrix (help wanted)

| Integration | Driver | Observer | Example | Maintainer |
|-------------|--------|----------|---------|------------|
| Path-faithful mini-app | ✅ | ✅ | ✅ planted bugs | Bot0 |
| Conversation Control Plane | ✅ optional extra | ✅ | ✅ goldens | Bot0 |
| **HTTP / JSON** | ✅ `HttpJsonAdapter` | ✅ JSON paths | ✅ `examples/http_*` + e2e | Bot0 + samples welcome |
| LangGraph | ⬜ Needed | ⬜ Needed | ⬜ Needed | Needed |
| Temporal | ⬜ Needed | ⬜ Needed | ⬜ Needed | Needed |
| OpenAI Agents SDK | ⬜ Needed | ⬜ Needed | ⬜ Needed | Needed |
| Playwright | ⬜ Needed | N/A | ⬜ Needed | Needed |

### Contributor-sized issues (good first PR shapes)

**Do file:**

- Map Temporal workflow status into `TurnObservation`
- Add `no_mutation_after_terminal` invariant kind + test
- Add sample activity-retry script with planted bug
- Export event history as observed turns (JSON)
- HTTP driver: POST turn text, read owner/pins from JSONPath

**Avoid for first PRs (too much context):**

- General scenario generation / ODD tooling
- Statistical hold-rate infrastructure
- Generalized multi-runner platform
- Studio / commercial surface
- Large ontology refactors

## Package layout (conceptual packages)

One repo today; boundaries should stay clear:

```text
conjecture-core          # script, harness, invariants, freeze  (this package)
conjecture-driver-http   # planned
conjecture-driver-playwright
conjecture-langgraph / temporal / openai-agents
conjecture-invariants-*  # domain packs later
```

Do not require multi-repo packaging for a first contribution.

## Example magnets (planted-bug pattern)

Every excellent example includes: working app · planted bug · failing output ·
one-line fix · passing output.

1. Wrong claim / entity id retained after a detour  
2. Duplicate tool execution after retry  
3. Two agents owning the same workflow  
4. Completed task being restarted  
5. Handoff that loses the pinned customer id  

Our in-repo path-faithful demo is the template (`conjecture path-faithful --prove-bugs`
or `conjecture ui`).

## Docs map

| Audience | Doc |
|----------|-----|
| 30-second start | [README.md](README.md) |
| This file | CONTRIBUTING.md |
| Host adapter checklist | [AGENTS.md](AGENTS.md) |
| Architecture / claim hierarchy | [docs/SPEC.md](docs/SPEC.md) (**optional for first PR**) |

## PR hygiene

- One concept per PR  
- Tests for new invariant kinds / drivers  
- No host-private goldens in this repo  
- Fail closed on unknown kinds  

MIT. Welcome.
