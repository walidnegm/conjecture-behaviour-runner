# Session reviewer protocol — monorepo coding agent

**Role:** findings + verdict + **suggested fixes** after a Conjecture run.  
**Not** the invent/author LLM. **Not** the runner (Python only).

You operate **in the host monorepo coding session** (any agent with path-faithful
code + conversation access — Cursor, Claude Code, Grok Build, Codex, …).  
Optional display brand: `CONJECTURE_SESSION_AGENT_LABEL` (default:
`session coding agent`). You have access to code, local/staging conversation
history, and the review backlog under the host backlog dir (Bot0:
`conjecture_host/expansion/backlog/`).

## Triggers (two commands)

User (or habit after a batch):

```text
review conjecture backlog
```

Develop findings + classify. `product_bug` stays **open** as `backlog_fix`.

After findings are developed and seals are ready (or already implemented):

```text
fix
```

**Close open items** and **document the patch on each closed item** via
`close_with_patch` / `close_open_with_patch` (or `POST /api/backlog/close`).

Or: process a single `items/<id>.json` / conversation id they name.

## Inputs (per backlog item)

* `scenario_id`, `failure_mode`, `adapter`, `product_path`
* `conversation_id` / `thread_id` (when host E2E ran)
* `run_passed`, `run_error`, `evidence_path`
* `findings_skeleton` / deterministic tables (code-owned; may be thin)
* Candidate YAML under `candidates/scenarios/` when present

## What you do

1. **Load** the item and scenario purpose / must_hold / mode_detection.  
2. **If conversation_id present** — read transcript + route_data + control events
   (local Postgres or staging admin API per host AGENTS.md).  
3. **Layer trace** (product): claim → cleanup → guardrails → router → referential
   / decide → leaf delivery. Name the earliest wrong layer.  
4. **Classify** (exactly one):

   | Label | When |
   |-------|------|
   | `conjecture_caught` | CAQ law PASS/FAIL is correct and sufficient; product behaved per sealed contract |
   | `product_bug` | User-visible flow wrong (intent, leaf, empty surface, improve pipeline miss, …) — **even if** soft invariants “passed” |
   | `rate_limit` | 429 login / llm_hour / chat / conversation_create |
   | `infra` | Empty shell, adapter misconfig, missing password, wrong base URL |
   | `inconclusive` | Cannot decide without more evidence |

5. **Write findings** in the agreed table shape (below).  
6. **Suggest fixes** as concrete monorepo actions (files, contracts, ratchets, STEAL rows).  
7. **Update backlog** via `update_backlog_item` or edit `items/<id>.json`:
   * `product_bug` → `status: backlog_fix` (**stays open** until `fix`)  
   * `conjecture_caught` / `rate_limit` / `infra` → usually `closed`  
8. **On user command `fix`:** implement high-priority `product_bug` seals
   (contract + path-faithful ratchet), then **close open items with patch
   documentation** — do not leave `backlog_fix` hanging after the work shipped.

### `fix` close protocol (required)

After implementing (or confirming already-landed) seals:

1. Prefer `close_with_patch(item_id, patch={...})` or
   `close_open_with_patch(patch={...}, item_ids=[...])`.
2. That sets: `status=closed`, `classification=fixed`, and stores **`patch`**
   on the item:

```json
{
  "summary": "one-line what shipped",
  "files": ["path/to/changed.py", "tests/..."],
  "commits": ["abc1234"],
  "tests": ["test_module.py::test_case"],
  "seal": "contract + ratchet name",
  "notes": "optional longer note"
}
```

3. The **closed** item is the permanent record of the patch — not a side chat.
4. Re-run the scenario when possible to prove the seal.

## Findings JSON (authoritative shape)

```json
{
  "headline": "<one line>",
  "verdict": "PASS | FAIL | INCONCLUSIVE | ERROR",
  "classification": "conjecture_caught | product_bug | rate_limit | infra | inconclusive",
  "what_should_have_happened": [
    {"index": 0, "role": "user|assistant|setup|system", "what_happened": "..."}
  ],
  "what_actually_happened": [
    {"index": 0, "role": "user|assistant|setup|system", "what_happened": "..."}
  ],
  "expected_vs_observed": [
    {
      "aspect": "exclusive_owner | delivery_leaf | improve_pipeline | ledger | ...",
      "expected": "...",
      "observed": "...",
      "match": false
    }
  ],
  "what_went_wrong": "<plain English>",
  "root_cause_hypothesis": "<layer + mechanism>",
  "code_path_hypothesis": "symbol → symbol → symbol",
  "failure_mode_slug": "<registry slug or empty>",
  "suggested_fixes": [
    {
      "priority": "P0|P1|P2",
      "title": "<short>",
      "layer": "referential|decide|leaf|prompt|driver|infra|test",
      "files": ["path/to/file.py"],
      "action": "<what to change — seal, not phrase laundry>",
      "ratchet": "<test module or residual path_id if known>"
    }
  ],
  "seal_recommendation": "<one paragraph>",
  "confidence": 0.0
}
```

## Analysis object (store on backlog item)

```json
{
  "prose": "<narrative soak write-up, complete sentences>",
  "classification": "product_bug",
  "conversation_id": "conv_…",
  "suggested_fixes": [ ],
  "related_scenarios": ["…"],
  "reviewed_at": "<iso>",
  "reviewer": "session_agent"
}
```

## Rules

* Prefer **path-faithful** proof (same entrypoint as the user: chat / SSE / ledger).  
* **Never** sole-fix product bugs with synonym laundry lists.  
* Soft host Observation (agent_type only) is not proof of exclusive-owner health.  
* Empty transcript + 429 → `rate_limit` / `infra`, not `conjecture_caught`.  
* PASS invariants + wrong product leaf → **`product_bug`**, not ignore.  
* Suggest fixes you could implement in this monorepo in the same session.

## Related process doc

Host monorepo: `docs/conjecture-multi-agent-pipeline.md`
