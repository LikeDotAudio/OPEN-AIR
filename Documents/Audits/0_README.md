# OPEN-AIR Design Audit — 2026-07-17

A high-level design audit of OPEN-AIR at v40: the good, the bad, and the ugly —
measured against the project's actual goal, with a concrete plan for the
TypeScript + WASM generation of the platform.

## Contents

| File | What it covers |
|---|---|
| [1_Design_Audit.md](1_Design_Audit.md) | The extracted mission statement, the scorecard, and the good/bad/ugly analysis of every subsystem — including the Discovered-tab case study |
| [2_Architecture_Diagrams.md](2_Architecture_Diagrams.md) | Diagrams: data transfer (current vs. target), YAK translation, file/folder structure, folders-make-tabs, the WYSIWYG loop, and the library map |
| [3_TypeScript_Migration_Plan.md](../Strategies/3_TypeScript_Migration_Plan.md) | The phased plan: contracts-first TypeScript migration, YAK 2 capability model, WASM strategy, supervision, and live discovery |
| [Phase 1.md](../Strategies/Phase%201.md) | Deep dive: deployment strategy for the `contracts/` package — scaffolding, zod→JSON-Schema→Rust codegen, golden vectors, validate CLI with CI ratchet, rollout order |
| [Phase 2.md](../Strategies/Phase%202.md) | Deep dive: frontend TypeScript migration — Vite/pnpm scaffolding, the `window.*` bridge mechanic, typed widget registry, cutover/deploy/PWA strategy |
| [4_Contracts_Structural_Guidelines.md](../Strategies/4_Contracts_Structural_Guidelines.md) | Structural guidelines for the Phase 1 `contracts/` package, grounded in a full code-level inventory of every cross-boundary shape (topics, device records, heartbeats, layout JSON, YAK tree) |
| [contracts-debt-inventory.md](../Strategies/Validations/contracts-debt-inventory.md) | The day-one `openair-validate` drift count (169 errors / 2,093 deprecations, 2026-07-17) — the ratchet baseline; the number only goes down |

## The one-paragraph verdict

OPEN-AIR's architecture ideas are genuinely good — a filesystem-driven UI, an
MQTT spine, a verb-based instrument grammar, Rust protocol agents. What is
hurting it is not any single idea but the **absence of contracts between the
ideas**: every boundary (topics, YAK commands, widget types, layout JSON,
config files) is an unchecked string, and nearly every subsystem has quietly
grown **two sources of truth**. The Discovered-tab failure is not a bug; it is
the architecture demonstrating its central weakness in one pipeline. The
TypeScript migration is the right move precisely because its main deliverable
is not "the frontend in a new language" — it is **a single, typed contract
layer shared by the browser, the Rust agents, and the YAK definition plane**.
