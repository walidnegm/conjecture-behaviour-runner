# Examples

**Face claim:** **LLM proposes · code enforces** — freeze-safe **state-law** gates
(owner · pin · handoff/terminal) under pin/freeze; ledger store agnostic (DB /
LangGraph / Temporal / …) as long as Observation projects the rule-set.
not a chat quality product. Inspiration: [Conversation Control Plane](https://github.com/walidnegm/conversation-control-plane).

## Start here (hero)

Multi-turn conversation on a real `handle()` (healthy **PASS** + planted bugs **FAIL**):

```bash
pip install -e ".[dev]"
python examples/e2e_multi_turn.py
# or: conjecture path-faithful --prove-bugs
```

| File | What |
|------|------|
| **`e2e_multi_turn.py`** | In-process MiniChatApp → verifier PASS/FAIL (planted bugs) |
| **`http_debug_app.py`** | **Portable host** — MiniChatApp over HTTP with `debug.owner` / `debug.pins` |
| **`http_e2e.py`** | **HttpJsonAdapter e2e** — real loopback HTTP + `--prove-bugs` |
| **`trajectory_authored_sole_continue.json`** | Script golden (authored trajectory + envelopes) |
| **`trajectory_observed_pass.json`** / **`…_fail_owner_steal.json`** | Observed evidence shapes |
| **`scenario_sole_continue.yaml`** / **`.json`** | Experimental Scenario description language |
| **`scenario_compile_and_run.py`** | Scenario → Script → run (`pip install -e ".[scenarios]"`) |
| `control_plane_goldens.py` | CCP stream unit goldens (`[control-plane]`) |
| **`parameterized_templates.py`** | **Any kind** — `sole_continue_script` / `reorient_keeps_owner_script` |
| `sole_continue_golden.json` / `.yaml` | Portable Script with arrange effects |
| `minimal_script.py` | Null-adapter smoke |

**Templates** (host vocabulary, not product goldens): [`../templates/README.md`](../templates/README.md).

**FAIL** = expected contracts ⊭ `TurnObservation` (state law). Not prose quality.

Agent authoring: [../prompts/conjecture_script_author.seed.md](../prompts/conjecture_script_author.seed.md)
