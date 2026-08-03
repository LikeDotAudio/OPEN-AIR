# Strategies — historical planning records

> ## ⚠️ DEPRECATED as documentation
>
> **These are plans, not descriptions.** The parts that shipped are now
> *features*, documented where the code lives:
>
> | For | Read |
> |---|---|
> | The contract layer, topic grammar, schemas, codegen, validate/ratchet | [`contracts/README.md`](../../contracts/README.md) |
> | Protocol agents, discovery, heartbeats, rescan | [`BackEnd/ComProtocols/README.md`](../../BackEnd/ComProtocols/README.md) |
> | The typed frontend and migration mechanics | [`ui/README.md`](../../ui/README.md) |
> | The project as a whole | [`README.md`](../../README.md) |
>
> Nothing here should be used to learn how OPEN-AIR works today. Keep them for
> *why* decisions were made and what is still planned.

These documents were written 2026-07-17/18 to plan the v40 → v41 rework. They
are preserved because the reasoning behind a decision outlives the decision,
and because the unshipped phases are still the roadmap.

## What shipped (now features — see the READMEs above)

| Document | Status |
|---|---|
| `3_TypeScript_Migration_Plan.md` | Phases 0–1 **shipped**; Phase 2 partially; Phases 3–5 pending |
| `4_Contracts_Structural_Guidelines.md` | **Shipped.** The rules now live as review law in `contracts/README.md` |
| `Phase 1.md` | **Shipped** — all six rollout steps, DoD closed out in the document |
| `Phase 1 Step 3.md` | **Shipped** — payload schemas, codegen turn-on, browser LWT |
| `Phase 2 Step 1.md` | **Shipped** — the `ui/` package builds the whole app; cutover pending |
| `Phase 2.md` | **Partially shipped** — scaffold and ratchets done; conversions and cutover pending |

## Still the roadmap

- **Phase 3 — YAK 2.** Class capability files + model dialect bindings,
  `inherits:`, reply parsers, one Rust translation core built natively *and*
  to WASM for in-browser command preview and dry-runs.
- **Phase 4 — Device Registry & supervision.** One `DeviceRecord` document per
  device with TTL aging, a Discovered tab that is a live widget rather than a
  generated panel, agent supervision with restart, native Rust VISA, and
  structured logging on the bus.
- **Phase 5 — Live tree & polish.** fs-watch → retained tree topic so folder
  changes redraw every browser instantly.

## Living records (not deprecated)

- [`Migration_Ledger.md`](Migration_Ledger.md) — the append-only archive trail.
  Every file moved, converted, retired, or deleted gets a line, in the commit
  that does it. **Still active** and still required for every change.
- [`Validations/`](Validations/) — the `openair-validate` day-one drift
  inventory (169 errors / 2,093 deprecations) that the CI ratchet baselines
  against. **Still the reference** for what debt remains.
