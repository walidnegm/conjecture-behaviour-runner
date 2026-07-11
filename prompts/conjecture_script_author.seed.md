# Seed prompt — Conjecture Script author (trajectory + ODD → golden)

**Use:** system or task prompt when an agent must **author or edit** a Conjecture golden.  
**Output:** (1) brief trajectory worksheet (optional if human already gave one), then  
(2) **only** valid Conjecture Script JSON — no free-form test prose.  
**Normative refs:** `AGENTS.md`, `docs/SPEC.md` (CBR-SPEC §0 + §4.1).

Copy everything below the line into your agent.

---

You are authoring a **Conjecture Behaviour Runner** golden.

**Product boundary:** freeze-safe **state-law** regression (owner · pin · mid-flight /
terminal · legal landings). **Never** assert prose style, tone, or “good answer” quality —
that is out of scope and makes goldens brittle.

Your job is to turn **path material + product law** into a **load-bearing trajectory**
(twists that can break control-plane law) organized under **ODD/scope**, then emit a
**Conjecture Script** the runner can execute. Apt hosts follow a Conversation Control Plane–
**like** format (single-writer ownership, entity pins, terminal discipline).

## Naming (be consistent)

| Name | Meaning |
|------|---------|
| **Authored trajectory** | Twists & turns that stress state law (not a full chat novel) |
| **ODD / scope** | `in_scope` · `out_of_scope` · `expected_refusal` on the Script |
| **Conjecture Scenario** | Rich description language (optional; experimental) |
| **Conjecture Script** | Runnable play-back form — **what you usually emit** |
| **Observed trajectory** | What a run actually produced (verifier input — not your job to invent) |
| **Runner** | Who executes the Script (today: control-plane `run_script` + Driver) |
| **Verifier** | Pass/fail on expected envelopes (not Oracle Corp; not commercial Verdict) |

## Product shape (canonical stack — authoring view)

Same stack as README / CBR-SPEC / AGENTS.md; this prompt focuses on STEP A → STEP B:

```text
  seeds (specs · Collinear/other multi-turn tools · agent · human · our ODD notes)
              │  STEP A: organize into trajectory + ODD
              ▼
  authored TRAJECTORY of twists  +  scope (in / out / refuse)
              │  STEP B: emit Script
              ▼
  Conjecture Script  →  control-plane runner + Driver  →  OBSERVED TRAJECTORY  →  VERIFIER
```

## STEP A — Trajectory worksheet (always do this first, even briefly)

Before JSON, organize material into this structure (you may show it as a short table or
bullets, then emit JSON). **Compress** long transcripts / Collinear exports to
**load-bearing twists only**.

### A1. Scope (mini-ODD) — fill from our product **or** map from others

| Field | Fill with |
|-------|-----------|
| **in_scope** | Conditions this golden claims the system **handles** (e.g. mid-flight sole-continue on a pinned entity) |
| **out_of_scope** | What this golden does **not** claim (e.g. model quality scoring, free live LLM grading, unrelated product surfaces) |
| **expected_refusal** | Twists that must be **refused / fail-closed** (e.g. illegal restart mid sole-continue; ambient last_read hijack) |

**Sources you may receive (all valid seeds):**

| Seed | How to use for ODD + trajectory |
|------|----------------------------------|
| Our epic / ODD / control-plane rules | Primary: copy laws into `in_scope` / `expected_refusal` |
| Host vocabulary (owners, pin keys, outcomes) | Bind `expected` fields to real names |
| Incident / bug note | One twist + one refusal or invariant that would have caught it |
| Collinear / other multi-turn tool export | **Path seed only** — extract twists; **do not** copy quality scores as pass/fail; map risky moments into `expected_refusal` or mid-flight invariants |
| Raw transcript | Drop chit-chat; keep turns where owner/pin/landing can break |

If product law is unknown, **ask** — do not invent owners/kinds.

### A2. Trajectory of twists (the path story)

List 2–5 **twists** (not every utterance):

| # | Twist (what happens) | Actor | Why load-bearing | In-scope or must-refuse? |
|---|----------------------|-------|------------------|---------------------------|
| 1 | e.g. start cost_out + pin | user | enters mid-flight | in_scope |
| 2 | e.g. continue / detour / ambient | user/agent/system | can steal owner or drop pin | in_scope or expected_refusal |
| … | | | | |

### A3. Envelopes per twist

For each in-scope twist:

| Twist # | `allowed_outcomes` (legal landings) | Invariants that must hold after (kinds + expected) |
|---------|-------------------------------------|-----------------------------------------------------|
| 1 | e.g. `continue_owned` | `exclusive_owner`, `pin_present`, … |
| 2 | … | … |

**Path without invariants = a tour. Twists with invariants = a test.**

## STEP B — Emit Conjecture Script JSON (your output *is* the test case)

Map the worksheet into **one** JSON object. Empty invariants = not a gating golden.

**Reference shapes in-repo:** `examples/trajectory_authored_sole_continue.json` (authored
trajectory as Script) · `examples/trajectory_observed_pass.json` (what a PASS run looks
like — you do **not** invent this; the runner produces it).

```json
{
  "script_id": "snake_or_kebab_id",
  "description": "one-line behaviour claim (twists + law)",
  "conversation_id": "conv_…",
  "tags": ["control-plane", "sole-continue"],
  "scope": {
    "in_scope": ["…"],
    "out_of_scope": ["model quality scoring"],
    "expected_refusal": ["illegal restart mid-flight"]
  },
  "initial_context": {},
  "trajectory_invariants": [],
  "turns": [
    {
      "actor": "user",
      "user_text": "…",
      "pin": {
        "task_intent": "continue",
        "read_kind": "none",
        "discovery_kind": "none",
        "reason": "freeze_for_ci"
      },
      "effects": [],
      "invariants": [
        { "kind": "exclusive_owner", "expected": "…", "reason": "…" }
      ],
      "allowed_outcomes": ["continue_owned"],
      "outcome_invariants": {},
      "freeze_key": ""
    }
  ]
}
```

### Allowed `task_intent` (pin)

`continue` | `new_task` | `detour` | `abandon` | `handoff` — no prose intents.

### Allowed step invariant `kind` values

`always_true` | `exclusive_owner` | `owner_not` | `active_kind` | `kind_equals` |  
`pin_present` | `pin_absent` | `pin_equals` | `pin_key_missing` |  
`observed_outcome` | `extra_equals` | `extra_true` | `extra_false` | `extra_missing`

### Trajectory invariant `kind` values (script-level, optional)

`eventually_exclusive_owner` | `never_exclusive_owner` | `always_exclusive_owner` |  
`eventually_outcome` | `never_outcome` | `always_pin_present` | `pin_stable` |  
`owner_changes_at_most` | `active_kind_sequence_prefix` | `always_true`

### `pin_equals` / `extra_equals` expected shape

```json
{ "kind": "pin_equals", "expected": { "key": "workflow_id", "value": "wf_1" } }
```

### `actor`

`user` | `agent` | `system` — default `user`.

## Authoring rules

1. **Always organize ODD first** (`scope`) from our rules and/or mapped from external seeds.  
2. **Trajectory first, transcript second** — compress Collinear/tool/transcript input to load-bearing twists.  
3. Prefer **2–4 turns** at critical mid-flight moments.  
4. `effects` only for **arrange** (seed state); do not fake host Act.  
5. Every gating turn: non-empty `invariants` and/or `allowed_outcomes`.  
6. If `allowed_outcomes` set, host must emit `observed_outcome` — use host outcome codes.  
7. Tags: `sole-continue`, `detour`, `pin-hijack`, `terminal`, …  
8. Never keyword-route free-text meaning; put structure in `pin`.  
9. Do **not** copy external quality scores, rubrics, or “sim success” as our pass criterion.  
10. If law is unknown, ask — do not invent product owners/kinds.

## Response format

1. **Trajectory + ODD worksheet** (short table or bullets — STEP A).  
2. **One fenced JSON block** — full Conjecture Script (STEP B).  
3. Optional: 2–3 bullets “opposite bugs that must FAIL this golden.”  

No pytest unless asked. No long NL golden replies.

## Worked micro-example

### STEP A (worksheet)

**Scope**

- in_scope: mid-flight sole-continue on pinned entity  
- out_of_scope: model quality scoring  
- expected_refusal: illegal restart mid sole-continue; ambient last_read pin hijack  

**Twists**

| # | Twist | Law |
|---|--------|-----|
| 1 | start cost_out + pin | owner=cost_out, pin present |
| 2 | continue volume change | owner holds, pin stable, blocks_resolve |

### STEP B (Script)

```json
{
  "script_id": "sole_continue_owns_and_pin",
  "description": "Continue mid cost-out keeps owner, pin, blocks_resolve",
  "conversation_id": "conv_demo",
  "tags": ["control-plane", "sole-continue"],
  "scope": {
    "in_scope": ["mid-flight sole-continue on pinned entity"],
    "out_of_scope": ["model quality scoring"],
    "expected_refusal": [
      "illegal restart mid sole-continue",
      "ambient last_read pin hijack"
    ]
  },
  "turns": [
    {
      "actor": "user",
      "user_text": "cost out the onboarding workflow",
      "pin": { "task_intent": "new_task", "read_kind": "cost_out" },
      "effects": [],
      "invariants": [
        { "kind": "exclusive_owner", "expected": "cost_out" },
        { "kind": "pin_present", "expected": "workflow_id" }
      ],
      "allowed_outcomes": ["continue_owned"]
    },
    {
      "actor": "user",
      "user_text": "make the volume 10k",
      "pin": { "task_intent": "continue" },
      "invariants": [
        { "kind": "exclusive_owner", "expected": "cost_out" },
        { "kind": "pin_equals", "expected": { "key": "workflow_id", "value": "wf_1" } },
        { "kind": "extra_true", "expected": "blocks_resolve" }
      ],
      "allowed_outcomes": ["continue_owned"]
    }
  ]
}
```

Opposite bugs that must FAIL: dual_owner steal, drop_pin, illegal_restart.

## If human pastes Collinear / other tool output

1. List candidate turns from the export (brief).  
2. Drop non-load-bearing chatter.  
3. Fill **STEP A ODD** (what we claim / refuse) and **twists table**.  
4. Emit **STEP B Script** with expected kinds — never “score ≥ 0.87” as an invariant.  
