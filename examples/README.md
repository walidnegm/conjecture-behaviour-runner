# Examples

- `minimal_script.py` — stub pin + null adapter (no control-plane install required)
- `control_plane_goldens.py` — three portable goldens against the real Conversation Control Plane multi-turn stream contract (`pip install -e ".[control-plane]"`)

Host-private goldens stay in your application repository; these examples are contract demos only.

| File | What |
|------|------|
| `minimal_script.py` | Null-adapter smoke (`always_true`) |
| `control_plane_goldens.py` | Live CCP adapter + three portable goldens |
| `sole_continue_golden.json` | Full multi-turn sole-continue golden (load with `load_script_json`) |
| `sole_continue_golden.yaml` | Same shape in YAML (`load_script_yaml`, needs PyYAML / `[scenarios]`) |

```bash
# Structure load (no host adapter required for parse)
python -c "from conjecture_behaviour_runner import load_script_json; print(load_script_json('examples/sole_continue_golden.json').script_id)"
```
