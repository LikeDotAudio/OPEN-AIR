> ## 📌 HISTORICAL SNAPSHOT — 2026-07-17 (v40)
>
> Preserved as written. Many findings below are now FIXED — see the resolution table in [0_README.md](../Audits/0_README.md#resolution-status).
> How the system works **today**: [`README.md`](../../README.md), [`contracts/README.md`](../../contracts/README.md), [`BackEnd/ComProtocols/README.md`](../../BackEnd/ComProtocols/README.md).
>
> **§8 (appended 2026-07-18) records what has since been accomplished and what happens
> next**, re-verified against the working tree at `964f9d29e`. Sections 1–7 below are the
> original text and are *not* edited; status markers in §8 supersede them wherever they
> disagree. The task list lives in [1 Plan of attack.md](../Audits/1%20Plan%20of%20attack.md).

# OPEN-AIR Design Audit — The Good, the Bad, and the Ugly

*2026-07-17 · v40 · High-level design only; implementation details cited as evidence, not as complaints.*

---

## 1. The extracted top-level goal

Before judging the design, state what it is for. Reading the code, the README,
the changelog, and the YAK tree, the mission is:

> **OPEN-AIR is a software VEE / LabVIEW**: an open, vendor-neutral instrument
> orchestration environment where
> 1. devices are **discovered automatically** across many protocols (VISA/SCPI,
>    MIDI, AES70, OSC, SNMP, Ember+, SMPTE 2138, PTP…),
> 2. a **middleware definition plane (YAK)** abstracts "multiple devices that do
>    the same thing differently" into one command vocabulary,
> 3. the **UI is composed from the filesystem** — folders are tabs, JSON files
>    are panels — and is editable live in a WYSIWYG editor,
> 4. everything flows over **one observable data bus (MQTT)**, so any component
>    (or any third-party tool) can watch, inject, log, or replay traffic.

Every architectural decision should be scored against those four pillars. The
audit below does exactly that.

**Non-negotiables carried forward** (per the owner): MQTT stays as the data
bus; the existing widget libraries stay; folders-make-tabs stays. Good news:
nothing in this audit argues against any of those. They are the *strongest*
parts of the design.

---

## 2. Scorecard

| Pillar | Idea | Execution today | Root cause |
|---|---|---|---|
| Discovery | ★★★★★ | ★★☆☆☆ | Discovery works; *delivery to the UI* is a broken 4-stage pipeline |
| YAK middleware | ★★★★★ | ★★☆☆☆ | No capability model — per-model copy-paste defeats the abstraction |
| Folders-make-tabs | ★★★★★ | ★★★☆☆ | Renders from a stale snapshot, not the live filesystem |
| MQTT bus | ★★★★★ | ★★★☆☆ | Three topic namespaces, plus a *second* bus (the `/ws` broadcast) |
| Supervision/keep-alive | ★★★★☆ | ★☆☆☆☆ | Empty stubs; nothing restarts anything |
| Logging | ★★★☆☆ | ★★☆☆☆ | Three parallel logging systems; the sophisticated one is unused |

---

## 3. The Good

These are the things worth protecting through the rewrite.

### 3.1 MQTT as the spine
Using retained MQTT topics as both transport *and* state store is a legitimate
architectural pattern (the broker is the database). It gives you, for free:
observability (`mosquitto_sub -t 'OpenAir/#'` is a debugger), language
neutrality (Rust, Python, browser all speak it), late-joiner state sync
(retained messages), and decoupling between producers and consumers. This is
the correct bus for a lab-orchestration system and it should stay.

### 3.2 Folders-make-tabs
`Gui_Frames/` → tabs is genuinely distinctive and genuinely good. The
filesystem *is* the document model: ordering via `N_` prefixes, splits via
`left_50`-style folder names (`FrontEnd/tabManager/WindowManager.jsx:12`),
panels as JSON files. Users reorganize their cockpit with a file manager, git
diffs the UI, and the WYSIWYG editor saves back into the same tree
(`POST /api/save`). This is the "your folders are your interface" pillar and it
works — the flaw is only that the browser renders a *snapshot* of the tree
rather than the tree (see §5.1).

### 3.3 The YAK verb grammar
`SET / RIG / NAB / DO` is a clean, minimal instrument grammar (write-scaled,
write-raw, query, imperative). The class → model → SCPI-subsystem folder
organization (`10_Yak/1_Spectrum_YAK/1_N9340B/0_Frequency/…`) matches how lab
people actually think about instruments. The *concept* of a middleware
definition plane between GUI intent and vendor dialect is exactly right — it is
the VEE/LabVIEW instrument-driver idea, done as data instead of code.

### 3.4 Rust protocol agents
Moving the protocol agents to Rust (`BackEnd/ComProtocols/openair-*`) was the
right call: the VISA subnet/gateway hunter, the AES70 `nom` parser, protobuf
for SMPTE 2138 — these are the parts that need to be fast, concurrent, and
crash-proof. The direction is correct; the supervision around them is not (§4.4).

### 3.5 The in-app WYSIWYG editor
The editor renders **inside the live app tree**, sharing the real MqttProvider
and the real renderer (`FrontEnd/editorWYSIWYG/Entry.jsx`). You edit the panel
while it shows live data, and save writes the same JSON the loader reads. Most
SCADA/test tooling separates "design time" from "run time"; OPEN-AIR fusing
them is a real differentiator and worth keeping intact.

### 3.6 Breadth of protocol ambition
Ten protocol crates, a widget library ~100 families deep, ECharts graphs, a
PWA shell, WASM-drawn panels. The scope is coherent with the mission — this is
not feature sprawl, it is the actual product.

---

## 4. The Bad

Structural decisions that are costing more than they return. These are the
things the TypeScript generation must fix *by design*, not by patching.

### 4.1 Two sources of truth, everywhere
This is the systemic disease. Every major subsystem has a pair of authorities
that can (and do) disagree:

| Subsystem | Truth A | Truth B | Consequence |
|---|---|---|---|
| UI tree | live `GET /api/tree` (`orchestrator/src/api.rs:33`) | static `FrontEnd/api/tree.json` snapshot, which is what `index.html:244` actually fetches | UI renders a 3.4 MB cached file from July 10; new folders/panels invisible |
| YAK command | SCPI template in `10_Yak/**.json` | routing/scaling in each widget's `yak_handler` block | Matched by bare string `command` name; nothing validates the pair |
| MQTT topics | `config.ini` `topic_listen`/`topic_publish` per agent | hard-coded strings in `main.rs` / `mqtt.rs` | INI values largely ignored; `OpenAir/System/Protocols/…` vs `OpenAir/Protocol/…` vs `OpenAir/Gui/#` coexist |
| Data bus | MQTT broker (1883/9001) | the orchestrator's own `/ws` broadcast (`SystemState`) | AES70/OSC discoveries go only to `/ws`; VISA/MIDI go only to MQTT — no single place sees everything |
| 34401A DMM | `4_DMM_YAK/1_34401A/` (full) | `8_Multimeter_YAK/1_34401A/` (partial, diverged) | Same physical instrument, two diverging definitions |

### 4.2 Stringly-typed boundaries with no contracts
Every inter-component boundary is an unchecked string:
- **Topics** are ad-hoc concatenation (`topicMaker.jsx`, `main.rs:284`).
- **Widget dispatch** is fuzzy substring matching — `type.includes('fader')`
  (`WidgetFactory.jsx:110-130`); a typo silently renders a dashed fallback box.
- **YAK lookup** is `HashMap<model, HashMap<commandName, scpi>>` with a
  fallback that searches *all models* when model is `None` — and `mqtt.rs`
  sets model to `None` on **every** execute, so two models sharing a command
  name silently shadow each other (`openair-yak/src/repository.rs`).
- **Converters** are a hard-coded enum where unknown names pass through
  silently (`openair-yak/src/converters.rs`).
- **Layout JSON** has at least three schema generations in the wild (`OcaBin`
  current, `_GuiValue`/`subscribe` legacy, Pattern A vs Pattern B YAK files)
  and no schema validates any of them.

This is the "shoehorned into ultra-flexible JSON + Python" debt the owner
already suspects. Flexibility without contracts became fragility.

### 4.3 YAK has no capability model
The three spectrum analyzers (`1_N9340B`, `2_N9342CN`, `3_HPE4411A`) carry
**byte-identical** frequency SCPI files. That means YAK today is not an
abstraction plane — it is three copies of the same driver. The entire point
("multiples of the same sort of device that does the same things differently")
requires: *class defines the capability, model supplies the dialect*. Today
there is no class-level definition at all, so a fourth spectrum analyzer means
a fourth copy-paste, and a fix to one means editing N files.

### 4.4 Supervision is a facade
- `openair.py` is a launcher, not a supervisor: it builds, kills port 8000,
  spawns YAK fire-and-forget, then `os.execv`s itself away (`openair.py:100`).
- Protocol agents are tokio tasks that die silently (AES70 swallows
  `ConnectionRefused`, `orchestrator/main.rs:196-198`). Nothing restarts them.
- `oa_heartbeat_core_rs` is an **empty stub** whose header comment promises a
  "sub-millisecond heartbeat orchestrator."
- Six protocol crates (`nmos`, `rest`, `sap`, `mdns`, `dnssd`, `websocket`)
  are 25-line placeholders that still publish `status = online` at boot
  (`Core/orchestrator/src/mqtt.rs`) — the system reports health it does not have.
- "Keep-alive" today means only the MQTT PINGREQ, which proves the socket is
  alive, not the agent, the device, or the pipeline.

### 4.5 The frontend platform has no floor
142 JSX files compiled by **Babel in the browser on every page load**, loaded
by 160 ordered `<script>` tags, communicating through **~197 `window.*`
globals**, cache-busted by hand-edited `?v=N` strings, with no package.json,
no bundler, no types, no lint. The 2.5 s splash screen exists to hide the
compile time. This was a rational v1 choice (zero toolchain); at 21,500 lines
of JSX it is now the single biggest brake on velocity, and it is precisely
what the TypeScript migration dissolves.

### 4.6 Three parallel logging systems
A sophisticated Rust logging gate with a hierarchical matrix
(`oa_logging_gate_rs`) exists — and nothing uses it. Agents log via raw
emoji `println!`, YAK via `env_logger`, and the debug toggler *regex-rewrites
source files* to flip `*DEBUG = True` flags (`oa_debug_toggler_rs`). The logs
that matter (device found, command sent, reply parsed) are not on the bus, so
the UI can never show them. Ironically, the best log viewer in the project is
`CommandRouter.jsx` — which works precisely because YAK publishes its monitor
traffic *to MQTT*. That pattern is the answer (§ Plan, Phase 4).

---

## 5. The Ugly

Small in line count, large in blast radius. Fix these regardless of any plan.

1. **Hard-coded wrong absolute paths, twice, both load-bearing.**
   `openair-yak/src/main.rs:32` and `build_discovered_gui.py:6` both point at
   `/home/anthony/Documents/OPEN-AIR/…` — the repo lives under
   `Documents/GitProjects/OPEN-AIR`. Result: the YAK agent loads **zero**
   definitions, and the discovery GUI builder writes into a phantom tree.
2. **The Rust VISA agent shells out to `python3 -c`** with a
   string-interpolated pyvisa script for every probe and every write, escaping
   quotes by `payload.replace("'","\\'")` (`orchestrator/main.rs:233-268,
   349-368`). That is a command-injection surface and a fork-per-command tax
   inside the "native" fast path.
3. **YAK is transmit-only.** The verbs publish SCPI out; no Rust component
   parses replies back into the `Outputs` `_GuiValue`s. NAB queries go out;
   answers go nowhere. State mirroring — half the point of the middleware —
   was dropped in the Python→Rust port.
4. **`retain: true` on every publish at up to 45 Hz** (`MqttProvider.jsx:35,
   143`): every fader drag leaves permanent retained state on the broker.
5. **Dead things that still bite:** the unreferenced `TabManager.jsx`; empty
   `comDatabase/` and `Core/Launch/`; `_Legacy_Commands/` folders and
   `*.json.old` files that the YAK loader happily ingests into the live
   command map; duplicated splash JSX inline in `index.html`.
6. **Folder-prefix collisions as identity.** Two YAK classes share prefix `4_`
   (`4_DMM_YAK`, `4_Load_YAK`); power models are numbered `1,2,2,2`. The
   loader derives model identity from these names.

---

## 6. Case study: why the Discovered tab is empty

The reported symptom — *"VISA identifies N9340B and 34401A, publishes to MQTT,
and the Discovered tab shows nothing"* — is the whole audit in one pipeline.
Four independent breaks, each an instance of a §4 disease:

```
VISA agent ──(retained MQTT)──► broker ──► build_discovered_gui.py ──► Gui_Frames/0_discovered/*.json ──► tree.json ──► browser
     OK              OK              ✗ (a)(b)(c)                                  ✗ (d)
```

- **(a) Wrong topic** — the builder subscribes to `visa/Device/#`
  (`build_discovered_gui.py:10`) but the agent publishes under
  `OpenAir/System/Protocols/visa/Device/…` (`main.rs:284`). It never receives
  a single message. *(Disease: stringly-typed topics, no shared contract.)*
- **(b) Wrong path** — output dir hard-coded to the phantom
  `/home/anthony/Documents/OPEN-AIR/…` (`build_discovered_gui.py:6`).
  *(Disease: config as constants.)*
- **(c) Never runs** — nothing launches the builder; `openair.py` doesn't know
  it exists. *(Disease: no supervisor owning the pipeline.)*
- **(d) Stale snapshot** — even with (a)–(c) fixed, the browser reads the
  static `FrontEnd/api/tree.json` from July 10, not the live `/api/tree`
  (`index.html:244`). New files would not appear until someone regenerates the
  snapshot. *(Disease: two sources of truth.)* And a fifth latent break: the
  builder emits legacy `_GuiValue`/`subscribe` schema the current renderer no
  longer speaks. *(Disease: no schema validation.)*

**Design conclusion:** discovered devices are *live data*, and routing live
data through a filesystem-generation step was the architectural mistake — the
filesystem tree should be reserved for *authored* UI. The right shape (detailed
in the plan): agents publish canonical retained device records to one
`OpenAir/Discovery/<protocol>/<deviceId>` namespace; the Discovered tab is a
**live widget** subscribed to `OpenAir/Discovery/#` that renders a card per
retained record — with a "Promote to panel" action that *then* writes an
authored frame into `Gui_Frames` via the existing `/api/save`. Discovery stays
data; folders stay the interface you *authored*. Also worth noting: the
`"Regex didn't match."` lines in the boot log are a red herring — they come
from README-JSON extraction in `api.rs:194`, not from discovery.

---

## 7. Systemic themes (what v41 must be built on)

1. **One truth per fact.** One tree endpoint. One topic grammar. One YAK
   definition per device. One bus (MQTT — the `/ws` SystemState channel either
   becomes a dumb MQTT-over-WebSocket bridge or dies).
2. **Contracts at every boundary.** A single `contracts/` package — TypeScript
   types + JSON Schema, mirrored into Rust via codegen — for: topic grammar,
   device records, YAK definitions, layout JSON, agent heartbeats. Everything
   that crosses a process boundary validates against it. This is the real
   payload of the TypeScript migration.
3. **Class/model split in YAK.** Capabilities defined once per device class;
   models supply dialect bindings and overrides. Copy-paste becomes inheritance.
4. **Liveness is data on the bus.** Agent heartbeats, device last-seen, command
   monitors — all retained MQTT topics, all renderable by ordinary widgets.
   The system's health UI becomes just another folder of panels.
5. **The filesystem is for authored UI; the bus is for live state.** Folders
   make tabs — and the tree the browser renders must be the *live* tree,
   pushed on change, so reorganizing folders redraws the dashboard in real
   time. That finally delivers the README's promise.

The concrete migration sequence, the YAK 2 definition format, and the WASM
strategy are in [3_TypeScript_Migration_Plan.md](../Strategies/3_TypeScript_Migration_Plan.md).
Diagrams for all of the above are in [2_Architecture_Diagrams.md](2_Architecture_Diagrams.md)
(in `Documents/notes/`, not this folder — see its §7 for the current-state diagram).

---

# 8. Status — what has been accomplished, and next steps

*Appended 2026-07-18. Re-verified against the working tree at `964f9d29e` by direct
inspection — deliberately not against git history or the changelog's self-description.
Where this section and §§1–7 disagree, this section is current.*

## 8.1 Updated scorecard

| Pillar | Execution 2026-07-17 | Execution 2026-07-18 | What moved |
|---|---|---|---|
| Discovery | ★★☆☆☆ | ★★★★☆ | 17 VISA instruments correctly categorized on real hardware; DNS-SD went from a `2+2` stub to a working mDNS agent finding 42 services. Delivery to the UI works. Held at 4 — still round-trips through the filesystem (§8.4). |
| YAK middleware | ★★☆☆☆ | ★★☆☆☆ | Unchanged by design — YAK 2 is Phase 3 and explicitly frozen. Bindings are now *linted* (46 `yak-binding-lint` findings), which is measurement, not repair. |
| Folders-make-tabs | ★★★☆☆ | ★★★★☆ | The browser now fetches the live `GET /api/tree`; the stale snapshot is only a static-host fallback. §4.1's headline instance is closed. |
| MQTT bus | ★★★☆☆ | ★★★☆☆ | One declared topic grammar now exists and is enforced. **Not raised** because the `/ws` side-bus survives and is worse than described (§8.3). |
| Supervision / keep-alive | ★☆☆☆☆ | ★★★☆☆ | Real `AgentHeartbeat` + MQTT Last Will on every agent *and* browser session, verified live with SIGKILL. Stubs publish `status = stub` instead of `online`. Restart/supervision still absent. |
| Logging | ★★☆☆☆ | ★★☆☆☆ | Untouched. Phase 4. |
| **Contracts** *(new pillar)* | — | ★★★★☆ | The §7.2 recommendation shipped: `contracts/` with zod schemas, a topic grammar, cross-language golden vectors, `zod → JSON Schema → cargo-typify` codegen with a freshness gate, and a CI ratchet. |

## 8.2 Accomplished — findings now closed

**From §4 (The Bad):**

- **§4.1 UI tree** — ✅ Fixed. Live endpoint is authoritative.
- **§4.1 MQTT topics** — ✅ Fixed. One topic grammar (`contracts/src/topics/`), legacy
  classifier, and `config.ini` values now linted rather than ignored.
- **§4.2 Stringly-typed boundaries** — ✅ **Fixed, and this was the audit's central
  finding.** `contracts/` defines every shape crossing every boundary once in
  TypeScript and *generates* the Rust the agents compile against. Golden vectors in
  `contracts/vectors/` are consumed by **both** vitest and `cargo test`, so adding a
  case on one side fails the other side's CI until implemented. Device-ID derivation
  (FNV-1a 64) is implemented twice and pinned by vectors, because two agents computing
  different IDs would silently fork the device registry.
- **§4.4 Supervision is a facade** — ✅ Mostly fixed. Heartbeats and Last Will are real
  and live-verified; the broker is the supervisor. Restart remains Phase 4.

**From §5 (The Ugly):**

- **§5.1 Hard-coded absolute paths** — ✅ Fixed in Rust (zero occurrences in any `.rs`
  file) and in the discovered-GUI builder, which now derives its path from `__file__`.
  Four remain in Python utilities (§8.3).
- **§5.4 `retain: true` at 45 Hz** — ✅ Fixed. Control values publish non-retained; one
  settle-delayed retained publish preserves late-joiner state.
- **§5.5 Dead things** — 🔄 Partial. `topicUtils.js` deleted; `_Legacy_Commands/`,
  `*.json.old`, and `temp_norm_*` are now *reported* (41 findings) rather than silently
  ingested.

**From §6 (the Discovered-tab case study):** ✅ All four documented breaks plus the
latent fifth are fixed — correct topic (`build_discovered_gui.py:40`), derived path
(`:28`), actually spawned (`main.rs:381`), current OcaBin schema. The *architectural*
objection stands (§8.4).

**Beyond the audit** — measurement infrastructure that did not previously exist:
`openair-validate` names 169 errors and 2,093 deprecations, baselined in
`validate.baseline.json` so CI fails only on *new* debt; `contracts-ci.yml` replaced
deploy-only CI with four real jobs.

> **The honest qualifier.** Of the above, the contract layer, the heartbeats, and the
> tree fix are genuine repairs. The drift baseline is **measurement, not repair** — as
> of today nothing in it has been paid down. That distinction is preserved deliberately;
> see §8.5.

## 8.3 Findings that got *worse* or were understated

Three items where re-verification contradicts the optimistic reading:

1. **§5.2 `python3 -c` interpolation is unauthenticated, network-reachable RCE.**
   `main.rs:552` "escapes" quotes with `payload.replace("'", "\\'")`, which writes a
   backslash into Python *source*; a payload ending in a trailing backslash consumes the
   closing quote and breaks out. The payload arrives raw off MQTT (`main.rs:532`), and
   `broker/mosquitto.conf:20` sets `allow_anonymous true` with no `bind_address` on
   either listener. **Any host that can reach TCP 1883 gets code execution as the
   orchestrator user.** This is now the highest-severity item in the repository.
2. **§4.1 `/ws` side-bus has zero consumers.** Four producers publish `SystemState` to
   it; grepping the tree for `/ws` yields only the route (`main.rs:420`) and a comment.
   The browser uses MQTT-over-WebSocket on 9001 instead. MIDI and VISA are dual-homed
   and survive — **OSC and AES70 discoveries therefore reach nothing at all.** This is a
   bug, not architectural debt.
3. **§5.6 folder-prefix collisions are 57, not 2.** Across 44 directories, including the
   repo root and `5_Protocols/10_Yak` itself. §5.1's path problem also persists in four
   Python files, all pointing at the *old* repo root — broken, not merely non-portable.
4. **§4.1's "two sources of truth" is a *three*-way split for the YAK listen topic.**
   `config.ini` declares `OpenAir/Gui/Protocols/Yak/#`; `config.rs:18` defaults to
   `OpenAir/System/Protocols/yak/sub`; and `mqtt.rs:46` **hard-codes `"OpenAir/Gui/#"`
   and subscribes to that**. `config.topic_listen` is parsed into the struct and then
   referenced zero times. Detail in
   [yak_protocol_report.md](yak_protocol_report.md#21-the-listen-topic-has-three-competing-values).

Also note **§4.5 (frontend has no floor) is less improved than it appears**: `ui/`
bundles the whole app only by side-effect-importing 146 untouched `.jsx` files through
`legacy.ts`. Zero widget or manager modules are converted, 207 of 210 globals are still
`any`, `ui/` has no tests, and `FrontEnd/index.html` remains the served runtime.

## 8.4 Standing design conclusions, unchanged

The two structural conclusions of this audit are **not** yet delivered and remain the
target:

- **Discovery is live data and must stop round-tripping through the filesystem.**
  `build_discovered_gui.py:191` still writes panels to `Gui_Frames/0_discovered/`. The
  script's own docstring concedes values are "baked as static text at scan time"
  because the browser only subscribes to `OpenAir/Gui/#`. The §6 target shape — agents
  publish retained records to `OpenAir/Discovery/<protocol>/<deviceId>`, the Discovered
  tab is a live widget, "Promote to panel" writes authored frames — stands.
- **§4.3 YAK has no capability model.** Unchanged and deliberately frozen. The
  duplicate 34401A (§4.1) proves the cost: `repository.rs` keys on
  `HashMap<model, …>` while `mqtt.rs:102-104` passes `model: None` on every execute, so
  the two definitions **silently shadow each other** — last loaded wins. Note the
  `None` is now *deliberate*, with a source comment explaining that the GUI hierarchy
  no longer carries the model; it is a reasonable local decision that becomes a
  correctness bug the moment two models share a command name.
- **§5.3 YAK is transmit-only** — still true; no module parses replies. But the
  missing half is now half-built: `nab.rs:25-31` wraps outbound commands in a
  `correlation_id` envelope, so the receiver has something to match on. See
  [yak_protocol_report.md](yak_protocol_report.md) §2.3, which also records that
  `openair-yak` is **no longer a scaffold** — it is a 427-line binary implementing all
  four verbs, with no `lib.rs` and therefore none of the `2+2` template problem.

## 8.5 Next steps

Full task list with sizes and evidence: **[1 Plan of attack.md](../Audits/1%20Plan%20of%20attack.md)**.
Summarized against this audit's own sections:

| Horizon | Work | Closes |
|---|---|---|
| **Day 14** | Bind + authenticate the broker; delete the subprocess interpolation and pin it with a trailing-backslash vector; fix the 4 broken Python paths; complete `requirements.txt`; attest credential rotation in writing; gate production deploys behind CI; evict the 210 MB `.crawler/` | §5.2, §5.1, §8.3 |
| **Day 45** | One-command startup (broker + orchestrator + UI); CI green on a clean second machine; run the tests CI currently only `cargo check`s; retire `/ws` and publish OSC/AES70 to MQTT; codemod the two mechanical debt rules; merge the duplicate 34401A; fix root-level prefix collisions | §4.1, §4.6, §5.5, §5.6, §8.3 |
| **Day 90** | A stranger installs and drives an instrument we do not own, without contacting the author | §7 as a whole |
| **Frozen** | YAK 2 / class-model split (§4.3), WASM core, native Rust VXI-11, live Discovered widget (§6), unified logging (§4.6), device registry + restart supervision (§4.4) | Phase 3–4 |

**The debt is more tractable than the raw count suggests.** Of 2,262 findings,
`legacy-widget-type` (856) and `legacy-label-form` (655) are **1,511 — 67% — and both
are mechanical codemods.** Two afternoons plus review retires two-thirds of the
baseline. Conversely, 236 findings live under `5_Samples/`, so deleting demo files
would book a 10.4% "reduction" while repairing nothing; the ratchet must therefore
report per-rule, exclude `5_Samples/` from reduction targets, and fail when file counts
drop without a Migration Ledger entry.
