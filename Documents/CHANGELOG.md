# Changelog

## 2026-07-18 - Deploy on Every Push · Repository Button · Install Path

- **Every push publishes.** The production deploy workflow only fired for
  `main`, so anything pushed on another branch silently never reached the
  host — the "it doesn't publish every time" symptom. It now triggers on
  every branch except the sandbox ones (which have their own workflow and
  host), queues rather than drops concurrent pushes, writes a **deploy
  summary** to the run page so a publish is visible rather than assumed, and
  the previously-dead `full_sync` input is wired to a real full resync for
  when the server's incremental sync state drifts.
- **Deploy secret-hygiene fix.** `FTP-Deploy-Action`'s default excludes do
  **not** cover `.env`, while the upload root is `./FrontEnd/` — which is
  exactly where the local FTP credentials live. Both workflows now exclude
  `.env*`, logs, and editor junk explicitly. (CI was never exposed —
  `.env` is gitignored so it is absent from the runner's checkout — but a
  local or misconfigured run would have published it.)
- **Repository button** in the top-right of the header, linking to the source
  on GitHub, with the GitHub mark and the project's orange hover treatment.
  The README's clone URL pointed at `APKaudio/OPEN-AIR` while `origin` is
  `LikeDotAudio/OPEN-AIR`; both now agree with the remote.
- **`requirements.txt` is now real.** It listed `paho-mqtt` alone while the
  orchestrator shells out to `python3 -c "import pyvisa"` using the
  **pure-Python backend** (`ResourceManager('@py')`) — so a clean install
  died at the first instrument probe. Now pins `pyvisa`, `pyvisa-py`, and
  `paho-mqtt` with the reason for each, and documents the optional
  pyvisa-py transports. Verified against installed versions.
- **Discovered-GUI builder runs warning-free on paho 1.x and 2.x**
  (`CallbackAPIVersion.VERSION2` when available; one callback signature
  serves both APIs).

### Decision record: the Sampler is removed from OPEN-AIR *(supersedes the entry below)*

**Final — 2026-07-18.** The Sampler has been **moved out of the project
entirely** and removed from this repository, together with the libraries that
powered it. This executes the 2026-07-17 executive-review mandate and closes
the governance finding that a board order had been reversed without a written
decision.

Removed:

| Path | What it was |
|---|---|
| `Gui_Frames/4_Console/100_Sampler/` | the `Console → Sampler` panel |
| `libControl/special/Sampler/` | sampler widget |
| `libControl/special/SamplerDrumkit/` | audio runtime — owned `oaAudioCtx`, `oaDecodeAudio`, `oaEncodeWav`, `OA_DRUM_*` |
| `libControl/special/SamplerSequencer/` | step sequencer |
| `libControl/special/SamplerSoundBrowse/` | sound browser |
| `libControl/special/AudioEditor/` | waveform editor — **sampler-only**, despite the neutral name |
| `libControl/special/PadBrowse/` | pad browser — **sampler-only**, despite the neutral name |

`AudioEditor` and `PadBrowse` carry no "Sampler" prefix but depend on the audio
runtime defined in `SamplerDrumkit.js` and appear in no panel outside
`100_Sampler`. They are the "libraries that power it" and would have been dead
code — or worse, broken references — had only the four prefixed widgets gone.
Verified before removal: no surviving widget references any removed one.

Also updated: 6 `<script>` tags dropped from `index.html`; the `Sampler` /
`AudioEditor` / `Sequencer` entries removed from `WidgetFactory.jsx`'s registry;
`ui/src/legacy.ts` regenerated (146 → 140 imports) and `ui/src/globals.d.ts`
regenerated (210 → 178 globals — 32 audio globals retired).

**No debt-reduction credit is claimed for this.** The Sampler contributed
**zero** findings to `validate.baseline.json` (verified: errors 169 and
deprecations 2,093 are unchanged, and no baselined key referenced a removed
path). This is a **scope change, not debt paydown** — the distinction the
executive review demanded, since a shrinking baseline achieved by deleting
files is not progress. Note for the record that the 236 findings under
`Gui_Frames/5_Samples/` belong to the widget **demo panels**, which are a
different thing from the Sampler and remain in the tree.

<details>
<summary>Superseded earlier entry, kept for the record</summary>

> **Decision record: the Sampler is product scope** *(2026-07-18, reversed the
> same day by the entry above)*
>
> The 2026-07-17 executive review ordered the Sampler quarantined to its own
> repository; the follow-up review recorded that order as **reversed**. Making
> the decision explicit, as that review required:
>
> **The Sampler stays in OPEN-AIR as product scope.** `Console → Sampler` and
> its four widget files (`Sampler`, `SamplerDrumkit`, `SamplerSequencer`,
> `SamplerSoundBrowse`) are a console feature built on the same widget library,
> panel schema, and MQTT layer as every other panel — not an unrelated side
> project. It ships, it is documented here, and it is subject to the same
> contract validation as the rest of the tree. Superseding the audit's
> recommendation, on the record, rather than silently.

</details>

## 2026-07-18 - Documentation: plans become features

- **The README is a real project README again**: what OPEN-AIR is, the four
  pillars as they actually work, an architecture sketch, and two new
  first-class sections — **the contract layer** and **protocol management &
  discovery** — plus repo layout, quick start, workspace commands, and an
  honest status table (what is complete vs. what is still roadmap).
- **Section READMEs added**, so documentation lives with the code:
  [`contracts/README.md`](contracts/README.md) (schemas, topic tree, codegen,
  validate/ratchet, and the schema design law that used to live in the
  planning docs), [`BackEnd/ComProtocols/README.md`](BackEnd/ComProtocols/README.md)
  (the agent fleet with real/stub status, heartbeats + Last Will, discovery
  topics, rescan semantics, how to add a protocol), and
  [`ui/README.md`](ui/README.md) (the typed frontend and its ratchets).
- **`Documents/Strategies/` deprecated as documentation**: every plan carries
  a HISTORICAL banner pointing at the feature docs. `Migration_Ledger.md` and
  `Validations/` remain **active records**, not history.
- **`Documents/Audits/` marked as a 2026-07-17 snapshot** and left as written,
  with a per-finding **resolution table**: what is fixed, what is detected but
  not repaired, and what remains roadmap — including the Discovered-tab case
  study, now fully resolved plus two further bugs found during the repair.

## 2026-07-18 - Sampler Restored + Discovered-Tab Rescan + Tab-Based Editor Entry

- **Drag jiggle fixed — mouse capture wins**: while a control is being
  adjusted locally, inbound MQTT state (including the browser's own stale
  broker echoes, which arrive a few ms behind the hand) no longer yanks it
  backwards. Inbound applies again once the hand rests (600 ms grace,
  `window.OA_CAPTURE_GRACE_MS` to tune); the settle-retained publish means
  the bus and the control agree at rest. Per-widget, so `shared_topic`
  twins on the same page still mirror a drag live.
- **Discovered tab uses the library table component**: the label-stack
  display is gone — every category panel is now an `OcaTable`
  (`libControl/text/OcaTable`: sticky header, zebra rows, row-count footer,
  its own scroll region), with per-family column ordering and a readable
  `last_seen` column. Bonus repair: `OcaTable` had been silently broken on
  the WidgetFactory registry path (it received `node` but destructured
  `config` — Sample.json's own "Discovered Devices" example rendered
  empty); it now accepts either, fixing every registry-dispatched table
  in the app.
- **DNS-SD discovery is real — the `dnssd` crate is no longer a stub**: it
  now browses `_services._dns-sd._udp.local.` (the meta-query enumerating
  EVERY advertised service type), then browses each type via `mdns-sd` and
  publishes retained attribute topics under
  `OpenAir/System/Protocols/dnssd/Device/{type}/{instance}/`. Vanished
  services clear their retained topics. The orchestrator spawns it as a
  continuous browse thread; its protocol status honestly reports `online`
  (left the stub list). The Discovered tab gains a **dnssd** category —
  first live sweep found **42 services** (Rigol LAN, RTSP/AES67-style audio
  streams, printers, Chromecasts...). RESCAN re-sweeps it like everything
  else.

- **WYSIWYG entry moved to the tabs, globally**: right-click any tab —
  folder tab or top-level window tab — to open the editor on that folder's
  first panel file (depth-first through subfolders). The canvas right-click
  entry is retired; panels keep the browser's native context menu.

- **Sampler is back**: `Console/Sampler` (panel + the four widget files) was
  deleted by the `explosion` commit — before any migration work — and has
  been restored from that commit's parent. The live tree picked it up with
  no regeneration (the Phase 0 live-tree fix working as designed);
  `legacy.ts` regenerated with zero dead tags remaining.
- **The Discovered tab can now rescan on demand**: a new `0_Scan` control
  panel (always written by the builder, sorts first in the tab) carries a
  RESCAN DEVICES actuator publishing to
  `OpenAir/System/Protocols/visa/Device/Rescan`. The orchestrator's VISA
  agent is now a scan **loop**: trigger → full re-probe → retained topics
  refreshed → Discovered panels regenerated → idle. Safety semantics:
  retained and zero-value payloads never trigger (no scan storms on page
  load or broker replay), and the browser's settle-republish of the same
  press is deduped — live-tested: one press = exactly one scan. Reload the
  page after a rescan to see updated panels (live tree redraw is Phase 5).
- **"Unknown Instrument" fixed — the knowledge base was never found**: the
  VISA lookup read `assets/visa_devices.json` relative to the process cwd
  only, so run from the repo root it matched nothing and all 17 instruments
  (33210A/33220A/34401A×7/54641D×2/DS1104Z×2/N9340B...) fell to "Not in
  Knowledge Base". Now: walk-up path resolution + the KB compiled into the
  binary as guaranteed fallback (disk copy still wins, so the inventory
  stays editable). Companion fixes: each rescan clears the previous scan's
  retained topics (no ghosts when devices re-categorize or vanish), the
  builder prunes stale category folders, and the 154 pre-fix ghost topics
  were swept. Discovered tab now reads DMM(6)/Generator(2)/Oscilloscope(4)/
  Spectrum(1)/midi(4). Note: N9342CN is genuinely absent from the KB.
- **Discovered panels scroll**: generated panels now declare
  `behavior.overflow_ns: "auto"` — OcaBin clips by default, and a scan can
  find more devices than fit one screen (14 Unknown_Instruments did).

## 2026-07-18 - Local Stack Smoke Test + the MQTT Flush Bug

- **Full local stack verified end-to-end**: broker + orchestrator (live
  `/api/tree`) + `ui/` dev server. Headless boot against the LIVE tree
  renders the real tab set (including `Instruments`, which the stale
  snapshot never showed).
- **Orchestrator flush bug found and fixed by the smoke test**: the boot
  MQTT client's drain thread processed only 10 connection events, so most
  of the 33 queued retained publishes (protocol configs/statuses,
  heartbeat) never reached the broker — only 2 of 16 statuses landed.
  Now: drain thread runs until `disconnect()` completes (deadline-bounded);
  all 16 land, stub statuses verified on the wire
  (`nmos/rest/sap/mdns/dnssd/websocket = stub`).
- **CI rust job fixed for bare runners**: `libasound2-dev` installed
  (openair-midi → alsa-sys) + rust-cache for the three cargo trees — the
  first push's failure was exactly this.
- Vite dev proxies `/assets` alongside `/api` to the orchestrator.

## 2026-07-18 - Phase 2 Step 1: the `ui/` Package Exists and Builds

- **The isolated typed frontend scaffold is real**: `ui/` joins the pnpm
  workspace with exact-pinned deps (react 18.3.1 — the version the CDN tag
  resolves today — echarts 5.5.0, echarts-gl 2.0.9, mqtt 5.10.1, zod,
  `@openair/contracts`), Vite (`base './'`, `/api` proxy, cross-boundary
  `fs.allow`), and the per-file one-way strict tsconfig.
- **The 152-script-tag load order is captured as code**:
  `scripts/gen-legacy.ts` deterministically regenerates `src/legacy.ts`
  from `FrontEnd/index.html` — 142 side-effect imports in exact tag order,
  4 dead tags (deleted Sampler files) skipped by name, 6 CDN tags dropped
  in favor of npm. `main.tsx` recreates the CDN-globals world
  (`window.React/ReactDOM/echarts/mqtt`) from the npm singletons before the
  legacy graph loads.
- **`vite build` bundles the entire legacy app on the first attempt** —
  1,017 modules, zero files needing the comment-out escape hatch;
  typecheck green. Not the runtime yet: `FrontEnd/index.html` stays the
  only served app until the Phase 2 §4 overlap window opens deliberately.
- Checklist audit: `Documents/Strategies/Phase 2 Step 1.md`.
- **Cutover prep (same day)**: the inline `text/babel` boot block became
  `ui/src/boot.tsx` (gen-legacy can't capture inline scripts — the bundle
  now actually boots); `globals.d.ts` inventories the **182** window
  globals (3 hand-typed, regen-safe); eslint + CI ratchets armed (no new
  `window.*` outside named bridges, one-module-one-tree collision check,
  generated-file freshness). **Headless Chrome smoke test: the bundle
  boots and renders the same tab set as the legacy page**, with a cleaner
  console (legacy throws 3 dead-Sampler load errors; the bundle skips
  those tags by name). Two deltas logged for the human overlap window:
  OAPanels wasm script-pair ordering, and a widget-count difference under
  virtual time.

## 2026-07-18 - Phase 0: Stop the Bleeding (all six items)

- **The Discovered tab works again — every break in the audit's four-stage
  pipeline fixed**: the builder (`Deployment/build_discovered_gui.py`)
  subscribes to the topics the agents actually publish
  (`OpenAir/System/Protocols/{visa,midi}/Device/#`), emits **strict-valid
  v41 panels** (verified against the layout contract) instead of the dead
  `_GuiValue`+`subscribe` schema, and is spawned by the orchestrator after
  each VISA scan. First live run produced 11 devices across 6 category
  panels from the broker's retained state. `0_discovered/` is gitignored
  and excluded from validate — discovery is data, not authored UI
  (Phase 4 replaces this pipeline with the Device Registry).
- **Live tree**: `index.html` fetches the orchestrator's `GET /api/tree`
  first — new folders/panels appear without regenerating anything; the
  static `tree.json` snapshot survives only as the FTPS-host fallback.
- **YAK repo path**: the agent walks up from cwd to find
  `FrontEnd/Gui_Frames/5_Protocols/10_Yak` (env `YAK_REPO_PATH` still
  wins) — no more zero-definitions when launched from the wrong directory.
- **Stubs stop lying**: nmos/rest/sap/mdns/dnssd/websocket now publish
  `status = stub`, not `online`.
- **Retained-fader flood fixed**: high-rate control values publish
  `retain:false`; one settle-delayed retained publish (400 ms after rest)
  preserves late-joiner state sync. Contracts T5 semantics, live today.
- **`broker/mosquitto.conf` checked in** (1883 + websockets 9001,
  persistence on) — the broker stops being an unmanaged assumption.

## 2026-07-17 - v41 Contracts Package: Plan Reconciliation + Phase 1 Steps 1-4

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
  in `Documents/Strategies/Migration_Ledger.md` (append-only) and ships with
  a changelog entry; CI fails silent removals.
- **Strategy-before-code ruling**: any step that touches a running component
  gets its own deployment-strategy audit first — first applied as
  `Documents/Strategies/Phase 1 Step 3.md`.
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
- **Docs reorganized**: forward-looking strategy documents (migration plan,
  Phase 1/2 deep dives, contracts guidelines, migration ledger) moved from
  `Documents/Audits/` to `Documents/Strategies/`; the point-in-time audits
  (design audit, diagrams, executive review) stay in Audits. Cross-links
  rewritten on both sides. Validation output lives in
  `Documents/Strategies/Validations/`.
- **Phase 1 step 3 deployed — payload contracts + codegen + the ghost-tab
  fix**: `AgentHeartbeat` (H1) and `DeviceRecord` (D1) zod schemas with
  legacy-v0 shapes schema'd by name; the zod→JSON-Schema→cargo-typify (0.7.0)
  pipeline turned ON with committed output and a real `gen:check` CI gate;
  D2 `deviceIdFor` (FNV-1a 64) + ISO time helpers vector-pinned in TS and
  Rust; `mapV40VisaRecord` replay-proven lossless in both languages. The
  browser now registers a real MQTT **Last Will** on
  `OpenAir/System/Agents/web-{guid}` and dual-publishes the v41 heartbeat
  beside the untouched legacy Failover beat — LWT delivery verified live
  against the local broker (SIGKILL → retained `offline`). Crate-rule
  amendment: `regress` (typify's validation regex engine) joins
  serde/serde_json as the only allowed deps.
- **Phase 1 step 4 deployed — the layout contract + the first honest drift
  count**: `contracts/src/layout/` schemas the panel JSON as it exists
  (widget-type classification seeded from the live dispatch code, two-mode
  validation where deprecations are named not fatal, the L3 yak binding with
  its cross-field rule, the L4 folder grammar) plus the Y7 runtime
  `yak_handler` wire message. `pnpm validate` (openair-validate) walks
  Gui_Frames + the YAK tree + every config.ini: **169 errors / 2,093
  deprecations** on day one — including the two 34401As, 57 `N_` prefix
  collisions, 45 dead config.ini topic triples, and 45 converter uses the
  YAK agent silently passes through. Inventory published at
  `Documents/Strategies/Validations/contracts-debt-inventory.md`.
- **Phase 1 step 5 deployed — the ratchet, armed**: `contracts/
  validate.baseline.json` locks the day-one debt; CI now fails only on debt
  NOT in the baseline (kill-tested: probe file → red, removed → green).
  `--update-baseline` shrinks it after fixes; the number only goes down.
- **Phase 1 step 6 deployed — Rust adoption seed. Phase 1 complete.**
  `openair-contracts` is a path dependency in BOTH BackEnd workspaces. First
  real consumers: the YAK agent registers an MQTT Last Will and publishes a
  retained contract-typed `AgentHeartbeat` at `OpenAir/System/Agents/yak`
  (verified live — SIGKILL flipped the retained status to `offline` via the
  broker); the orchestrator publishes its retained beat (LWT deferred to the
  Phase 4 supervisor's persistent client). All six Phase 1 DoD boxes ticked
  in `Documents/Strategies/Phase 1.md` §7.

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
