# Parameterized script templates

**Laws are portable. Product goldens are not.**

When you add a multi-turn kind, do **not** copy another host’s `cost_out_*` scripts
and hope they apply. Instantiate these **templates** with **your** ledger vocabulary.

Companion CCP doc: [Host transition discipline](https://github.com/walidnegm/conversation-control-plane/blob/main/docs/host-transition-discipline.md)
(idle reorient = CONTINUE, never COMPLETE; every host result names a transition).

---

## Templates (Python builders)

| Builder | Story | Proves |
|---------|--------|--------|
| `sole_continue_script(...)` | open → pin → bare continue → steal-shaped continue → detour | Owner + pin stick; detour yields |
| `reorient_keeps_owner_script(...)` | mid-flight → terse continue (reorient) → status ask → resume | **No false COMPLETE** on reorient/status |

```python
from conjecture_behaviour_runner import LlmMode, run_script
from conjecture_behaviour_runner.templates import (
    TemplateStreamAdapter,
    reorient_keeps_owner_script,
    sole_continue_script,
)

# Any kind/owner/pin strings — host vocabulary
script = sole_continue_script(
    kind="invoice_intake",
    exclusive_owner="invoice_intake",
    pin_key="invoice_id",
    pin_value="inv_42",
)
result = run_script(script, adapter=TemplateStreamAdapter(), llm_mode=LlmMode.STUB)
assert result.passed
```

**CCP-backed run** (kind must be sole-continue in CCP; pin key should be one the
contract projects, e.g. `workflow_id`):

```python
from conjecture_behaviour_runner.contrib.control_plane import ControlPlaneStreamAdapter
from conjecture_behaviour_runner.templates import sole_continue_script

script = sole_continue_script(
    kind="cost_out",
    exclusive_owner="cost_out",
    pin_key="workflow_id",
    pin_value="wf_1",
)
run_script(script, adapter=ControlPlaneStreamAdapter(), llm_mode=LlmMode.STUB)
```

---

## Parameters

| Param | Meaning |
|-------|---------|
| `kind` | Your ledger `active_task.kind` |
| `exclusive_owner` | Expected exclusive owner (often same as kind) |
| `pin_key` / `pin_value` | Identity freeze for the stream |
| `agent` | Optional agent id on begin (defaults to owner) |
| `open_phase` / `pinned_phase` / `phase` | Host phase strings |

---

## Laws vs goldens

| Layer | Share publicly? |
|-------|-----------------|
| Invariant kinds (`exclusive_owner`, `pin_present`, …) | Yes — package library |
| These templates | Yes — parameterized |
| Your product goldens | Host-private *instances* of templates |

See also: `demo_scripts()` — two synthetic `demo_task` instances for CI smoke.

---

## Candidate author (Scenario precursor)

Autonomously author **candidate Scenarios** from host vocabulary (no LLM):

| | |
|--|--|
| **Template pack** | [`candidate_author/`](candidate_author/) |
| **Python** | `conjecture_behaviour_runner.candidate_author` |
| **CLI** | `conjecture candidates author --example --out DIR` |

Host fills kinds/leaves; engine emits Scenario YAML for the local console
(`CONJECTURE_CANDIDATES_DIR`). Product STEAL tables stay on the host.
