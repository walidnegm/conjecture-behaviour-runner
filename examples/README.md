# Examples

**Canonical stack** (same as README / CBR-SPEC / docs/README — abbreviated here):

```text
  seeds (specs · Collinear/other multi-turn tools · agent · human)
       → authored TRAJECTORY of twists
       → Conjecture Scenario and/or Conjecture Script
       → control-plane runner (run_script) + Driver
       → OBSERVED TRAJECTORY → VERIFIER
       → pytest / CI only *hosts* the run
```

## Start here

Multi-turn agentic conversation (healthy **PASS** + planted bugs **FAIL**):

```bash
pip install -e ".[dev]"
python examples/e2e_multi_turn.py
# or: conjecture path-faithful --prove-bugs
```

| File | What |
|------|------|
| **`e2e_multi_turn.py`** | E2E: conversation → MiniChatApp Act → verifier PASS/FAIL |
| **`trajectory_authored_sole_continue.json`** | **Authored trajectory** as Conjecture Script (twists + expected envelopes) |
| **`trajectory_observed_pass.json`** | **Observed trajectory** after a healthy run (PASS) |
| **`trajectory_observed_fail_dual_owner.json`** | Observed trajectory when continue steals owner (FAIL) |
| `minimal_script.py` | Null-adapter smoke (`always_true`) |
| `control_plane_goldens.py` | Control-plane adapter goldens (`pip install -e ".[control-plane]"`) |
| `sole_continue_golden.json` / `.yaml` | Portable sole-continue **Conjecture Script** (adapter-oriented effects) |

**Authored vs observed:** you write Script JSON (path + expected). The runner emits
observed JSON (`RunResult` / observations). FAIL = expected ⊭ observation.

Host-private goldens stay in your application repository.

Agent authoring: [../prompts/conjecture_script_author.seed.md](../prompts/conjecture_script_author.seed.md)  
( trajectory + ODD worksheet → Script JSON ).
