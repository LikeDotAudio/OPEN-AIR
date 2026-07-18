# Changelog

## 2026-07-17 - v41 Plan Reconciliation + Phase 1 Scaffold

- **Plan reconciliation**: `Phase 1.md`, `Phase 2.md`, and
  `4_Contracts_Structural_Guidelines.md` reconciled — the inventory-backed
  guidelines win on schema content (`schemaVersion` field, `schemas/` dir,
  D1/H1 payload shapes, H1/D3 status enums, dual YAK contracts), Phase 1
  wins on deployment mechanics (golden vectors, ratchet baseline, committed
  codegen, hand-written `topics.rs`).
- **UI isolation ruling**: Phase 2 rewritten — the typed app is a new `ui/`
  package; `FrontEnd/` keeps data (`Gui_Frames/`, `api/`) and shrinking
  legacy source. Conversion = `git mv`, never copy; enforced by a CI
  collision check.
- **Archive trail ruling**: every migration move/retire/delete records a line
  in `Documents/Audits/Migration_Ledger.md` (append-only) and ships with a
  changelog entry; CI fails silent removals.
- **Phase 1 step 1 deployed**: pnpm workspace root, Node/Rust toolchain pins,
  `@openair/contracts` package skeleton, and `contracts-ci.yml` — the repo's
  first non-deploy CI.
- **Phase 1 step 2 deployed — the topic grammar**: `Topics` build/parse in
  TypeScript (`contracts/src/topics/`) and Rust (`contracts/rust/`), one
  declared topic-family table with retain classes, the full v40 legacy
  namespace map (`isLegacy` + alias table), and `topicMaker.jsx`'s panel-path
  semantics canonized as `Topics.gui.fromPanelPath`. Both implementations are
  pinned by one golden-vector file (`contracts/vectors/topics.json`) run by
  vitest AND cargo — 64 TS + 5 Rust suite assertions green. `topicUtils.js`
  (the older, disagreeing topic utility, zero callers) deleted.

## 2026-07-06 - YAK Orchestration, Live Command Routing, and UI Ergonomics

- **Intelligent Port Lifecycle Management**: Upgraded `openair.py` to aggressively hunt down and kill ghost processes on port 8000 using `fuser` and `lsof` during startup. This prevents the orchestrator from crashing due to "Address already in use" conflicts and ensures background VISA discovery tasks always complete.
- **YAK Model-Aware Routing**: Integrated nested hardware model routing inside the YAK Repository. The YAK agent now dynamically builds SCPI templates based on the specific hardware models identified by the VISA scanner.
- **Console Live-Monitoring**: Ripped out silent internal loggers from the Rust YAK agent (`mqtt.rs`, `rig.rs`, `set.rs`, `nab.rs`, `do_cmd.rs`) and replaced them with highly visible `println!` terminal output to mirror the MIDI agent's real-time MQTT debugging.
- **Frontend YAK Command Router**: Migrated `CommandRouter` to a bespoke React component (`CommandRouter.jsx`) featuring an auto-scrolling, syntax-highlighted terminal interface that subscribes natively to YAK's `monitor/in` and `monitor/out` MQTT topics for live traffic visualization.
- **Router UI Ergonomics (3235)**: Ran an automated script across `yak_router.json` to overhaul the tiny, default `OcaBooleanActuator` buttons. Actuators now feature massive 44x250 hitboxes and distinct, descriptive labels (e.g. `CLOSE Channels`, `SELECT Channel`) instead of the default generic "Toggle" text.
- **Root Directory Cleanup**: Purged multiple unused experimental `.py` and `.js` scratch files to keep the root directory pristine.

## 2026-07-05 - Fader scaling, Web Splash, and Mobile PWA Enhancements

- **FaderDial Overhaul**: Fixed an issue where horizontal fader elements overlapped their dial components due to unconstrained flex layout shrinking on smaller screens.
- **Dynamic Fader Sizing Fix**: Removed artificial constraints on the FaderDial knob size, while gracefully capping automatic font growth. Explicit JSON layout fonts (e.g. `"font": 10`) are now correctly honored.
- **Left Padding Optimization**: Corrected `frequency.json` configs where excessive `"padx": 20` shifted faders too far right, causing layout compression.
- **Desktop Splash Screen**: Implemented a native desktop boot splash screen (`splash.py`) featuring an animated GIF to mask the Rust kernel boot time.
- **Web PWA Splash Screen**: Synchronized the Web App experience by embedding the same animated splash GIF natively into `index.html`.
- **Background Lazy Loading**: Optimized the web splash sequence so the React `LoaderOrchestrator` mounts secretly in the background, aggressively downloading UI components while the 2.5s visual animation plays.
- **Mobile Cache Management**: Deployed a "FLUSH CACHE & RELOAD" button deep in the Settings menu (tap OPEN-AIR logo) to give standalone mobile/PWA users a native way to bypass Service Worker caches and hard-refresh their interface.
