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
| 2026-07-17 | retire | `FrontEnd/index.html` script tag `comMQTT/topicUtils.js?v=1` | — | (this commit) | Tag removed with the file |
