# Candidate author template (portable)

**Laws are portable. Host kinds are not.**

This pack is the **template engine** for autonomously authored **Conjecture Scenarios**
(precursor to Scripts). Fill **your** vocabulary — do not ship product agents as
Conjecture enums.

**Taxonomy (working, not FMEA):** failure mode **slug** = unique registry `id` (class) →
many **incidents** / **candidate scenarios** (trajectories you author here) → **sealed
pattern** → **execution evidence**. Rows you emit are scenarios, not modes. See CAQ
[Working taxonomy](../../docs/conversational-authority-quality.md#working-taxonomy-not-fmea-reinvention)
and the local console Help panel.

### Conceptual split (not harness-first)

| Concept | Meaning |
|---------|---------|
| **User trajectory** | The behavioral story |
| **Scenario geometry** | Normalized conditions that make it adversarial (`surface` × `act` × stealer, pins) |
| **Failure-mode mapping** | Class of violation stressed (registry **slug**, e.g. `owner_steal`) |
| **Mode detection** | Observable evidence the mode materialized (asserts / traces) — not an “oracle” |

Authoring order:

1. What is the user trying to do?  
2. What state is the system in?  
3. What unexpected but plausible action occurs?  
4. What must the system do?  
5. What evidence would show the mode hit?  

**Twist 0** = test-harness setup (arm surface) — not end-user chat.  
**Twist 1+** = real user free-chat under that surface.

### Console runs (file-based)

The local console can **run** a candidate via a stub `GeometryHoldAdapter` and write
**execution evidence** under:

```text
candidates/scenarios/evidence/<scenario_id>/<timestamp>_healthy.json
candidates/scenarios/evidence/<scenario_id>/latest.json
```

That directory is **gitignored**. Evidence JSON uses the working taxonomy:

`failure_mode` · `candidate_scenario` · `user_trajectory` · `scenario_geometry` ·
`mode_detection` · pass/fail.

Planted steal (`?steal=1`) yields ownership to the stealer so detection can FAIL.
A real host Driver is still required for path-faithful product Act.

```text
📍 Discovery path: Host vocab → Invent → Expand → Scenario → Script → Sealed
   (same tracker contract as Prose → Draft IR → Staffed IR → Compile/save)

HostVocabulary (your kinds · competing leaves · invent geometry)
        │
        ▼  author_candidates()  (invent first, then expand)
  CandidatePath[]
        │  write_candidate_scenarios()
        ▼
  Scenario YAML  →  compile_scenario_to_script()  →  Script  →  Sealed pattern
```

Pretty diagram: [`docs/images/discovery-pipeline.svg`](../../docs/images/discovery-pipeline.svg) ·  
Python strip: `pipeline_tracker.render_discovery_lifecycle_diagram("scenario")`

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
