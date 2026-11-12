# Incident: act reinterpreted downstream (portable seed)

| Field | Value |
|-------|--------|
| **Slug** | `act_reinterpreted_downstream` |
| **Date** | 2026-09-15 |
| **Host** | Bot0 (control-plane reference host) |
| **Conjecture-class?** | yes |

## Symptom

A user clicks one chip. The product answers **four different things across
four turns**, and none of them is the act the chip carried. Every individual
reply is well-formed. Nothing errors. The ledger is not corrupt. Chat looks
fine, and the state law is wrong — which is why this is Conjecture-class and
not a unit test.

The act was never ambiguous. Grounding resolved it **correctly** on the third
turn. The failure is entirely downstream of the semantic commit point: three
separate stages each answered as though the act were something else.

| turn | what the product said | which stage took it |
|------|----------------------|---------------------|
| 1 | a product blurb — "I'm here to help you build workflows" | a topicality guard that recognised the chip by its SENTENCE, and the sentence had changed |
| 2 | "The last build didn't succeed yet." | a recovery classifier evaluated the chip against a surface where it means nothing, got `other`, and answered anyway |
| 3 | "Now describe the workflow you'd like to build." | the act resolved — then a ladder whose return type **could not express the state it was in** fell through to its default arm |
| 4 | "Continue on the card for the next pre-save step." | same default arm; there was no card to continue on |

## Expected law

| Field | Expected | Observed (bug) |
|-------|----------|----------------|
| act (per turn) | stable — the act cognition committed | changes turn to turn |
| outcome when not grounded | `ask` / `reject` / `defer` | prose, four times |
| grounding | resolved once | resolved correctly, then ignored |

**I8** — after cognition commits the canonical act, downstream may refine
refs, ASK, REJECT, DEFER, DENY or FAIL. It may **not** reinterpret the act
into another act.

**I10** — unresolved means ASK / REJECT / DEFER. It is never a licence to
generate a conversational answer.

## Why a per-turn invariant cannot catch it

Turn 2 in isolation is a legitimate reply from a host with a failed build.
Turn 4 in isolation is a legitimate "continue on the card". Only the
**trajectory** shows that a single committed act produced four answers. That
is what `act_stable` is for, and it is the reason this seed exists as a
script rather than as an assertion.

## Notes

Demo vocabulary. Port by replacing the act id and the gate names with your
own. The host fills two observation extras:

* `extras["act"]` — the act this turn actually dispatched.
* `extras["grounded"]` — whether that act had everything it needed.

A host that reports neither is not failing this pattern; it is **abstaining**
from it, and `never_invented` stays silent by design. Reporting them is the
adoption step.
