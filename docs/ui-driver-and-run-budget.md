# UI driver and run budget

A pattern for checking an agentic product **through its own UI**, repeatably,
without letting a check turn into an open-ended model bill.

## Why

Agents (and people) verify UI changes with throwaway browser scripts. They are
path-faithful — they use the screen the user uses — but nothing re-runs them,
nothing caps what they spend, and nothing records what they proved. A UI
check belongs behind the same contract as every other run: a **Scenario** in,
an **Observed trajectory** out, with a **Driver** plugin doing the clicking.

## The pieces

| Piece | Module | Host's job |
|---|---|---|
| **UI step grammar** | `conjecture_behaviour_runner.ui_grammar` | Implement the locators and checks in your driver |
| **Run budget** (circuit breaker) | `conjecture_behaviour_runner.budget.RunBudget` | Inject a `model_calls()` counter from your usage log / gateway |
| **UI driver** | your adapter (Playwright, Cypress, …) | Map maneuvers to clicks; call `budget.check(step_id)` before each step |

**Grammar** — small on purpose:

```text
locator   testid:<id>[#n] · text:<text> · placeholder:<text> · role:<role>=<name>
checks    visible:<loc> · hidden:<loc> · count:<loc>=<n> · text:<loc>~<sub>
          networkidle · delay:<ms> · model_calls_at_most:<n>
maneuvers navigate · click · fill · press · expect
${NAME}   replaced from the environment, so one scenario runs on any seeded stack
```

**Budget** — checked **before every step**:

```python
from conjecture_behaviour_runner.budget import RunBudget

budget = RunBudget(model_calls=my_usage_counter)   # default cap 0, 300 s
for step in scenario.steps:
    budget.check(step.id)        # raises BudgetExceeded: over cap, over time, or unmeasurable
    driver.drive(step)
```

- Default model-call cap is **0**. A deterministic UI flow spends nothing; a
  non-zero count is itself a finding (something on that path called a model).
- A behaviour run that must cross a model **raises the cap on purpose**.
- An unmeasurable budget **refuses to run** — never run blind.
- A recursive or runaway loop stops at the next step, with the reason on the
  trajectory.

## Say what kind of evidence you produced

| Kind | What it proves | With a UI driver |
|---|---|---|
| **Sanity** | the change does what it says on the real path, once | a scenario run by hand after a change — the default use |
| **Regression** | a committed check fails without the fix | only when the scenario is committed **and** a test runs it (usually nightly / local, not the pre-push gate — it needs a live stack) |
| **Behaviour** | an envelope of allowed outcomes over runs | needs non-deterministic steps, N runs, and a declared budget |
| **Failure mode** | a named mode does not recur | only when the scenario names the mode it guards (see `incidents/registry.yaml`) |
| **Functional / non-functional** | does it work · how long, how much | invariants · step latency and the model-call count on the trajectory |

## Deterministic vs behaviour, and what it costs

A flow over code-owned surfaces (forms, canvases, cards) is **deterministic**:
budget 0, single run, cheap. A flow that crosses cognition (a chat turn, an
extraction, a "suggest" button) is **behaviour**: every run costs real tokens,
so run it rarely, with an explicit cap, and **save the raw model output as a
fixture** so cheap tests replay it instead of calling the model again.

## Which failure modes a UI driver can see

Those whose symptom is on the screen: hollow open / hollow advance (a surface
opens empty), the wrong delivery leaf, a false "saved" claim, a finite choice
that re-runs, a connection loss that loops on resume, a view that is missing
what the state holds. Control-plane modes (owner steal, dropped pin, illegal
restart) are better caught by a control-plane adapter, where the ledger is
visible.

## Not in this pattern

No selector DSL or page objects; no screenshot diffing; no distribution
monitoring (that is a separate driver above the runner).
