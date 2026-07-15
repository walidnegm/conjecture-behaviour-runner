# Candidate author template (portable)

**Laws are portable. Host kinds are not.**

This pack is the **template engine** for autonomously authored **Conjecture Scenarios**
(precursor to Scripts). Fill **your** vocabulary — do not ship product agents as
Conjecture enums.

```text
HostVocabulary (your kinds · competing leaves · invent geometry)
        │
        ▼  author_candidates()  (+ invent_all when geometry declared)
  CandidatePath[]
        │  write_candidate_scenarios()
        ▼
  Scenario YAML  →  compile_scenario_to_script()  →  Script
```

## Files

| File | Role |
|------|------|
| `host_vocabulary.example.yaml` | sole-continue kinds + foreign leaves + **invent geometry** |
| `matrix.example.yaml` | finite-expansion cells (`seed_pending` / `gap`) |
| `residual.example.yaml` | hand-authored high-value probes |

Package prompt (editable, out-of-code):  
`src/conjecture_behaviour_runner/candidate_author/prompts/geometry_propose.md`

## Inventor vs expander

| Engine | What it does |
|--------|----------------|
| **Inventor** (prefer first) | Geometry: exclusive surface × typed act × pre-decide stealer |
| **Expander** | Cross-product: sole-continue kind × foreign leaf; matrix / residual / incident seeds |
| **Propose** (optional LLM) | LLM suggests new surfaces/stealers; **code** runs law + physics backcheck |

Principle: **LLM proposes · code enforces.** Proposals never auto-route product chat.
Default invent caps: **4** proposals and **4** inventive scenarios per author turn.
Normative: [`docs/SPEC.md` §2.2](../../docs/SPEC.md).

### Invent env

| Env | Default | Meaning |
|-----|---------|---------|
| `CONJECTURE_INVENT_MAX_PROPOSALS` | 4 | LLM proposals per invent turn |
| `CONJECTURE_INVENT_MAX_SCENARIOS` | 4 | Inventive scenarios emitted per author run |
| `CONJECTURE_INVENT_PROMPT_PATH` | package `prompts/geometry_propose.md` | Out-of-code prompt |
| `CONJECTURE_INVENT_LLM_BASE_URL` | — | OpenAI-compatible base URL |
| `CONJECTURE_INVENT_LLM_MODEL` | — | Model id (your choice; not hardcoded) |
| `CONJECTURE_INVENT_LLM_API_KEY` | — | Secret (or `OPENAI_API_KEY`) |
| `CONJECTURE_INVENT_LLM_TIMEOUT_S` | 60 | HTTP timeout |

Edit the package prompt in place, or point `CONJECTURE_INVENT_PROMPT_PATH` at a
host-maintained copy.

## Quick start

```bash
# Expansive + residual + matrix (example vocabulary)
conjecture candidates author --example --out /tmp/cbr_candidates

# Optional: LLM invent geometry (requires CONJECTURE_INVENT_LLM_*)
export CONJECTURE_INVENT_LLM_BASE_URL=https://api.openai.com/v1
export CONJECTURE_INVENT_LLM_MODEL=gpt-4o-mini   # any model id you choose
export CONJECTURE_INVENT_LLM_API_KEY=...
conjecture candidates author --example --invent-llm --out /tmp/cbr_candidates

# Caps (CLI overrides env)
conjecture candidates author --example --invent-llm \
  --max-invent-proposals 4 --max-invent-scenarios 4 --out /tmp/cbr_candidates

CONJECTURE_CANDIDATES_DIR=/tmp/cbr_candidates conjecture ui
```

Python:

```python
from conjecture_behaviour_runner.candidate_author import (
    load_example_template_bundle,
    author_candidates,
    write_candidate_scenarios,
    invent_all,
    propose_geometry,
    merge_proposals_into_vocab,
)

bundle = load_example_template_bundle()
vocab = bundle["vocabulary"]

# Optional: LLM propose → merge accepted surfaces/stealers into vocab
# result = propose_geometry(vocab, use_env_llm=True)
# vocab = merge_proposals_into_vocab(vocab, result.accepted)

paths = author_candidates(
    vocabulary=vocab,
    matrix_cells=bundle["matrix_cells"],
    residuals=bundle["residuals"],
)
write_candidate_scenarios(paths, "out/scenarios")
```

## Host integration

1. Build `HostVocabulary` from **your** ledger kinds + surface leaves.  
2. Declare invent geometry when you want non-expansive candidates:
   `exclusive_owner_surfaces`, `pre_decide_stealing_leaves`, `typed_reply_acts`,
   `sealed_exclusive_pairs`.  
3. Optionally map STEAL / incident table → `HostIncident`.  
4. Call `author_candidates` + `write_candidate_scenarios`.  
5. Point `CONJECTURE_CANDIDATES_DIR` at the output for the local console.

**Do not** import host agent registries into this package.

## Vocabulary fields

| Field | Meaning |
|-------|---------|
| `sole_continue_kinds` | Mid-flight kinds that own continue |
| `kinds_suppress_surface` | Kinds that suppress foreign surface classifiers |
| `foreign_capability_leaves` | Competing multi-turn starts |
| `foreign_library_leaves` | List/open/inspect leaves |
| `kind_to_owner` | kind → exclusive_owner string |
| `exclusive_owner_surfaces` | Armed finite surfaces that own next free text |
| `pre_decide_stealing_leaves` | Early leaves that steal when a surface is armed |
| `typed_reply_acts` | How users answer without a perfect chip |
| `sealed_exclusive_pairs` | `surface\|stealer` pairs already sealed |
