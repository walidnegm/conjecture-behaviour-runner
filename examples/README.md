# Examples

**Face claim:** freeze-safe **state-law** gates (owner · pin · terminal) under pin/freeze —
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
| **`e2e_multi_turn.py`** | **Hero** — MiniChatApp Act → verifier PASS/FAIL (planted bugs) |
| **`trajectory_authored_sole_continue.json`** | Script golden (authored trajectory + envelopes) |
| **`trajectory_observed_pass.json`** / **`…_fail_dual_owner.json`** | Observed evidence shapes |
| **`scenario_sole_continue.yaml`** / **`.json`** | Experimental Scenario description language |
| **`scenario_compile_and_run.py`** | Scenario → Script → run (`pip install -e ".[scenarios]"`) |
| `control_plane_goldens.py` | CCP stream unit goldens (`[control-plane]`) |
| `sole_continue_golden.json` / `.yaml` | Portable Script with arrange effects |
| `minimal_script.py` | Null-adapter smoke |

**FAIL** = expected contracts ⊭ `TurnObservation` (state law). Not prose quality.

Agent authoring: [../prompts/conjecture_script_author.seed.md](../prompts/conjecture_script_author.seed.md)
