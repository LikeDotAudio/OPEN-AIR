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
| 2026-07-17 | add | — | YAK agent LWT + retained AgentHeartbeat (`openair-yak/src/mqtt.rs`); orchestrator retained beat (`orchestrator/src/mqtt.rs`) | be5a352ab | Step 6: first Rust consumers of contract types. Verified live: yak beat observed on broker; SIGKILL → broker-delivered retained `offline`. Orchestrator has no LWT (ephemeral client — Phase 4 supervisor owns it). **Phase 1 complete** |
| 2026-07-18 | add | — | `ui/` package (Vite + strict TS, exact-pinned react 18.3.1/echarts 5.5.0/echarts-gl 2.0.9/mqtt 5.10.1, `@openair/contracts`), `scripts/gen-legacy.ts`, generated `src/legacy.ts` (142 imports in tag order, 4 dead tags skipped, 6 CDN dropped), `main.tsx` globals bridge | (this commit) | Phase 2 step 1: scaffold builds the FULL legacy graph (1,017 modules) on first try; typecheck green. NOT the runtime — FrontEnd/index.html untouched until the §4 overlap window |
| 2026-07-18 | add | — | `ui/src/boot.tsx` (inline text/babel boot block → TSX), `src/globals.d.ts` (182-global inventory, 3 hand-typed), `scripts/{gen-globals,check-collisions}.ts`, eslint floor, CI `ui` job; ui pinned TS 5.9 (ts-eslint can't parse TS 7) | (this commit) | Cutover prep. Headless Chrome smoke test: bundle BOOTS, same tab set as legacy A/B, cleaner console (legacy throws 3 dead-Sampler errors). Known deltas logged: OAPanels wasm ordering; widget-count timing — human overlap window confirms |
| 2026-07-18 | add | `7e061802e^` | `FrontEnd/Gui_Frames/4_Console/100_Sampler/Sampler.json`, `FrontEnd/libControl/special/{Sampler,SamplerDrumkit,SamplerSequencer,SamplerSoundBrowse}/*` | (this commit) | Sampler RESTORED — deleted by the user's `explosion` commit, not by migration; Anthony asked for it back. legacy.ts 142→146 imports (0 dead tags), globals 182→210 |
| 2026-07-18 | add | — | VISA rescan loop + `spawn_visa_write_daemon` (`orchestrator/main.rs`); `0_Scan/Scan.json` control panel (builder) | (this commit) | Discovered tab gains RESCAN: non-retained value-1 publish on `.../visa/Device/Rescan` re-runs the scan + builder; retained/zero payloads ignored; settle-republish deduped (drain). Live-tested: one press = one scan |
| 2026-07-17 | add | — | Phase 0 items 1–6: yak repo-path walker (`main.rs`), live `/api/tree` fetch with snapshot fallback (`index.html`), builder rewrite (`Deployment/build_discovered_gui.py`) + orchestrator spawn, stub `status=stub` (`mqtt.rs`), live-event `retain:false` + settle-retained (`MqttProvider.jsx`), `broker/mosquitto.conf` | (this commit) | Discovered pipeline fixed end-to-end: builder run live produced 11 devices across 6 strict-valid panels; ratchet 0 new. Deviations: snapshot kept as FTPS fallback (not deleted); `0_discovered/` gitignored + excluded from validate (generated data, deleted in Phase 4) |
