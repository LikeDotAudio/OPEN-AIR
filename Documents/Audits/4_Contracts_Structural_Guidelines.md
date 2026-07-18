# Structural Guidelines for `contracts/` — the Phase 1 Keystone

*2026-07-17 · Companion to [3_TypeScript_Migration_Plan.md](3_TypeScript_Migration_Plan.md)
(Phase 1) and [1_Design_Audit.md](1_Design_Audit.md) (§4.2, §7.2). Based on a
full code-level inventory of every cross-boundary shape in v40: all MQTT topic
strings in Rust/Python/JS, every device-record and heartbeat payload, the
de-facto layout JSON schema across 478 `Gui_Frames` files, and all 192 files of
the YAK tree plus its parser.*

---

## 0. What the inventory changed about Phase 1

The plan's Phase 1 text was written from the design audit. The code-level sweep
confirms the thesis (every boundary is an unchecked string) but **corrects five
assumptions** the contracts package must not bake in:

1. **The YAK placeholder syntax is `<name>`, not `{Hz}`.** The tree uses
   angle-bracket placeholders (`<hz_value>`, `<offset>`, `<channel>`…) with a
   *minority* brace form (`{value}`, bare `{}`) mixed in. The runtime replaces
   `<input_name>`, falling back to "first `<...>` found"
   (`openair-yak/src/verbs/set.rs`). The contracts grammar must define the
   angle-bracket form as canonical and flag the brace files as legacy.
2. **The verbs are not in the definition files.** SET/RIG/NAB/DO never appear
   in the YAK tree JSON — they arrive at runtime as `yak_handler.yak_type`
   over MQTT (`openair-yak/src/models.rs:9`). The block labels `NAB`,
   `RIG_Settings` in the files are human convention the parser ignores
   entirely (`repository.rs:83-101`). So there are **two** YAK contracts to
   write: the definition-file shape *and* the runtime `yak_handler` message.
3. **The yak binding block's real keys** are `enable, yak_type, sub_path,
   command, input_name, converter` (+ occasional `marker_number`,
   `trace_number`, `trigger_only`) — not the `verb/command/topic/unit` sketch
   in the plan. 62 occurrences, all consistent.
4. **`FrontEnd/YAK/` is empty.** The real tree is
   `FrontEnd/Gui_Frames/5_Protocols/10_Yak/` (192 files). The `validate` CLI
   must walk that path (and the empty dir should be deleted).
5. **`OpenAir/Protocol/...` is not an MQTT namespace.** Those strings
   (`GuiOsc`, `MidiIn`, `AES70`) are `SystemState.topic` fields on the `/ws`
   WebSocket broadcast (`orchestrator/src/main.rs:456-466`); no broker ever
   sees them. "Collapsing three namespaces" is really: collapse **two** MQTT
   namespaces + absorb one WebSocket side-bus.

Everything below is written against what is actually on disk.

---

## 1. Package structure

```
contracts/
├── package.json            # name: @openair/contracts — zod is the ONLY runtime dep
├── src/
│   ├── topics/
│   │   ├── grammar.ts      # segment rules, casing, reserved names
│   │   ├── tree.ts         # the full declared topic tree (one table)
│   │   └── builders.ts     # typed build/parse per topic family
│   ├── device-record.ts    # DeviceRecord + status enum + identity rules
│   ├── heartbeat.ts        # AgentHeartbeat + LWT payload
│   ├── envelope.ts         # the {value, full_id} GUI envelope, versioned
│   ├── layout/
│   │   ├── node.ts         # OcaBin/OcaBlock/leaf discriminated union
│   │   ├── widget-types.ts # the closed enum of widget type strings
│   │   ├── yak-binding.ts  # yak_handler block
│   │   └── folder-grammar.ts # N_ prefixes, split names, topic derivation
│   ├── yak/
│   │   ├── class.ts        # YAK 2 class capability file (Phase 3 target)
│   │   ├── model.ts        # YAK 2 model binding file (Phase 3 target)
│   │   ├── v40-definition.ts # schema of TODAY'S tree files (migration source)
│   │   └── verbs.ts        # SET/RIG/NAB/DO + yak_handler message schema
│   ├── log-event.ts        # LogEvent stream doc (Phase 4 pre-work)
│   └── index.ts
├── vectors/                # language-neutral golden vectors (topics + payloads),
│                           #   consumed by BOTH vitest and cargo test (Phase 1 §4)
├── schemas/                # generated JSON Schema output (checked in, diffed in CI)
├── rust/                   # openair-contracts crate: src/gen/ is typify output,
│                           #   never hand-edited; src/topics.rs is the hand-written
│                           #   grammar mirror, pinned honest by vectors/
└── cli/validate.ts         # the walk-and-report CLI (§7)
```

Structural rules for the package itself:

- **R1 — One shape, one file, one export.** Every cross-boundary shape is a
  zod schema plus its inferred TS type, exported once. No type is declared in
  `ui/` or `agents/` that duplicates a contracts shape — the Rust side gets it
  by codegen only.
- **R2 — zod is the only runtime dependency.** `contracts/` imports nothing
  from the app and depends on no framework, so it can be consumed by the Vite
  bundle, the validate CLI, Node scripts, and (via JSON Schema) Rust and any
  future consumer.
- **R3 — generated artifacts are committed and diffed.** `schemas/*.json` and
  the Rust crate are generated in CI and committed, so a PR that changes a
  contract shows the schema diff in review. CI fails if regeneration produces
  a diff the PR didn't include. (Today's CI is FTPS deploy only —
  `.github/workflows/deploy-*.yml` — with zero test/lint/cargo steps; this is
  the first real gate.)
- **R4 — every schema carries `schemaVersion`.** Retained MQTT documents
  outlive deployments (the broker is the database). Every retained document
  schema gets a `schemaVersion: z.literal(N)` field so consumers can reject or
  migrate old retained state instead of misparsing it. Today's payloads have
  no version field anywhere.
- **R5 — casing policy.** New v41 documents use `camelCase` keys (`lastSeen`,
  `deviceType`). Schemas that describe *existing* v40 wire shapes
  (`last_online`, `full_id`, `yak_handler`) keep their historical snake_case
  and live under a `V40` name or a `/** @deprecated v40 */` tag. No schema
  mixes the two conventions.
- **R6 — no stringly enums.** Every vocabulary discovered in the inventory
  becomes a closed zod enum: device `status`, agent `status`, verb names,
  converter names, protocol names, widget `type` strings, split-folder
  directions. Unknown values fail parsing loudly — the direct antidote to
  `type.includes('fader')` dispatch and silent converter passthrough.

---

## 2. Topic grammar (`contracts/src/topics/`)

### What the inventory found

- Exactly **one** topic helper exists in the whole codebase
  (`FrontEnd/comMQTT/topicMaker.jsx` — `buildGuiPrefix`); every other topic in
  Rust (`format!` in ~25 sites), JS (template literals in EQ, Sampler,
  Sequencer, Reverb, DirectionalButtons…), and Python (f-strings in the test
  harnesses) is raw concatenation.
- The browser subscribes to **exactly one wildcard**: `OpenAir/Gui/#`
  (`MqttProvider.jsx:69`). Every frontend read outside it is silently dead —
  notably `CommandRouter.jsx:17-18` reading
  `OpenAir/System/Protocols/yak/monitor/{in,out}`, and `Fleet_Display.json`
  subscribing to `OPEN-AIR/...` (wrong casing entirely).
- Three different values exist for the YAK listen topic: hardcoded
  `OpenAir/Gui/#` (`mqtt.rs:19`), config.ini `OpenAir/Gui/Protocols/Yak/#`,
  and the code default `OpenAir/System/Protocols/yak/sub` (`config.rs:18`).
  Only the hardcoded one is live.
- Two competing "protocol config" shapes:
  `OpenAir/System/Protocols/{proto}/config` (orchestrator, `mqtt.rs:90`) vs
  `OpenAir/System/Config/{proto}` (frontend, `ProtocolConfigDisplay.jsx:51`) —
  neither side subscribes to the other.
- Retain policy is decided per call site: all GUI publishes hardcode
  `retain: true` (`MqttProvider.jsx:135,174`) including 45 Hz fader values,
  while MIDI input events and YAK monitor traffic are non-retained.
- At least six topic families are published with **no subscriber in the repo**
  (`/config`, `/status`, `System/Config/{proto}`, `Failover` heartbeat,
  `Deploy/stamp`, the whole MIDI Input tree).

### Guidelines

- **T1 — The topic tree is a declared table, not emergent strings.**
  `topics/tree.ts` enumerates every topic family as data: pattern with typed
  segments, direction, payload schema reference, retain class, QoS class, and
  the intended producer/consumer roles. The builders and parsers in
  `builders.ts` are generated from (or written against) this table. The table
  *is* the documentation the plan asked for — and it is machine-checkable.
- **T2 — Ban concatenation outside `contracts/`.** All app code builds topics
  via the typed builders and parses via the typed parsers (which return a
  discriminated union, not `string[]` indexing — the `parts[2]`-style indexing
  in `build_discovered_gui.py:19-21` is the failure mode). A grep-able lint
  rule ("no string literal starting with `OpenAir/` outside contracts") is
  cheap and worth adding to CI on day one; the Rust codegen ships equivalent
  `Topic` constructors so `format!("OpenAir/...")` can be banned there too.
- **T3 — One tree, four crowns:** `OpenAir/{Discovery|Gui|Yak|System}/...` as
  the plan specifies, with the additional rulings the inventory forces:
  - `OpenAir/Discovery/{protocol}/{deviceId}` — **one JSON document per
    device**, not today's one-topic-per-attribute explosion
    (`.../Dev{n}/{manufacturer}`, `/serial`, … at `main.rs:303`). Per-attribute
    topics make atomic reads impossible and forced the `/value`-leaf guessing
    that broke `build_discovered_gui.py`.
  - `OpenAir/Yak/...` absorbs today's `OpenAir/System/Protocols/yak/{pub,
    monitor/*, ignore}` and the `/config` piggyback channel on Gui topics.
  - `OpenAir/System/{Agents|Config|Log}/...` — one config channel (ending the
    `System/Protocols/{p}/config` vs `System/Config/{p}` split).
  - The `/ws` `SystemState` strings (`OpenAir/Protocol/*`) map into the tree
    (AES70/OSC/MIDI events under `OpenAir/Discovery` or `OpenAir/System`) as
    part of retiring the side-bus.
- **T4 — Segment grammar is explicit.** Allowed charset per segment
  (`[A-Za-z0-9_-]`, no spaces — today spaces are patched to `_` ad-hoc at
  `main.rs:284`), fixed casing (`OpenAir` literal; the `oagui`→`GUI` mapping
  in `topicMaker.jsx:38` and the `OPEN-AIR` frame are both bugs the grammar
  outlaws), and no empty segments. The parser rejects, never guesses.
- **T5 — Retain class belongs to the topic family, not the publish call.**
  The table marks each family `retained-state` (device records, heartbeats,
  configs, tree) or `live-event` (control values, MIDI events, monitors).
  Builders expose this so the MQTT layer sets the flag from the contract —
  dissolving both the 45 Hz-retained-fader bug and the it-depends drift.
- **T6 — Subscriptions are contracts too.** The browser's single
  `OpenAir/Gui/#` subscription is why CommandRouter is dead. Each consumer
  declares which topic families it reads, from the same table, so "component
  reads a family nobody delivers to it" becomes a static error the validate
  CLI can report, not a silently empty widget.
- **T7 — A v40 alias map, not silent renames.** The table carries
  `v40Aliases` per family (e.g. `OpenAir/System/Protocols/visa/Device/#` →
  `OpenAir/Discovery/visa/...`) so the transition bridge and the validate CLI
  can mechanically flag old-namespace usage while both exist.

---

## 3. DeviceRecord (`contracts/src/device-record.ts`)

### What the inventory found

- The de-facto VISA record: `manufacturer, model, serial, firmware, raw_idn,
  resource, device_type, notes, last_online, connected, status` — maintained
  in **two hand-synced implementations** (PyO3 `resource_manager/mod.rs:61-134`
  and the orchestrator's inline-python path `main.rs:210-325`).
- `status` has three unrelated vocabularies: `"found"/"identified"`
  (orchestrator), `"Unresponsive"` (scan_and_catalog), `"online"` (protocol
  status). `connected` is numeric 0/1 while the browser heartbeat uses boolean
  `active`. MIDI's `type` means input/output role; the known-devices JSON's
  `type` means device category.
- Device identity is `Dev{n}` — a scan-order index. `last_online` is stamped
  once at boot and never refreshed; nothing ages anything out.
- MIDI records are just `name` + `type`; AES70/OSC/SNMP emit *control events*,
  not device inventory; six protocol crates are stubs.

### Guidelines

- **D1 — One document, one topic.** `DeviceRecord` is a single JSON document
  published retained to `OpenAir/Discovery/{protocol}/{deviceId}`. Canonical
  fields: `schemaVersion, protocol, deviceId, deviceClass, make, model,
  serial, firmware, address, rawIdn, status, firstSeen, lastSeen, notes,
  extra`. `extra` is an explicitly-typed per-protocol extension object
  (`visa: { resource }`, `midi: { direction, portIndex }`) — protocol
  specifics never leak into the core field set.
- **D2 — `deviceId` is stable and derived by declared rule, not scan order.**
  Priority: serial number → protocol-native stable address (VISA resource
  string, MIDI port name) → content hash of make+model+address. The derivation
  function lives in contracts (both languages get it), because two agents
  computing IDs differently recreates the duplicate-34401A problem on the bus.
- **D3 — One `status` enum for devices:**
  `discovered | identified | unresponsive | stale | removed`, with `stub`
  reserved for agents (§4). The three current vocabularies map into it in the
  schema's doc comment so the migration is mechanical.
- **D4 — Liveness is data with rules.** `lastSeen` is required and refreshed
  by the registry (Phase 4); the contract *documents the TTL semantics*
  (e.g. `stale` after N missed refreshes, record deleted/`removed` after M) so
  UI, registry, and tests share one definition. Booleans for liveness
  (`connected: 0|1`) are banned — staleness is computed from `lastSeen`, never
  stored as a flag that goes stale itself (which is exactly what
  `connected:1`-forever does today).
- **D5 — Discovery ≠ control.** AES70/OSC control events get their own small
  event schemas; they are not DeviceRecords. A protocol that cannot yet
  enumerate devices publishes no records — it does not fake one.

---

## 4. Agent heartbeat (`contracts/src/heartbeat.ts`)

### What the inventory found

- No agent publishes a real heartbeat. The orchestrator writes a retained
  `/status = "online"` string once at boot for **all sixteen** protocols —
  including the six stub crates (`mqtt.rs:91`) — and nothing ever writes an
  offline counterpart. `oa_heartbeat_core_rs` is an empty stub. The only live
  beat is the browser's 1 Hz `Failover` publish, which registers **no MQTT
  LWT**, so a killed tab leaves `active: true` retained forever
  (`MqttProvider.jsx:81-135`).

### Guidelines

- **H1 — One shape:** `AgentHeartbeat = { schemaVersion, agent, status,
  version, startedAt, lastBeat, partition?, host?, pid? }` (`partition` is
  the browser-failover field, carried by web sessions only), retained at
  `OpenAir/System/Agents/{agent}`. `status: starting | online | degraded |
  stub | stopping | offline`. Stub agents report `stub` — the contract makes
  the plan's Phase 0 item 4 permanent by construction, ending health the
  system does not have.
- **H2 — LWT is part of the contract.** The schema ships a
  `heartbeatLwt(agent)` helper returning the exact `{status: "offline"}`
  payload and topic to register as the MQTT Last Will. A heartbeat contract
  without a will is how the browser's `active:true` ghost happens; every
  connecting agent (and the browser) registers it.
- **H3 — Browser sessions are agents.** The `Failover/WEB/Heartbeat/{guid}`
  shape folds into the same schema (`agent: "web/{guid}"`) rather than
  remaining a fourth liveness dialect.

---

## 5. Layout schema (`contracts/src/layout/`)

### What the inventory found

- 478 panel files, two accepted root shapes (wrapper-map vs bare node,
  disambiguated at `LoaderOrchestrator.jsx:45`), **161 distinct `type`
  strings**, dispatched by an exact registry for containers
  (`WidgetFactory.jsx:26-39`) plus an *ordered fuzzy substring cascade* for
  leaves (`FieldComponent.jsx`, first match wins).
- Readers accept two generations of every value pillar: nested
  (`domain.primary.min`, `label.active.text.En`) and legacy flat (`min`,
  `label_active`) — flattened at `FieldComponent.jsx:16-66`. A third label
  generation (`label: {En: ...}`) comes from `build_discovered_gui.py`, which
  also emits a `subscribe` key **no reader anywhere consumes**.
- The editor round-trips whatever is in memory (no schema on write,
  `file_writer.jsx:25-38`) and cannot author `OcaSplit`/`OcaNotebook`/
  `OcaArray` children (its add-path only knows `fields`/`blocks`,
  `Core/state.jsx:91-96`).
- Folder grammar is real parsed syntax: `^(\d+)_` ordering and
  `^(left|right|top|bottom)_(\d+)$` splits (`WindowManager.jsx:12-16,
  280-297`), and the *file path itself becomes the MQTT topic*
  (`topicMaker.jsx`).

### Guidelines

- **L1 — A discriminated union on `type`, with `type` as a closed enum.** The
  schema's node union: containers (`OcaBin`, `OcaBlock`, `OcaArray`,
  `OcaSplit`, `OcaNotebook`, `OcaTable`, …) each with their real key set
  (`blocks`, `fields`, `panels`, `tabs`, `blueprint`/`data`,
  `layout_columns`, `column_sizing`, `behavior`…), plus a leaf-widget schema.
  The widget `type` enum is seeded from the observed-in-use list and, in
  Phase 2, becomes *generated from the typed widget registry* — one source for
  "what widgets exist," killing the fuzzy cascade from the schema side while
  Phase 2 kills it from the dispatch side.
- **L2 — Strict core, explicit legacy profile.** Two validation modes:
  `strict` (the v41 shape: nested `domain`/`value`/`label` pillars only, one
  root shape) and `legacy` (additionally accepts the flat keys and old label
  forms, but *reports each use as a named deprecation*). The validate CLI runs
  legacy mode on day one — the deprecation counts are the technical-debt
  inventory the plan asked for, per file, per key. Keys that nothing reads
  (`subscribe`, stray `widget_type`) are errors even in legacy mode.
- **L3 — The yak binding block is schema'd as it exists:**
  `yak_handler = { enable: boolean, yak_type: 'set'|'rig'|'nab'|'do',
  sub_path, command, input_name?, converter?, marker_number?, trace_number?,
  trigger_only? }` with `converter` drawn from the closed converter enum
  (today: 6 known names, unknown silently passes through —
  `converters.rs`). Cross-field rule: `set`/`rig` require `input_name`.
- **L4 — Folder grammar is a contract surface.** `folder-grammar.ts` owns the
  `N_` prefix rule, the split-name regex, the reserved folder names, and the
  path→topic derivation (the TS twin of `buildGuiPrefix`). It is used by the
  tab engine, the editor's save path, *and* the validate CLI — which can then
  flag prefix collisions and unparseable names in `Gui_Frames` exactly as it
  does in the YAK tree.
- **L5 — Layout `topic`/`shared_topic` overrides must parse.** Any explicit
  topic in a panel file validates against the topic grammar (§2). This is what
  catches `Fleet_Display.json`'s `OPEN-AIR/...` and `System/Control/...`
  orphans at validate time instead of as a dead tab.
- **L6 — The editor is the enforcement point.** Phase 2's save-gate (zod
  validation before `POST /api/save`) uses *this* schema in strict mode — so
  the tree converges: legacy files are flagged read-side, and nothing new
  enters the tree except strict-valid JSON.

---

## 6. YAK schemas (`contracts/src/yak/`)

### What the inventory found

- The live tree (`Gui_Frames/5_Protocols/10_Yak/`, 192 files) is GUI-widget
  JSON, not a command DSL: the parser extracts only
  `{model → {commandName → message}}`, keying model from the **grandparent
  folder name** (misattributing deeper nestings), scanning *every* `.json`
  including nine `temp_norm_*` legacy files and nine `_Legacy_Commands/`
  folders, with md5-identical files across models and a duplicated 34401A
  (`4_DMM_YAK` vs `8_Multimeter_YAK`). Model lookup then ignores all of it:
  `model` is forced to `None` on every execute (`mqtt.rs:77-80`), so every
  command resolves via a search-all-models fallback — global shadowing.
- No ranges, no reply parsers, units only as display metadata
  (`domain.units`). Placeholder syntax is mixed (`<name>` majority, `{value}`
  minority). Numbering collisions: two `4_` classes, two `1_` generators,
  three `2_` power models.

### Guidelines

- **Y1 — Schema both ends of the migration.** `v40-definition.ts` describes
  today's files *just well enough to extract from*: the `Execute Command`
  node shapes (Pattern A and B), `message`, `Input`/`Outputs` `_GuiValue`s,
  `domain.units`. `class.ts`/`model.ts` define the Phase 3 target (capability
  files + dialect bindings + `inherits` + reply parsers). The extraction
  script is then a typed v40→v41 function, not another regex pass.
- **Y2 — Identity comes from file content, never directory position.** Class
  and model files declare `class`, `model`, `inherits` as fields. The
  grandparent-folder heuristic, the `N_` prefix as identity, and the `4_`/`1_`
  collisions all become impossible rather than merely fixed.
- **Y3 — Commands address `class.capability`, globally unique by
  construction.** The capability id (`SpectrumAnalyzer.frequency.center`) is
  the primary key; the schema rejects duplicate capability ids within a class
  and duplicate model bindings — the contract-level end of command shadowing.
- **Y4 — The placeholder grammar is formal.** Canonical form `<ident>`;
  `model.ts` requires every placeholder in a binding template to resolve to a
  declared capability parameter (name + unit + range). The brace forms and
  the "replace first `<...>`" fallback are v40-legacy, reported by validate.
- **Y5 — Units and ranges live on the capability**, as the plan says
  (`{ verb: set|nab, unit: Hz, min, max }`) — converters become declarative
  unit pairs, closing the silent-passthrough enum.
- **Y6 — NAB requires a reply parser.** A capability that supports `nab`
  must declare its reply shape (type, unit, parse pattern) in the model
  binding. Today NAB answers go nowhere; the schema makes the receive path a
  required part of declaring a query, not an optional afterthought.
- **Y7 — The runtime message is a schema too.** `verbs.ts` types the
  `yak_handler` config message and the execute envelope (including
  `correlation_id` — already emitted at `nab.rs`/`rig.rs`/`do_cmd.rs`, unused
  downstream) so the browser, the YAK agent, and the future WASM core share
  one wire contract.
- **Y8 — Exclusion is explicit.** The schema set defines what a *definition
  file is not*: `_Legacy_Commands/`, `temp_norm_*`, `*.old`, `commands_tree.md`
  and loose scripts are non-definitions. The v40 loader ingests all JSON it
  finds; the compiler (Phase 3) and validate CLI both share one include/exclude
  rule from contracts instead of each inventing one.

---

## 7. The `validate` CLI (`contracts/cli/validate.ts`)

Definition of done for Phase 1, expanded from the inventory:

- **Walks** `FrontEnd/Gui_Frames/**` (layout schema, legacy mode) and
  `FrontEnd/Gui_Frames/5_Protocols/10_Yak/**` (v40 YAK schema) — the real
  paths, not the empty `FrontEnd/YAK/`.
- **Reports, per file:** schema errors; legacy-key deprecations (counted, so
  progress is measurable); unknown widget `type` strings; unparseable folder
  names and `N_` prefix collisions; topic overrides that fail the grammar;
  yak_handler blocks with unknown converters or missing `input_name`;
  placeholder/`Input`-field mismatches; byte-identical duplicate definition
  files (md5) and duplicate model definitions (the two 34401As).
- **Also lints the static config surface:** every `config.ini`
  `topic*` value must parse against the topic grammar — which immediately
  surfaces the three-way YAK listen-topic divergence and the declared-but-dead
  `pub/sub/ignore` triples.
- **Exit code** is nonzero on errors (not on deprecations), so it can enter
  CI on day one without blocking on the whole debt list; a `--strict` flag
  flips deprecations to errors as migration milestones land.
- **Output is data first** (JSON report, human summary second) — the day-one
  report is the canonical technical-debt inventory the plan calls for, and
  diffing successive reports is how Phase 2–3 progress gets measured.

CI wiring: a new workflow running `validate`, schema regeneration diff-check
(R3), and `cargo check` on the generated Rust crate — the first non-deploy CI
this repo has had.

---

## 8. Expected day-one findings (so nobody is surprised)

From the inventory, the first `validate` run will at minimum report: the two
34401A definitions and the `4_`/`1_`/`2_` numbering collisions; 9
`temp_norm_*` legacy files (7 of them in md5-identical sets) plus the
LCR-borrowing-Load's-connection-file case; the `Connection_N9340B.json` file
inside the HPE4411A model; mixed `<>`/`{}` placeholders; ~448 typeless
data-set entries and ~50 AES70 data-model `type` strings that need either a
data-set schema or relocation out of the panel tree; the dual root shapes;
thousands of legacy flat-key deprecations (`min`/`max`/`label_active`);
`Fleet_Display.json`'s three dead topics; `build_discovered_gui.py`'s
`subscribe` key and prefix-less topic; and every `config.ini` topic that
diverges from the code. That list is not a reason to soften the schemas —
it is the deliverable.

---

*Method note: this document was produced from four parallel code sweeps
(topics, device records/heartbeats, layout JSON, YAK tree/tooling) over the
v40 codebase on 2026-07-17. File:line citations refer to that revision.*
