# `@openair/contracts` — the contract layer

**One definition of every shape that crosses a process boundary**, shared by
the browser, the Rust agents, and the tooling.

TypeScript-first (zod) → JSON Schema → Rust types by codegen. Behavior that
codegen cannot express (the topic grammar, device-ID derivation) is written
twice and kept honest by shared golden vectors.

```
src/**/*.ts ──z.toJSONSchema──► schemas/*.schema.json ──cargo-typify──► rust/src/gen/*.rs
     │                                                                        │
     └── z.infer<> types + runtime validation for the browser & CLI           └── serde types for agents
```

---

## What lives here

| Module | Owns |
|---|---|
| `src/topics/` | The topic grammar: `grammar.ts` (segment rules), `tree.ts` (every family as data, with its retain class), `builders.ts` (typed build + total-function parse), `gui-path.ts` (panel path → GUI topic), `legacy.ts` (the v40 namespace map) |
| `src/device-record.ts` | `DeviceRecord` — the canonical discovered-device document, plus the v40 VISA shape and a lossless mapping between them |
| `src/heartbeat.ts` | `AgentHeartbeat` + `heartbeatLwt()` — liveness for agents and browser sessions |
| `src/identity.ts` | `deviceIdFor()` — the device identity rule (serial → address → FNV-1a hash) |
| `src/time.ts` | Unix-seconds → ISO-8601 UTC at the boundary |
| `src/layout/` | The panel JSON: `node.ts` (two-mode validation), `widget-types.ts` (what actually renders), `yak-binding.ts` (the `yak_handler` block), `folder-grammar.ts` (`N_` order, `left_50` splits) |
| `src/yak/verbs.ts` | The runtime `yak_handler` wire message the YAK agent receives |
| `vectors/` | Language-neutral golden vectors — consumed by **both** vitest and `cargo test` |
| `cli/validate.ts` | `openair-validate`: walks the tree, reports drift, enforces the ratchet |
| `schemas/`, `rust/src/gen/` | **Generated. Never hand-edited.** Committed so `cargo build` never needs Node |

## The topic tree

```
OpenAir/
├── Discovery/{protocol}/{deviceId}        retained DeviceRecord      (Phase 4 publisher)
├── Gui/{...panelPath}/{field}             live control values
├── Yak/
│   ├── cmd/{verb}/{class}/{model}         command plane              (Phase 3)
│   ├── state/{class}/{model}/{capability} parsed replies             (Phase 3)
│   └── monitor/{in|out}                   command monitor
└── System/
    ├── Agents/{agent}                     retained AgentHeartbeat
    ├── Config/{agent}                     retained config
    └── Log/{source}/{level}               structured log events      (Phase 4)
```

Every *current* v40 namespace is classified by name — `Topics.parse()` returns
`{kind: 'legacy', family: …}` with the v41 alias, so bridges and the validate
CLI can name old traffic instead of failing on it, and the eventual retirement
is a grep (`Topics.isLegacy`).

```ts
import { Topics } from '@openair/contracts'

Topics.discovery({ protocol: 'visa', deviceId: 'visa:MY12345678' })
Topics.agents.topic('yak')                       // OpenAir/System/Agents/yak
Topics.gui.fromPanelPath('/Window_1/left_50/0_Spectrum/10_YAK/1_N9340B/f.json')
                                                 // OpenAir/Gui/Spectrum/YAK/N9340B

const t = Topics.parse(raw)   // discriminated union; never guesses
```

---

## Schema design law

These rules are **review law**. They are what keep the package usable against
a live broker rather than merely correct on paper.

### Retained messages are a database you don't get to migrate

The broker holds payloads written by every version that ever ran.

1. **Every document carries `schemaVersion`** (integer literal). Parsers
   dispatch on it. Version-less input is v0 — the wild west — and where a real
   v0 shape exists it is schema'd *by name* (`LegacyFailoverHeartbeatV0`,
   `LegacyVisaRecordV0`) so validators can say what they found.
2. **Tolerant reader, strict writer.** Readers ignore unknown fields and
   default missing optionals; writers always emit the full current shape and
   never round-trip unknown fields back onto the bus.
3. **Within a major version, evolution is additive-optional only.** Renaming
   or retyping a field is a new major version and ships with a bus-migration
   step.

### Conventions

- **Timestamps are ISO-8601 UTC strings.** The bus is debugged with
  `mosquitto_sub` and human eyes; `1752786000` is hostile. Unix seconds
  convert at the contract boundary (`fromUnixSeconds`).
- **IDs are derived, never positional.** `deviceId = {protocol}:{stableKey}` —
  serial when the instrument reports one, else its protocol-native address,
  else a content hash. Scan-order identity (`Dev0`, `Dev1`) is banned: two
  agents computing IDs differently recreates the duplicate-instrument problem
  on the bus, so the derivation is a contract and is vector-pinned.
- **No stringly enums.** Device status, agent status, verbs, converters,
  protocol names, widget types — all closed. Unknown values fail loudly.
- **Liveness is computed, never stored.** `lastSeen` + documented TTL
  semantics; booleans like `connected: 1` go stale themselves and are banned.
- **Retain class belongs to the topic family, not the call-site.**
  `tree.ts` marks each family `retained-state` or `live-event`; control values
  are live events (this is what ended 45 Hz retained fader spam).
- **One shape, one file, one export.** No type that duplicates a contracts
  shape is declared in `ui/` or an agent — Rust gets its copy by codegen only.
- `z.any()` / `z.unknown()` require a `// WHY:` comment and show up in review.

### Dependency discipline

- `@openair/contracts` depends on **zod** and nothing else.
- `openair-contracts` (Rust) depends on **serde, serde_json, regress** and
  nothing else — no MQTT client, no async runtime. Types and topic strings
  only; client libraries belong in the agents.

---

## Codegen & verification

```bash
pnpm gen           # schemas/ + rust/src/gen/ (requires cargo-typify 0.7.0)
pnpm gen:check     # regenerate to a temp dir and diff — the CI freshness gate
pnpm test          # vitest, incl. every golden vector
cargo test --manifest-path rust/Cargo.toml   # the SAME vectors, Rust side
```

Generated artifacts are **committed**: a repo where `cargo build` only works
after running a Node toolchain is a repo where the Rust half stops building
the day Node breaks. CI enforces freshness instead.

Known limit, stated up front: zod → JSON Schema flattens some refinements, and
string `format`s are stripped from the typify input so Rust sees
pattern-validated strings instead of chrono types. Anything load-bearing for
Rust gets a **golden vector**, not trust in the translation.

---

## `openair-validate` — drift as data

```bash
pnpm validate                       # ratchet mode: fails only on NEW debt
pnpm validate -- --report json      # the full machine-readable inventory
pnpm validate -- --strict           # deprecations become errors (editor gate)
pnpm validate -- --update-baseline  # after fixing files; review the diff
```

It walks `FrontEnd/Gui_Frames/**` (layout schema in legacy mode), the YAK tree
(duplicate models, byte-identical definitions, `_Legacy_Commands/`,
`temp_norm_*`), the folder grammar (`N_` prefix collisions, unparseable
names), and every BackEnd `config.ini` (`topic*` values against the grammar).

**The ratchet** is what made day one survivable: the first run's
169 errors / 2,093 deprecations were written to `validate.baseline.json` and
committed. CI fails only on findings *not* in the baseline, so the inventory
can only shrink and new debt cannot enter. The readable version of that
inventory is
[`Documents/Strategies/Validations/contracts-debt-inventory.md`](../Documents/Strategies/Validations/contracts-debt-inventory.md).

---

## Adding a contract

1. Write the zod schema in `src/` — one shape, one file, `schemaVersion`
   literal, closed enums.
2. Add golden vectors under `vectors/payloads/{Schema}/{valid,invalid}/` —
   including a real capture off the broker if the shape already exists in the
   wild, and a `legacy-v0/` sample if it does.
3. Export it from `src/index.ts` (the only public surface).
4. Register it in `scripts/gen.ts` if Rust needs it; run `pnpm gen`.
5. Land it **with its first consumer** in the same change. A contract nobody
   consumes is documentation that lies.
