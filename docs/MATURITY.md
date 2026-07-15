# Package maturity (readiness disclosure)

Honest status for Conjecture Behaviour Runner and the public CAQ-FM companion.  
**Category thesis lives in** [conversational-authority-quality.md](./conversational-authority-quality.md) — not here.

This file is the place for “how ready is the *codebase*,” not the problem statement.

---

## Stage

**Early / OSS alpha (v0.1.x).** Credible doctrine, portable observation shape, mini-app
proofs, thin runnable battery. Not yet a broad enterprise regression product you drop in
for full coverage.

| You get today | You should not expect today |
|---------------|-----------------------------|
| Philosophy + vocabulary (Failure → Law → Proof) | Comprehensive wall of every authority failure |
| Harness + drivers + planted-bug demos | Drop-in coverage for arbitrary free-form agents |
| ~**6 runnable** portable seeds | Most production long-tail sealed in public CI |
| Full **catalog map** with status honesty | Every row `runnable` |

Catalog statuses: **runnable** · **seed_pending** · **host_only**. Hosts (product
codebases) still own most seals.

---

## Architectural fit

Pays rent when the system has (or will have) **exclusive owner**, **entity pins**, and
**yield/handoff** rules. Free-form RAG / prompt-chain bots without that shape need
structure first — or only take the doctrine.

Projection into Observation, multi-turn scripts, and driver maintenance are real work.
SI/vendor/AI can perform the grind; **enterprise owns law acceptance** (see thesis).

---

## Explicit non-goals (package)

| Not Conjecture’s job | Elsewhere |
|----------------------|-----------|
| Classifier / prompt quality | Cognition evals, monitoring |
| Prose tone | LLM eval |
| Domain math | Product tests |
| Deep concurrency / multi-writer races | Host fencing; future multi-actor seeds (gap) |

Green enforce goldens + wrong live labels is still a bad product.

---

## Meaningful next proofs (not more doctrine)

The next credibility milestones are path-faithful, not essay-length:

1. One **external host** integration beyond the mini-app  
2. One implementation by **someone other than the author**  
3. One defect found that **surface eval missed**  
4. One portable contract **rerun across two stacks**  
5. One **SI-style handoff** where the client keeps the same tests after changing implementer  

---

## See also

- [conversational-authority-quality.md](./conversational-authority-quality.md) — thesis  
- [incidents/CATALOG.md](../incidents/CATALOG.md) — map vs battery  
- [README](../README.md) — install and demos  
