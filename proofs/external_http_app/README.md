# External HTTP app (portability proof)

**This directory is the system under test.** It must **not** import
`conjecture_behaviour_runner`. Conjecture talks to it **only over HTTP**.

```text
proofs/external_http_app/app.py     ← independent SUT
        ↓  HTTP POST /chat
HttpJsonAdapter (Conjecture package)
        ↓
portable sole-continue golden
        ↓
Conjecture verifier
```

## Run

```bash
# from package root (with conjecture installed or PYTHONPATH=src for the *runner* only)
python proofs/run_external_http_proof.py --prove-bugs
```

Or manually:

```bash
# terminal A — SUT only
python proofs/external_http_app/app.py --port 8790

# terminal B — Conjecture client
PYTHONPATH=src python proofs/run_external_http_proof.py \
  --endpoint http://127.0.0.1:8790/chat --prove-bugs
```

Plant bugs on the **app** process (`--bug owner_steal|drop_pin|illegal_restart`), not in Conjecture.
