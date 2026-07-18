# Migration Ledger — v40 → v41

Append-only archive trail for the TypeScript/contracts migration. Every file
the migration **moves**, **converts**, **retires**, or **deletes** gets one
line here, in the same commit that does it. CI (contracts-ci) checks this
trail: a module removed or relocated without a ledger line fails the build;
a module present in both `FrontEnd/` and `ui/src` (copy instead of move)
fails the build. Git history is the archive; this file is the marker.

Actions: `add` | `move` | `convert` (jsx→tsx, implies move to `ui/src`) |
`retire` (kept on disk, no longer loaded) | `delete`.
Commit column: write `(this commit)` when the row lands with the change
itself; hashes may be back-filled later for cross-reference.

| Date | Action | Old path | New path | Commit | Note |
|---|---|---|---|---|---|
| 2026-07-17 | add | — | `Documents/Audits/Migration_Ledger.md` | 72d7e531d | Ledger established (ruling: archive markers + checks at every step) |
| 2026-07-17 | add | — | `pnpm-workspace.yaml`, `package.json`, `.nvmrc`, `rust-toolchain.toml` | fe130b3b0 | Phase 1 step 1: workspace root + toolchain pins |
| 2026-07-17 | add | — | `contracts/` | fe130b3b0 | Phase 1 step 1: @openair/contracts package skeleton |
| 2026-07-17 | add | — | `.github/workflows/contracts-ci.yml` | fe130b3b0 | Phase 1 step 1: first non-deploy CI |
| 2026-07-17 | add | — | `contracts/src/topics/`, `contracts/vectors/topics.json`, `contracts/rust/` | (this commit) | Phase 1 step 2: topic grammar TS+Rust, pinned by golden vectors |
| 2026-07-17 | delete | `FrontEnd/comMQTT/topicUtils.js` | — | (this commit) | Older of the two disagreeing topic utilities; zero callers; `topicMaker.jsx` semantics canonized in contracts instead |
| 2026-07-17 | retire | `FrontEnd/index.html` script tag `comMQTT/topicUtils.js?v=1` | — | 7f9df4b78 | Tag removed with the file |
| 2026-07-17 | move | `Documents/Audits/{3_TypeScript_Migration_Plan, Phase 1, Phase 2, 4_Contracts_Structural_Guidelines, Migration_Ledger}.md` | `Documents/Strategies/` | 6a14a8346 | Ruling: forward-looking strategy docs live in Strategies; point-in-time audits stay in Audits; cross-links rewritten |
| 2026-07-17 | add | — | `Documents/Strategies/Phase 1 Step 3.md` | f88adbaf7 | Deployment strategy for rollout step 3 (heartbeat/DeviceRecord/codegen/LWT) — first step touching a running component, planned before code per ruling |
| 2026-07-17 | add | — | `contracts/src/{heartbeat,device-record,identity,time}.ts`, payload + identity vectors | (this commit) | Step 3a/3c: H1/D1 schemas incl. legacy-v0 shapes named; D2 deviceId + ISO time helpers, vector-pinned both languages |
| 2026-07-17 | add | — | `contracts/scripts/gen.ts`, `contracts/schemas/`, `contracts/rust/src/gen/` | (this commit) | Step 3b: codegen ON (zod→JSON-Schema→cargo-typify 0.7.0); gen:check real in CI. Rule amended: `regress` allowed (typify validation runtime, no I/O) |
| 2026-07-17 | add | — | `contracts/rust/src/{heartbeat,device_record,identity,time}.rs` | (this commit) | Step 3b/3e: wrappers over gen types + `heartbeat_lwt` + lossless `map_v40_visa_record` (replay-proven) |
| 2026-07-17 | add | — | `FrontEnd/comMQTT/MqttProvider.jsx` LWT + v41 dual heartbeat | 7838af4ac | Step 3d: additive only; will targets `OpenAir/System/Agents/web-{guid}` per H2; legacy Failover beat unchanged; LWT kill-test verified against live broker (browser kill-tab spot-check recommended) |
| 2026-07-17 | add | — | `contracts/src/layout/{node,widget-types,yak-binding,folder-grammar}.ts`, `contracts/src/yak/verbs.ts` | (this commit) | Step 4: layout contract per L1–L6 (two-mode validation, type classification seeded from live dispatch code), yak binding (L3) + runtime wire message (Y7). Rust codegen for layout deferred to Phase 3 (its consumer) |
| 2026-07-17 | add | — | `contracts/cli/validate.ts` (`pnpm validate`) | (this commit) | Step 4: the walk-and-report CLI — layout legacy mode, folder grammar, YAK tree rules (md5 dups, legacy files, duplicate models), config.ini topic lint |
| 2026-07-17 | add | — | `Documents/Strategies/Validations/{contracts-debt-inventory.md, 2026-07-17_day-one-report.json}` | 18ce7901b | Step 4: first honest drift count — 169 errors / 2,093 deprecations. Step 5 ratchet baselines this |
| 2026-07-17 | add | — | `contracts/validate.baseline.json` + ratchet mode in `cli/validate.ts` + CI validate step | babf8f355 | Step 5: ratchet armed — CI fails only on debt not in the baseline; kill-tested (probe file → exit 1, removed → exit 0). Baseline may only shrink |
| 2026-07-17 | add | — | `openair-contracts` path dep in `openair-yak` + `open-air-orchestrator` Cargo.toml | (this commit) | Step 6: the dependency direction proven in BOTH workspaces |
| 2026-07-17 | add | — | YAK agent LWT + retained AgentHeartbeat (`openair-yak/src/mqtt.rs`); orchestrator retained beat (`orchestrator/src/mqtt.rs`) | (this commit) | Step 6: first Rust consumers of contract types. Verified live: yak beat observed on broker; SIGKILL → broker-delivered retained `offline`. Orchestrator has no LWT (ephemeral client — Phase 4 supervisor owns it). **Phase 1 complete** |
