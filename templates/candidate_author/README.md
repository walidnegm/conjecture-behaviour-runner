# Candidate author template (portable)

**Laws are portable. Host kinds are not.**

This pack is the **template engine** for autonomously authored **Conjecture Scenarios**
(precursor to Scripts). Fill **your** vocabulary — do not ship product agents as
Conjecture enums.

```text
HostVocabulary (your kinds · competing leaves)
        │
        ▼  author_candidates()
  CandidatePath[]
        │  write_candidate_scenarios()
        ▼
  Scenario YAML  →  compile_scenario_to_script()  →  Script
```

## Files

| File | Role |
|------|------|
| `host_vocabulary.example.yaml` | sole-continue kinds + foreign capability/library leaves |
| `matrix.example.yaml` | finite-expansion cells (`seed_pending` / `gap`) |
| `residual.example.yaml` | hand-authored high-value probes |

## Quick start

```bash
# From package root (or any host that installed conjecture-behaviour-runner)
conjecture candidates author --example --out /tmp/cbr_candidates
conjecture ui   # set CONJECTURE_CANDIDATES_DIR=/tmp/cbr_candidates
```

Python:

```python
from conjecture_behaviour_runner.candidate_author import (
    load_example_template_bundle,
    author_candidates,
    write_candidate_scenarios,
)

bundle = load_example_template_bundle()
paths = author_candidates(
    vocabulary=bundle["vocabulary"],
    matrix_cells=bundle["matrix_cells"],
    residuals=bundle["residuals"],
)
write_candidate_scenarios(paths, "out/scenarios")
```

## Host integration (e.g. Bot0)

1. Build `HostVocabulary` from **your** ledger kinds + surface leaves.  
2. Optionally map STEAL / incident table → `HostIncident`.  
3. Call `author_candidates` + `write_candidate_scenarios`.  
4. Point `CONJECTURE_CANDIDATES_DIR` at the output for the local console.

**Do not** import host agent registries into this package.

## Vocabulary fields

| Field | Meaning |
|-------|---------|
| `sole_continue_kinds` | Mid-flight kinds that own continue |
| `kinds_suppress_surface` | Kinds that suppress foreign surface classifiers |
| `foreign_capability_leaves` | Competing multi-turn starts |
| `foreign_library_leaves` | List/open/inspect leaves |
| `kind_to_owner` | kind → exclusive_owner string |
