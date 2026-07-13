# Incident: pin without open (portable seed)

| Field | Value |
|-------|--------|
| **Slug** | `pin_without_open` |
| **Date** | 2026-07-13 |
| **Host** | path-faithful mini-app (public demo) · host dogfood Bot0 |
| **Conversation / ref** | Bot0 staging `conv_09449a0d` (Wealth Bottleneck V1) |
| **Conjecture-class?** | yes (delivery-leaf / open surface) |

## Symptom (what the user saw)

- Reply looked like an internal status line: “Pinned scenario **X**. Ask me to load…”
- **Broken underneath:** identity pin was correct (`scenario_id` set) but **no product
  surface** opened (empty content blocks / `blocks_resolve=false`). User asked for
  drill-down into a scenario and its runs; they got pin-status only.

Planted bug id (mini-app): `pin_without_open`.

## Layer trace (earliest wrong layer)

UI → stream → chat entry → **armed-list / inventory name resolve (exclusive owner won)** →
**delivery leaf stopped at identity pin** → never open tool / blocks.

Not a wrong exclusive owner (that would be steal). Not a dropped pin. **Hollow open.**

## Classification

- [x] Looks fine enough / plausible while state law for *delivery* was wrong
- [x] Expressible as pin present **and** open surface (`blocks_resolve` / host blocks)
- [x] Cognition can be pinned for CI (`inventory_open` / `scenario_open` read_kind)
- [x] Ledger pin law is fine; host delivery leaf incomplete

## Expected law (host vocabulary)

| Field | Expected | Observed (bug) |
|-------|----------|----------------|
| pin key → value | e.g. `scenario_id` → `scen_1` | pin may be correct |
| open surface | `blocks_resolve=true` (or host content blocks non-empty) | `blocks_resolve=false` / empty blocks |
| exclusive_owner | free / inventory leaf (demo: `front_door`) | same — **not** the failure |
| product copy | scenario detail / runs / marketplace card | pin-status jargon only |

**Law in one line:** Identity pin is **routing authority**, not the product answer.
Delivery leaf must **open**, clarify, or refuse — never pin-status-only sole reply.

## Twists (scenario steps)

1. User has an armed inventory list (scenarios, marketplace, …).
2. User names a row with drill-down intent (“more about X and its runs”).
3. Host resolves id and writes pin.
4. Host must open surface for that stream; must not stop at “Pinned…”.

## Artifacts

- [x] `script.json` (required) — mini-app open leaf
- [x] Red: `MiniChatApp(bug="pin_without_open")`
- [x] Green: healthy mini-app
- [x] `CATALOG.md` row
- Host path seal: keep in the host application test suite (not this package)

## Fix notes (portable)

- Unique inventory hit → open stream tool + pin in same turn
- Source ratchet: ban pin-status-only sole answers in host short-circuits
- Distinct from **context-pin hijack** (wrong activity) and **owner steal**

## Notes

Demo uses `scenario_id` + `blocks_resolve` as the portable observation of “open leaf.”
Hosts map that to real cards/tables (e.g. scenario detail + runs). Product tools and
tenant data stay in the host repo — not in this public seed.
