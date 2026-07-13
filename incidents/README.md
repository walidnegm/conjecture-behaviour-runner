# Incident → Conjecture pattern library

When a multi-turn agent misbehaves, the bug is often **not** “the model said the
wrong words.” It is often: an agent **submitted the wrong type into the ledger**,
**ignored the ledger contract**, or **soft-enforced** sole-continue / pin /
handoff / **open leaf**. If the **ledger SDK is complete**, those become **host
implementation** bugs — and many of them are exactly what Conjecture is for.

## Start here (documentation map)

| Need | Open |
|------|------|
| **Patterns inventory (listed + described)** | [`CATALOG.md`](CATALOG.md) |
| **This playbook** (classify → capture → land) | this file |
| **One pattern** | `patterns/<slug>/INCIDENT.md` + `script.json` |
| **Copy template** | [`_template/`](_template/) |
| **Package face / planted-bug demo** | [`../README.md`](../README.md) |
| **Normative package spec** | [`../docs/SPEC.md`](../docs/SPEC.md) |
| **Agent coder on-ramp** | [`../AGENTS.md`](../AGENTS.md) §7 |
| **Host term lexicon** (Bot0 dogfood) | Host repo vocabulary doc (not shipped in this package) |

**`tests/` is not the inventory** — those are package unit tests.  
**The inventory is `CATALOG.md` + `patterns/`.**

---

## Learning loop

```text
live bug (chat / logs / ledger row)
        │
        ▼
  Is it Conjecture-class?  ──no──► fix elsewhere (classifier, domain math, UI copy…)
        │ yes
        ▼
  Capture as Scenario (describe the twist + expected law)
        │
        ▼
  Compile / author Script (executable golden)
        │
        ▼
  Prove FAIL on the broken path, PASS after the fix
        │
        ▼
  Land under patterns/ + CATALOG.md  → forever regression
```

## 1. Classify: is this a Conjecture-type bug?

Answer **yes** only if **all three** hold (or two strongly + pin/freeze is usable):

| # | Question | Conjecture-class signal |
|---|----------|-------------------------|
| 1 | Did the **reply look fine** (or plausible) while **state law** was wrong? | User trusted prose; owner/pin/handoff/open was illegal |
| 2 | Is the expected rule expressible as **owner · kind · pin · blocks_resolve · outcome** after Act? | Maps to standard invariant kinds |
| 3 | Can we **pin/freeze cognition** (continue / detour / new_task / …) so the failure is deterministic in CI? | Not “live model vibe” |

### Usually **yes** (host implementation of ledger / delivery contract)

- Wrong `exclusive_owner` / `active_kind` after a turn (steal to front door)
- Pin dropped, swapped, or re-resolved while sole-continue owns the stream
- Illegal restart / greenfield wipe mid-flight
- Handoff / abandon / detour wrong vs rule-set
- **pin_without_open** — identity pin correct, **open leaf** missing (pin-status only)
- Dual write / second owner while mid-flight

### Usually **no** (not Conjecture’s primary job)

| Class | Where it lives instead |
|-------|-------------------------|
| Classifier / router label wrong under free text | Cognition tests, prompt rubrics |
| Ledger **SDK** incomplete | CCP package tests — fix SDK first |
| Domain math, tables, financial formulas | Domain / renderer tests |
| Prose quality, tone | LLM eval |
| Pure infra (DB down, 500) | Ops / health |

## 2. Capture: Scenario then Script

| Artifact | Role | When |
|----------|------|------|
| **`INCIDENT.md`** | Human story: symptom, layer, expected law | Always |
| **`scenario.yaml`** (optional) | Rich description: twists, scope | Prefer for learning / ODD |
| **`script.json`** | **The CI golden** — turns + invariants + pins | Required for regression |

1. Write `INCIDENT.md` from the real failure.
2. Author `script.json` (or compile from scenario).
3. **Red first** on bug / planted equivalent; then green after fix.
4. Register in **`CATALOG.md`**.

Templates: [`_template/`](_template/).

Host kinds and pins are **your** vocabulary — demos use stand-ins only.

## 3. Layout

```text
incidents/
  README.md                 ← this playbook
  CATALOG.md                ← patterns inventory (list + describe)
  _template/
  patterns/
    <slug>/
      INCIDENT.md
      script.json           ← required
      scenario.yaml         ← optional
```

**Portable patterns** (no product secrets) ship here.  
**Host-private** product goldens stay in the host application repository.

## 4. Host application (product dogfood)

Keep full chat-path scripts, freezes, and path seals **in the host repo** next to
the product. This public tree only carries **portable** seeds (mini-app kinds /
pins as stand-ins).

## 5. Agent coder checklist

```text
[ ] Symptom: looks fine in chat / wrong underneath?
[ ] Expected law named (owner K, pin P, open surface, no restart, …)
[ ] Cognition pin/freeze set
[ ] Script with invariants (not empty tour)
[ ] FAIL on broken path; PASS after fix
[ ] CATALOG.md row + patterns/<slug>/
[ ] Host kinds/pins are host vocabulary
```

Prompt seed: [`../prompts/conjecture_script_author.seed.md`](../prompts/conjecture_script_author.seed.md).

## 6. What we learn over time

The **catalog is the memory**: which failure classes recur, which host kinds are
fragile, whether fixes were SDK vs implementation. That is Conjecture as
**executable memory of state-law breaks**.
