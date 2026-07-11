# Examples

**Start here:** multi-turn agentic conversation E2E (healthy + planted bugs):

```bash
pip install -e ".[dev]"
python examples/e2e_multi_turn.py
# or: conjecture path-faithful --prove-bugs
```

| File | What |
|------|------|
| **`e2e_multi_turn.py`** | **Upfront demo** — conversation → MiniChatApp Act → verifier PASS/FAIL |
| `minimal_script.py` | Null-adapter smoke (`always_true`) |
| `control_plane_goldens.py` | CCP adapter goldens (`pip install -e ".[control-plane]"`) |
| `sole_continue_golden.json` / `.yaml` | Portable sole-continue IR (load with `load_script_*`) |

Host-private goldens stay in your application repository; these examples are contract demos only.

```bash
# Structure load (no host adapter required for parse)
python -c "from conjecture_behaviour_runner import load_script_json; print(load_script_json('examples/sole_continue_golden.json').script_id)"
```
