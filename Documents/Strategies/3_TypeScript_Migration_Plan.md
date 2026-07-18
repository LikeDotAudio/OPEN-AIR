> ## ⚠️ HISTORICAL PLANNING DOCUMENT — Phases 0–1 SHIPPED · Phase 2 partial · Phases 3–5 are the roadmap
>
> This is a *plan*, not a description of how OPEN-AIR works today.
> The shipped parts are documented as features in [`contracts/README.md`](../../contracts/README.md), [`BackEnd/ComProtocols/README.md`](../../BackEnd/ComProtocols/README.md), and [`ui/README.md`](../../ui/README.md).
> See [Strategies/README.md](README.md) for the full index.

# The TypeScript + WASM Plan (v40 → v41)

*2026-07-17 · Companion to [1_Design_Audit.md](../notes/1_Design_Audit.md). Ordered so
each phase pays for itself and nothing big-bangs. The prime directive
throughout: **the migration's product is the contract layer** — TypeScript is
the vehicle, not the destination.*

## Ground rules

- **MQTT stays the bus.** The browser speaks MQTT-over-WebSocket only; the
  orchestrator's parallel `/ws` `SystemState` channel is retired (or reduced to
  a dumb bridge during transition).
- **Folders stay the interface.** The tab engine, `N_` ordering, `left_50`
  splits, and JSON panels all survive — they just get a schema and a live tree.
- **The widget library survives.** Every `libControl` component ports
  mechanically (`.jsx` → `.tsx`); none are redesigned in this migration.
- **No rewrite freezes.** v40 keeps running; each phase ships into it.

---

## Phase 0 — Stop the bleeding (days, not weeks)

Pure fixes; no architecture. Worth doing even if the rest never happens.

1. Kill both phantom absolute paths: derive repo root at runtime
   (`openair-yak/src/main.rs:32`, `build_discovered_gui.py:6`). Today the YAK
   agent loads **zero** definitions.
2. Point `index.html:244` at live `/api/tree` instead of the stale
   `api/tree.json` snapshot; delete the snapshot files.
3. To get devices listing in the Discovered tab *now*: fix the builder's
   subscription to `OpenAir/System/Protocols/visa/Device/#` (+ midi), fix its
   output schema to the current `OcaBin` shape, and have the orchestrator spawn
   it. (This whole pipeline is replaced in Phase 4 — patch it only enough to
   be useful meanwhile.)
4. Stop stub protocols (nmos/rest/sap/mdns/dnssd/websocket) from publishing
   `status = online`; publish `status = stub`.
5. `retain: false` for high-rate control values; retained only for
   config/state topics.
6. Check in a `broker/mosquitto.conf` (1883 + websockets 9001) so the broker
   stops being an unmanaged assumption.

## Phase 1 — The contracts package (the keystone)

Create `contracts/` — a single package that owns every cross-boundary shape.
TypeScript-first with zod (runtime validation for free), JSON Schema exported
from it, Rust types generated from the same source (schemars/typify, or
ts→JSON-Schema→Rust codegen in CI).

Contents:
- **Topic grammar.** One builder/parser for the whole namespace — no more
  string concatenation on either side. Collapse today's three namespaces
  (`OpenAir/System/Protocols`, `OpenAir/Protocol`, `OpenAir/Gui`) into one
  documented tree: `OpenAir/{Discovery|Gui|Yak|System}/...`.
- **DeviceRecord** — canonical discovered-device document (protocol, class,
  make, model, serial, address, lastSeen, status). One shape for VISA, MIDI,
  AES70, everything.
- **Layout schema** — the `OcaBin`/`OcaBlock`/field JSON, finally written
  down. Includes the yak binding block.
- **YAK schemas** — class capability files + model binding files (Phase 3).
- **Agent heartbeat** shape.

Definition of done: a `validate` CLI that walks `Gui_Frames` and the YAK tree
and reports every file that fails schema — run it in CI. (Expect a long list
on day one; that list *is* the technical-debt inventory.)

## Phase 2 — Frontend to TypeScript (incremental, not big-bang)

1. Introduce **Vite + TypeScript** alongside the current app: `package.json`,
   pin React 18, ECharts, MQTT.js as real dependencies (no CDNs), emit one
   bundle that `index.html` loads instead of 160 script tags. This alone
   removes Babel-in-browser, the splash-hidden compile, `?v=N` cache-busting,
   and load-order fragility.
2. Convert leaf-first with `allowJs: true`: utilities (`topicMaker`,
   `oaCssLen`) → hooks/providers (`MqttProvider`) → `WidgetFactory` +
   `FieldComponent` → widgets in batches → `WindowManager` last (and split its
   708 lines: tab engine / split-pane / MQTT lazy-publisher / editor bridge).
3. **Typed widget registry** replaces fuzzy dispatch: each widget module
   exports `register({ type: 'fader', component: Fader, schema })`; unknown
   types fail loudly. Deletes `WidgetFactory.jsx:110-130`'s
   `type.includes('fader')` roulette.
4. Delete the dead weight while passing through: `TabManager.jsx`, `js/app.js`,
   `css/style.css`, empty `comDatabase/`/`Core/Launch/`, duplicate splash JSX.
5. The WYSIWYG editor converts last, and gains the **validation gate**: saves
   must pass the layout schema (zod, in-browser) before `POST /api/save`.

Everything the user sees is unchanged; the platform underneath becomes typed,
bundled, and tree-shaken.

## Phase 3 — YAK 2: the capability model + one WASM core

This is the heart of the "middleware definition plane" vision.

**Definition split** (schema'd in `contracts/`):
- `yak/classes/SpectrumAnalyzer.yak.json` — capabilities, once per class:
  names, verbs allowed, units, ranges (`frequency.center: { verb: set|nab,
  unit: Hz, min, max }`). This is the plane the GUI binds to.
- `yak/models/N9340B.yak.json` — dialect bindings per capability
  (`frequency.center: ":FREQuency:CENTer {Hz}"`), plus **reply parsers** for
  NAB, plus `inherits:` so N9342CN is a delta file, not a clone. The three
  byte-identical spectrum definitions collapse to one class + three deltas.
- Widgets bind to `class.capability` (+ unit), not to a per-model command
  string — the two-sources-of-truth problem dissolves because the widget side
  and the device side both reference the same declared capability.

**Compiler:** `yak-compile` validates everything, resolves inheritance,
excludes `_Legacy_Commands`/`*.old`, detects duplicate/colliding names
(goodbye `4_DMM`/`4_Load`, goodbye second 34401A), and emits one flat
`yak.artifact.json`.

**One translation core, two targets:** a Rust crate implementing
SET/RIG/NAB/DO against the artifact — converters become declarative unit
conversions (Hz↔MHz from the schema, not a hard-coded enum) — built natively
into the YAK agent **and** to wasm32 via wasm-bindgen for the browser. The
WASM build gives the WYSIWYG editor offline validation, command preview
("this knob will emit `:FREQuency:CENTer 98700000`"), and full panel dry-runs
with a simulated device — VEE/LabVIEW-style design-time, with zero duplicated
logic.

**Close the loop:** the agent finally parses replies (the ported
`yak_receiver`), publishing typed state to `OpenAir/Yak/state/...` so `Outputs`
values mirror the instrument again. Correlation IDs already exist in NAB —
use them.

## Phase 4 — Discovery, supervision, and liveness as bus data

1. **Device Registry service** (small Rust task): consumes every protocol's
   raw finds, normalizes to `DeviceRecord`, publishes retained
   `OpenAir/Discovery/{protocol}/{deviceId}`, ages records out via
   `lastSeen` TTL (finally: keep-alive semantics for devices, not just
   sockets). AES70/OSC move onto MQTT here — the `/ws` side-bus retires.
2. **Discovered tab becomes a live widget** subscribed to
   `OpenAir/Discovery/#`: one card per retained record, green/grey by TTL,
   with **"Promote to panel"** — which looks up the model in the YAK artifact
   and writes an authored frame into the tree via `/api/save`. Discovery is
   data; folders hold what you *chose* to keep. `build_discovered_gui.py` is
   deleted.
3. **Supervisor:** the orchestrator owns agent lifecycles — spawn, watch,
   restart with backoff — and each agent publishes a retained heartbeat
   (`OpenAir/System/Agents/{name}`: status, version, lastBeat). A "System"
   folder of ordinary panels renders it. `openair.py` shrinks to `cargo run`.
4. **Native VISA:** replace the `python3 -c` pyvisa subshell with Rust VXI-11
   (the scanner already speaks it) — removes the injection surface, the
   per-command fork, and the last Python in the hot path.
5. **Logging on the bus:** agents log structured events to
   `OpenAir/System/Log/{source}/{level}` (as YAK's monitor topics already
   prove out); `CommandRouter`-style viewers become the system console. The
   unused Rust logging-matrix and the regex debug-toggler retire.

## Phase 5 — Live tree & polish

- fs-watch on the panels tree → retained tree topic → every browser redraws on
  folder change. "Your folders are your interface," live.
- Purge the ghost PyO3 modules (`oa_heartbeat_core_rs` and friends) or make
  the stubs honest; drop the `sys.modules` import hack once no Python imports
  remain.
- Repo reshape to the v41 layout (see diagram 4): `contracts/`, `agents/`,
  `yak/`, `ui/`, `panels/`, `broker/`.

---

## Sequencing rationale & risk

- **Phase 1 before Phase 2** because typing the frontend against unschema'd
  JSON just freezes today's drift into TypeScript `any`s.
- **Phase 3 before Phase 4's "Promote to panel"** because promotion needs the
  YAK artifact to know what panel a discovered N9342CN deserves.
- Biggest risk is Phase 3 scope. Contain it: keep the verb grammar and the
  folder organization exactly as-is; only *add* the class layer and the reply
  path. Migrate one device class end-to-end (Spectrum — it has the perfect
  three-similar-models test case) before converting the rest.
- Biggest payoff per effort: Phase 0 item 2 + Phase 4 item 2 — that is the
  path that puts discovered devices in the Discovered tab *by design* instead
  of by pipeline repair.
