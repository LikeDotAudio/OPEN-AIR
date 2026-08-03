# Changelog

## 2026-07-27 - A Command Library Instead Of A Command Table

515 commands became 3656, read out of the instrument manuals we actually own.
Every query now declares what it answers with, every setter what it accepts, and
every command carries its short-form spelling. The device knowledge base stopped
being duplicated.

### The sweep

- **`Documents/Audits/Yak commands missing.md`** — every SCPI command the manuals
  document and the tables did not, as pasteable YAK entries. 2483 of them, 1128
  queries. Written before anything was applied, so the diff between the audit and
  the tables is reviewable rather than a fait accompli.
- **+3141 commands across 12 models.** DS1104Z 73 → 760, Porta_one 35 → 608,
  54641D 113 → 438, the Generators 25 → 254, N9340B 36 → 223, the Power modules
  13-18 → ~190, 34401A 49 → 155, 6060B 28 → 122.
- **NAB went from 95 to 1553.** The tables could set far more than they could read
  back, which is why a panel meter showed a dash while the knob beside it worked.
- **Two PDFs read directly**, after the markdown-only sweep reported both models
  unreachable:
  - `Porta_one` — the markdown was mojibake and I called it unrecoverable. Wrong:
    the PDF has a text layer whose font is offset by a constant **29**. Shift every
    code point back and the document is intact (`DQ\x03IRUP` is `any form`). No OCR.
    573 commands, 286 queries, 311 factory defaults, and the choice lists.
  - `6060B` — a genuine 93-page scan: `pdftotext` returns 93 characters for the
    whole document and `tesseract` is not installed. Read visually, and what is in
    the table is **Table 4-1, "Summary of Commands and Parameters"** — the manual's
    own authoritative list rather than a regex sweep of prose. It also documents
    three aliases worth knowing before binding: `INST`=`CHAN`, `OUTP`=`INP`,
    `FUNC`=`MODE`.
- **Three models remain unreachable**: `3235`, `HP_8903B` and the LCR's own
  programming manual are PDF-only scans with no OCR available. The Router's 24
  panel bindings still name commands that do not exist.

### What a question answers

- **`returns` on all 1553 NAB entries** — `{count, type, unit}`, or one named field
  per answer where the command is **several questions in a row**. 33 are:
  `MODE?;MEAS:VOLT?;MEAS:CURR?;MEAS:POW?` puts four values on the wire and a
  `yak_readout` widget bound to it received one semicolon-joined string with no
  rule for splitting it. `NAB_all_marker_settings` returns **twelve** the same way.
- `count` is exact — the number of `?`, which also correctly ignores the leading
  setter in `INST:NSEL <chan>;MEAS:VOLT?;MEAS:CURR?` (two answers, not three).
- Types are the SCPI response forms the 6060B manual's Tables 2-1 and 2-4 define:
  NR1 / NR2 / NR3 / BOOL / CRD / AARD / BLOCK / ERROR. 43 are the type the 66000A
  dictionary states outright; **429 are left blank rather than guessed**.

### What a setter accepts

- **`arg` on all 1366 SET/RIG entries** — kind (numeric 412, enum 350, bool 158,
  integer 140, block 9, **unknown 291**), plus **350 choice lists**, **433
  defaults**, 222 units, 60 min/max pairs.
- **A range is a property of the instrument, not of the command.** 49 Power setters
  take a voltage; storing min/max on each would be 49 copies of one fact that then
  drift. `arg.domain` points at `model.json`, which is already where panels read
  limits from via `yak_domain`.
- **`limits: "query"` on 87** — the instruments that accept `MIN`/`MAX` as a query
  argument will report their own limits, so nothing has to author them. Verified
  per manual: the 34401A has 286 such forms, the 33220A 119, the 6060B's Table 4-1
  offers it on every numeric query. The Rigol's `MIN` tokens are measurement-item
  names, not limits; the N9340B and 54641D never mention it.
- **`unverified: true` on 3141.** The SCPI is what the manual prints; nothing has
  watched an instrument honour it. `grep -c unverified` per model says how much of
  a table is unproven.

### `scpiFast`

- **The short-form spelling, under the long form, on 2621 commands.** The 6060B
  manual, chapter 2: *"The short form provides the fastest program execution."* It
  also states the construction rule, so this is computed rather than authored — four
  letters or fewer keeps all of them, five or more takes the first four, or the
  first three when the fourth letter is a vowel. That agrees with the mixed-case
  capitals everywhere both exist (`RESistance` → RES, fourth letter a vowel;
  `SOURce` → SOUR, not).
- `repository.rs` reads it, `Command::template(prefer_fast)` picks the form, and all
  four verbs route through `get_scpi_form`. **`prefer_short_scpi` in config.ini,
  off by default** — the long form is what the tables were swept as and what a
  monitor log is readable in.

### One knowledge base, not two

- **`Yak/knownDevices.json`, 181 models** with `{manufacturer, type, notes}`.
  `openair-visa/assets/visa_devices.json` was **byte-identical** to it and is
  deleted; `oa_visa_known_devices/mod.rs` now embeds and resolves the Yak copy.
- **`manufacturer` restored.** It existed in `manager_visa_known_types.py` only as
  section comments, so converting to JSON dropped it and sorting the keys destroyed
  even the ordering that implied it. Kept as the source's own grouping —
  "HP / Agilent / Keysight" is one label because the 34401A was sold under all
  three names as the company changed hands; splitting it would invent a
  distinction the data never made.
- **+39 models**, and two types that did not exist: **LCR** and **Distortion**.
  Five models with YAK command tables were absent from the knowledge base
  entirely, so discovery answered "Unknown Instrument" and the panel builder
  skipped them — including Porta_one, which now has the largest vocabulary here.

### Defects the work exposed

- **Ten hand-authored commands were silently dropped** by the multi-step edit pass
  — three 34401A `CALCulate:AVERage` queries, four 6060B transient setters, three
  54641D trigger-edge setters, and no other name served their SCPI. Restored from
  git. It recurred once after the first restore and the cause is **not identified**;
  `validate_yak_tables.py --snapshot` / `--against` is how it was caught both times
  and is the guard until it is.
- **Nine commands had glued mnemonics** — `SOURce:CURRentLEVel:TRIGgered` is not
  valid SCPI, it is `SOURce:CURRent:LEVel:TRIGgered`, run together where the manual
  broke a line. Four Power models and the N9340B. Those commands could never have
  worked.
- **`subsystem` kept a trailing `?`** on six entries, from building the field off
  the SCPI string without stripping it.

### New tooling

- **`Deployment/validate_yak_tables.py`** — invariant checks (verb matches the
  template's shape, `returns.count` equals the number of `?`, chained queries carry
  one field per answer, enums have choices, no duplicate names or aliased nodes,
  `scpiFast` really is the short form), plus `--snapshot` / `--against` for the
  count regression that needs a baseline. Findings went 518 → 234 as its own
  false positives were fixed and the real defects were repaired.
- `Deployment/build_yak_command_list.py` and `build_yak_command_trees.py`
  regenerate `CommandList.csv` and the per-model `commands_tree.md` views, both
  with `--check`.

### Still open

- **122 enums with no choice list**, 44 of them on the 54641D, whose manual has no
  parameter tables — its choices are inline prose. Nothing can generate a legal
  test value for those.
- **Nothing was added to RIG.** The manuals name arguments inconsistently, so every
  swept parameter is a one-value SET; the multi-argument commands RIG exists for
  are sitting in SET.
- 291 `arg` blocks and 429 `returns` types are `unknown` — a live sweep answers
  both immediately, which is what the `unverified` flag is waiting for.

## 2026-07-27 - Two Files Per Instrument · YAK Commands Become A Table

Both halves of the instrument stack were data pretending to be a GUI. The
authored panels needed five directories to hold five files, because the frontend
builds tabs from folders and the templates had been shaped to match. The YAK
command tables were worse: 176 files shaped like panels, with the actual
model → command → SCPI table *pattern-matched out of them at load*. This makes
each one what it is — panels stay a tree, commands become a table.

### Instruments: two files, no folders

- **`<Type>/<Type>.json` and `<Type>/<Type>_N.json`** — the instrument, and the
  block that repeats. That is the whole layout; 21 directories are gone.
  `Power/Instrument/One_instrument/psu_one.json` was two levels of folder around
  one file, and it rendered as a pointless "One instrument" sub-tab.
- **Sub-tabs come from top-level keys.** `Spectrum.json` holds `amplitude`,
  `bandwidth`, `frequency`, `markers`, `traces`; the builder writes each to
  `0_amplitude/`, `1_bandwidth/` … Key order is tab order. A key holding a MAP of
  panels is one tab with several stacked — the Router's `Coax` tab is two cards —
  which is the same either-a-node-or-a-map test `LoaderOrchestrator` already
  makes on a file's own root. One key and one panel means no sub-tab at all.
  `OaTopicMaker` strips the `<i>_` prefix, so numbering the tabs never moves a
  widget's topic.
- **Header decks live in the N file** as siblings of the `${n}` block, and a group
  spec asks for one by name. Power keeps both of its decks — the bank of eight
  gets the logger, the quads get the master interlock — out of one file.
- **`manifest.json` names neither template path**; both are convention now, and
  `panel`/`unit`/`exclude` are gone with the folders they addressed.
- Verified by building the same simulated bench through the old and new builders:
  52 panel files each way, every MQTT topic prefix and every panel node hash
  identical, one intended difference (Power lost its stray sub-tab).

### YAK: SET, DO, RIG, NAB

- **One `commands.json` per model**, 515 commands across 15 models, bucketed
  under the verb that handles it — so a panel author picks `yak_type` by reading
  the file. Assignment is mechanical from the SCPI: `?` → NAB, no arguments → DO,
  one argument → SET, two or more → RIG. `<chan>`/`<slot>`/`<marker_number>` are
  not arguments; they identify the instance and are stamped per panel.
  Each command carries `description`, `group` and `subsystem`; `scpi` is the only
  field YAK reads.
- **The model is declared, not inferred.** It used to be read off the file's
  grandparent directory, so anything nested deeper than `<Model>/<Subsystem>/`
  was filed under a folder name — `_Legacy_Commands`, `CHANnel`, `Commands` — and
  **391 commands were reachable only through the search-every-model fallback**.
- **555 phantom commands gone.** The extractor matched an `Execute Command` child
  on any key, and every widget wraps its own in a `fields` object, so `fields`
  was filed as a command 555 times — 40% of what loaded.
- **32 silent collisions resolved.** Nothing enforced one definition per name and
  the winner was whichever file `read_dir` returned last. On the Power modules
  that decided between `INST:NSEL <chan>` and `INST:NSEL 1` — between addressing
  your slot and addressing slot 1 whichever module you clicked. Thirteen scope
  commands existed as per-channel copies (`CHANnel1:SCALe`, `CHANnel2:SCALe`, …)
  and collapse to `CHANnel<n>:SCALe`.
- **`<channel>` → `<chan>` throughout.** Only `<chan>` is ever stamped, so a
  template spelled the long way reached `fill_placeholders` unfilled, matched no
  payload key, and the verb refused to send — the module silently never switched
  on. The two spellings were split across the modern and legacy trees.
- **Seven names that covered two subsystems are split** — `Set_Scale` became
  `Set_Channel_Scale` / `Set_Timebase_Scale`, likewise Offset, Range and Mode.
  Nothing bound them yet, and it removes a trap: a panel asking for `Set_Scale`
  had no way to say whether it meant a channel or the timebase.
- **`Multimeter/34401A` folded into `DMM/34401A`** — same model, two family
  folders, and two files declaring model `34401A` would collide at load.
- `repository.rs` reads the declared table instead of walking for panel patterns,
  warns instead of overwriting on a duplicate name, and announces when it falls
  back to another model's command. `yak_crossref.py` reads the tables too.
  `commands_tree.md` and `Raw Commands.txt` stay — hand-written SCPI reference,
  and the source material for the tables still empty.

### Two generated sheets

- **`Yak/CommandList.csv` / `.xlsx`** — 515 rows: verb, command, description,
  arguments, instance params, group, subsystem.
- **`Instruments/Instrument functions.csv` / `.xlsx`** — 221 rows, one per
  control: tab, panel, block path, widget type, and whether it is driven by a
  `yak_handler` or still by literal SCPI (87 / 84, plus 49 unbound).

Both are reports regenerated from the JSON, not sources.

### Still broken, now visible

- **The Router panels have never worked.** 24 bindings to `Set_Relay_Card4` …
  `Set_Relay_Card9`; `Router/3235` offers `Close_Channels` / `Open_Channels` /
  `Select_Channel`. Predates this work. `yak_crossref.py` counts a widget as
  BOUND when it carries a `yak_handler` without checking the command resolves,
  which is why it reports the Router as finished.
- **84 controls still carry literal SCPI** in `message_details.*.command_value`,
  which is inert — only YAK translates and routes. 12 are dead duplicates beside
  a working handler; the rest need binding, and `LCR/4263A` and
  `Distortion/HP_8903B` need a vocabulary written before they can be.

## 2026-07-27 - Instruments Become Instances · YAK Drives Real Hardware · Discovery You Can Watch

A bench with eight 34401As had one DMM tab. Panels were a *display* of an
instrument family, bound to no instrument in particular, and the commands they
carried went to a topic nothing subscribed to. This makes a panel an instance of
a discovered device, gives YAK a way to address that device, and puts discovery
where you can see it happening.

### Per-device instrument panels

- **The authored panels moved out of the frontend** — `FrontEnd/Gui_Frames/1_Instruments/left_50/*`
  → `BackEnd/Instruments/`, one directory per VISA knowledge-base type (`34401A → DMM`).
  They are a template *library* now, not a tab tree. Nothing in the frontend reads
  the directory; `Deployment/build_instrument_panels.py` does.
- **One panel per discovered device**, stamped after every scan into
  `Gui_Frames/1_Instruments/left_100/` (generated, gitignored). Eight meters →
  eight tabs, each bound to its own VISA resource. Folder names carry the
  resource tail (`34401A_44-44-44-111-gpib7-4`) because model alone is not
  identity: all eight report serial `0`.
- **`manifest.json` declares what gets instantiated** — the single-instrument
  variant per type, plus `exclude` for multi-device children that would otherwise
  appear as a sub-tab under every device, plus `groups` that COMPOSE bank views
  from one unit template. `psu_eight.json` was 1183 lines of one module strip
  written eight times, and could not be right about limits because the chassis
  holds four module models; composed, each copy carries its own slot, model and
  ranges. The hand-duplicated bank panels are deleted (29 files), along with 48
  `*.json.old` editor backups.
- **Model capability sheets** (`Yak/<type>/<model>/model.json`) supply channel
  counts and voltage/current domains, so an 8 V module and a 60 V module no
  longer get the same widget. Previously the ranges were English prose in
  `visa_devices.json`.
- **Pruning is stamp-based.** Only directories carrying `.generated-by-openair`
  are removed, so a hand-authored panel dropped into the generated tree survives.

### YAK: commands that reach an instrument

- **`yak_handler` gained `target` and `model`**, stamped per device by the panel
  builder. Every verb published its SCPI to one global topic
  (`OpenAir/System/Protocols/yak/pub`) that **nothing subscribes to** — panels
  have never actually moved an instrument. SCPI now goes to that device's VISA
  `Write` topic as a raw string; hand-authored panels naming no device still use
  the old topic and envelope.
- **Every placeholder is filled, or nothing is sent.** `verbs::fill_placeholders`
  replaces the old "substitute `<input_name>`, else the first `<…>`" logic, which
  turned `APPLy:SINusoid <freq>, <amp>, <offset>` into
  `APPLy:SINusoid 1000, <amp>, <offset>` — a syntax error a panel cannot show you.
  Unresolved arguments now refuse the send and say which are missing.
- **Arguments resolve from sibling widgets.** An authored command block is an
  actuator beside its `Input/*` fields, each publishing to its own topic, so the
  press that fires the command carries only `value: 1`. `mqtt.rs` caches values
  from the `OpenAir/Gui/#` subscription it already held and folds the siblings in
  before dispatch. A named argument beats the actuator's own press value —
  without that ordering every command reads `1`.
- **`params` carry per-instance constants** (`<chan>`, slot selectors), applied
  before value injection so a voltage cannot land in a slot selector and quietly
  command the wrong module.
- **Boolean converters** (`bool_on_off`, `bool_off_on`, `bool_1_0`): a toggle
  publishes `1`, and `:SENSe:VOLTage:DC:RANGe:AUTO 1` is a syntax error on a
  34401A.
- **The Generator template is fully bound** — 25 inline `message` strings became
  handlers (11 `do`, 6 `set`, 5 `rig`, 3 `nab`), with the verb taken from the
  block the command was already filed under. Inline SCPI in a template is inert:
  only YAK translates and routes.
- **The DMM template is bound** (13 widgets) against nine new bare
  `CONFigure:…` commands authored in `Yak/DMM/34401A/Panel/`. The existing
  `Config_*` entries all carry `<range>,<resolution>`, which a mode toggle has no
  way to fill.
- **`yak_readout: true`** points a display widget at its device's `/Read` topic,
  so a query's answer has somewhere to land.

### Discovery you can watch

- **The browser subscribes to the live discovery topics.** `MqttProvider` had
  `OpenAir/Gui/#` only, while discovery tables publish to
  `OpenAir/System/Gui/Discovered/<category>` — so every table was frozen at
  whatever was baked into its panel file at build time.
- **A `_GuiScanActivity` feed** on the Discovered tab shows scan narration and
  device changes as they happen. Scan progress previously existed only in the
  orchestrator's stdout, which is invisible to anyone running the UI.
- **Every discovery agent narrates now**, not just VISA: the discovered-GUI
  watcher diffs the retained tree and announces appearances, disappearances and
  liveness flips to `OpenAir/System/Discovery/Activity`, summarising per category
  above eight changes so a staleness wave does not bury the two that mattered.
- **The watcher is a singleton** (flock). The orchestrator spawns one after every
  scan, so they accumulated — N copies republishing identical rows and narrating
  every change N times.
- **`OcaTable` is read-only.** It passed its node to `useMqttState`, which
  published `<topic>/config` AND, before rows arrived, its own null default over
  the row topic — retained-overwriting the data the agents had just produced.

### Instrument liveness

- **A heartbeat re-verifies one instrument per tick**, round-robin, using the
  same `*IDN?` path the scan uses. `last_online` was stamped only when a scan
  probed an instrument, so the table turned red fifteen minutes after every scan
  whether or not anything had moved. `OPENAIR_VISA_HEARTBEAT_SECS=0` disables it.
- ⚠️ **The first version of this wedged two LAN-GPIB gateways.** It probed the
  transport with a bare TCP connect, which for VXI-11 means knocking on the RPC
  portmapper (port 111). After ~20 minutes of 30-second knocks both gateways
  stopped creating links; every instrument behind them returned `VI_ERROR_IO`,
  to the scanner as much as to the UI, and they needed a power cycle. A directly
  attached instrument on the same network was unaffected, which is what
  identified the gateways as the victim. **No raw-socket probing** — the reason
  is recorded in the code so the cheap-looking version does not come back.

### Naming

- **`10_Yak` → `Yak`, and every `#_` prefix is gone** from the definition tree
  (177 directories): `10_Yak/4_DMM_YAK/1_34401A/1_MEASure/` is now
  `Yak/DMM/34401A/MEASure/`. Model identity is unchanged — `repository.rs` reads
  the grandparent directory and already stripped a leading `N_`.
- **`_YAK` suffixes and `yak_` prefixes are gone** (64 more renames). Verified
  behaviour-neutral: 18 models, 563 commands, identical model names before and
  after. `find_yak_tree()`, both Python tools and `FrontEnd/YAK/yak_renderer.js`
  updated — the renderer was stale twice over, still pointing into
  `ComProtocols/` where the crate no longer lives.

### Tooling

- **`Deployment/yak_crossref.py`** cross-references panel controls against the
  SCPI vocabulary, per instrument family: bound, matchable, control-with-no-command,
  and command-no-control-exposes. Matching is a suggestion, not an authority —
  name similarity cannot know that `Mode_FRES` means four-wire resistance, so
  domain knowledge lives in a curated alias table and everything else is scored
  for a human to judge.

### Known gaps

- Two LAN-GPIB gateways need a power cycle after the heartbeat incident above.
- `Set_Relay_Card4/5/7/8/9` (Router) and `Set_High_Sensitivity` /
  `Set_Power_Gain` (Spectrum) are bound to commands that do not exist in the
  vocabulary — they fail at runtime with nothing but a log line.
- 33 commands are ambiguous: same model, same name, different SCPI, resolved by
  whichever file the directory walk reached last. Most come from
  `_Legacy_Commands/` and `*_OLD.json`.
- `repository.rs` registers a phantom command named `fields` (one per model, 18
  in all) from the `fields:{"Execute Command"}` wrapper. No real command is lost,
  but it is a name that resolves and should not.
- 33210A, 33220A, 6060B and N9340B have no `model.json`, so their widgets ship
  unclamped.

## 2026-07-18 - W1/W2: the Front Door · Path Traversal Fix · One-Command Startup

Executes workstreams **W1** and **W2** of
[strategy to repair current issues.md](Audits/strategy%20to%20repair%20current%20issues.md),
which re-audited the 2026-07-18PM executive review against the working tree.

### 🚨 Security

- **`POST /api/save` was an unauthenticated arbitrary-file-write, reachable
  from any host on the network** (finding N3 — raised by no persona, found
  during the audit and **verified by execution**). The guard was
  `abs_path.starts_with(&gui_frames_dir)`, but `Path::starts_with` compares
  path *components* and never resolves `..`, so
  `Gui_Frames/../../../tmp/x.json` literally begins with the components of
  `Gui_Frames` and passed — the OS then resolved the traversal at `fs::write`
  time and the file landed outside the tree. Replaced with `resolve_within()`,
  which is **structural rather than textual**: every component must be
  `Component::Normal` (rejecting absolute paths, Windows prefixes, and every
  form of `..`), then the target's *parent* is canonicalised and required to
  sit inside the canonicalised base — which also defeats a symlinked parent
  pointing outward. The `.json` check survives as a secondary filter, never as
  the control that keeps writes in the tree. Regression tests cover five
  traversal payloads, absolute paths, and (unix) the symlink case. Same class
  of defect as the VISA injection fixed earlier today: a guard doing string
  matching where it needed structural validation.
- **Nothing binds all interfaces by default any more.** The HTTP server and
  the OSC listener both bound `0.0.0.0` — OSC was the lone outlier among the
  agents (AES70, MIDI, DNS-SD already used loopback), so any host on the
  network could inject OSC events. New `--bind` and `--osc-bind` both default
  to `127.0.0.1`. ⚠️ **Breaking for anyone reaching the UI from another
  machine** — pass `--bind 0.0.0.0` explicitly, and read the help text first:
  loopback is a *mitigation*, not a fix. `/api/save` still has **no
  authentication**, and putting auth in front of the mutating routes is the
  stated prerequisite for widening the bind.
- **A ready-made broker ACL ships as `broker/acl.example`**, separating agents
  (full access), the UI (read-all, write only `Gui/#` and rescan), and a human
  operator (the one credential allowed to publish the VISA `Write` topics that
  execute SCPI on real hardware). Authentication answers *who you are*; this
  answers *what you may do*. `broker/passwd` and `broker/acl` are now
  gitignored. **Not yet enforced** — `allow_anonymous true` still stands, and
  safety still rests on the loopback bind. The template is the policy; turning
  it on is W1-2's remaining half.

### One-command startup (F1 — the revenue gate)

- **`python3 docker/launch.py`** replaces the 7-command quick start that never
  mentioned `corepack`/`pnpm`. Preflights Docker, brings up broker +
  orchestrator, waits for broker health before starting agents, and opens a
  browser. `FrontEnd/Gui_Frames/` is bind-mounted, so panels edited in the
  WYSIWYG editor land on disk and show up in `git diff`.
  The launcher preflights before spending minutes on a build — daemon
  reachable (with a specific hint for the docker-group case), compose v2 with a
  v1 fallback, referenced paths present, ports free — and recognises the
  project's own containers so a second run does not report a bogus port clash.
- **Agents no longer race the broker.** The broker has a `$SYS/#` healthcheck
  and the orchestrator gates on `service_healthy`, replacing the confusing
  retry cascade when agents connected before the broker was accepting.
- **`--host-net` is documented as the mode a real bench needs**, with the
  reasoning: containers sit on a NAT'd bridge, so mDNS multicast never crosses
  it and the VISA subnet scan derives `172.20.0.x` and sweeps a range where no
  instrument lives. Both failures look identical to "no devices found", which
  is why the trade-off is spelled out rather than left to be rediscovered.
  Host mode correctly mounts the *bare-metal* `broker/mosquitto.conf`, since
  with the port mapping gone the bind address is the only confinement left.
- **`--hardware` exposes USB and MIDI** (`/dev/bus/usb`, `/dev/snd` with cgroup
  rules for majors 116/189/180). Bind-mounted rather than declared via
  `devices:`, which resolves once at container start — so hot-plugged
  instruments would never appear and one absent at boot would block startup.
- **The broker host is no longer hard-coded.** `127.0.0.1:1883` appeared in six
  places, which made running the orchestrator in a container impossible — there
  `broker` is a different host. New `--mqtt-host` / `--mqtt-port`, with
  `MQTT_HOST` / `MQTT_PORT` env fallbacks, threaded through the OSC, MIDI,
  AES70, DNS-SD, and VISA agents and the VISA write daemon.

### One bus, one truth (W3-1 and W3-2, pulled forward)

- **OSC and AES70 discoveries reached nothing at all** (F6). Both sent events
  only to the in-process `/ws` broadcast channel, which had **no subscribers** —
  MIDI and VISA were dual-homed onto MQTT and therefore worked. Both now publish
  at QoS 1 to `OpenAir/Protocol/GuiOsc/<addr>` and `OpenAir/Protocol/AES70/<addr>`.
  **Two protocols start working.**
- **The `/ws` route is deleted** — handler, `SystemState`, and `AppState` with
  it. Ordering was deliberate: publishing first, deleting second, or the two
  protocols would have gone from "reaching nothing" to "not existing". This also
  kills N2 — the orphan channel was *why* F6 survived multiple audits, since
  events arrived somewhere, nothing errored, and nothing logged.

### Discovery actually finds instruments

- **VISA mDNS browsed two service types and missed a scope sitting in plain
  sight.** Now browses six, and the load-bearing addition is `_http._tcp`: a
  Rigol advertises only as `rigollan._http._tcp.local.` and was invisible to
  this path despite listening on VXI-11. Second fix — the code trusted the
  *advertised* port and built VISA resources pointing at web servers; an
  advertisement is now only "a host worth probing", and ports 111 (`::INSTR`),
  5025, and 5555 (`::SOCKET`) are probed with a 700 ms timeout. Hosts are
  de-duplicated before probing and browses are stopped via `stop_browse`.
- **The subnet scanner was silently losing devices to its own SYN burst.** It
  spawned 254 threads at once, each racing several connects on a 200 ms budget;
  a Rigol that answers port 111 in 25 ms when probed alone was missed entirely.
  Now chunked at 48 concurrent with a 600 ms timeout — slower scan, no silent
  losses.
- **One instrument no longer appears as several rows.** `list_resources()`
  merged USB + mDNS + subnet output with no de-duplication. Results are now
  stable-sorted `::INSTR` ahead of `::SOCKET` (VXI-11 carries real device
  semantics — timeouts, SRQ, clear — and the subnet scanner pushed SOCKET
  first, so first-wins alone picked the wrong transport), then de-duped. After
  `*IDN?`, duplicates collapse on `(model, serial)` — **but only when the serial
  is usable**, because the bench has four HP 34401A DMMs all reporting serial
  `0` and naive keying would merge them into one device.
- **Ghost rows survive restarts no longer.** The retained-topic cleanup map was
  memory-only, so topics published by an earlier run were never cleared and one
  instrument accumulated stale rows no rescan could remove. `harvest_retained_device_prefixes()`
  now drains retained deliveries at boot and adopts the prefixes it finds.
- **Scan progress is visible to whoever is actually using the UI.** It existed
  only in the orchestrator's stdout — invisible from a browser, doubly so in a
  container. `scan_log()` publishes `{level, message, ts}` to
  `OpenAir/System/Protocols/visa/Scan/Log` (QoS 0, **non-retained** — an event
  stream, so a late joiner does not replay an old scan), and `MqttProvider`
  prints it to the browser console, colour-coded by level and kept off the React
  render path.
- **Discovered rows are tinted by liveness.** Retained state means a device
  unplugged weeks ago still renders, previously indistinguishable from a live
  one. Rows carry `_row_state` (`online`/`offline`/`unknown`, 15-minute window)
  and `OcaTable` tints them. Recency is the primary signal because every agent
  publishes `last_online`, while `connected` is VISA-only — treating its
  *absence* as offline marked every live DNS-SD service red. `unknown` is
  deliberate rather than folded into `offline`: colouring a missing timestamp
  red would assert more than we know.

### Stop describing what we have not built (W2)

- **Ten crates shipped a `cargo new` template asserting `2 + 2`** — but they
  were not one situation, and treating them identically would have wasted
  effort on half. Five (`ember`, `mqtt`, `ptp`, `snmp`, `smpte2138`) are **PyO3
  shims with real sibling modules** behind the non-default `python` feature —
  the template `add()` misrepresented working code as unimplemented, and is
  gone. Five (`mdns`, `nmos`, `rest`, `sap`, `websocket`) are **genuinely
  empty** and are now marked `pub const STATUS = "stub"` with a test asserting
  it, so the status is greppable and implementing one forces a deliberate
  update. `openair-mdns` is recorded as superseded in practice by
  `openair-dnssd`; `openair-websocket` is noted as unrelated to the browser's
  MQTT-over-WebSocket transport.
- **`openair-ember` did not compile at all** — `use pyo3::prelude::*` sat
  ungated at crate root while `pyo3` is optional behind the `python` feature.
  **CI never noticed, because it only checked `-p openair-yak`.** Both BackEnd
  workspaces are now `cargo check --workspace` *and* `cargo test --workspace`;
  the narrow check had also left 10 inline `#[cfg(test)]` modules never
  executed.
- **README Pillar 1 stops over-claiming.** It listed SNMP, Ember+, SMPTE 2138,
  and PTP as devices that "announce themselves and appear in the UI"; all four
  are unimplemented. It now separates **working today** (VISA/SCPI, MIDI,
  DNS-SD/mDNS, AES70, OSC) from scaffolded shims and stubs. The status table
  further down was always honest — the pillar is what people read.

### Layout and defaults

- **The repo root is now only files a tool can *only* find there.**
  `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `.nvmrc`, and
  `requirements.txt` moved to `Deployment/`; `CHANGELOG.md` to `Documents/`.
  Workspace globs point back up with `../`, and every CI job now uses
  `pnpm -C Deployment` and `node-version-file: Deployment/.nvmrc`.
  `rust-toolchain.toml` **cannot** move the same way — rustup searches upward
  from the crate, so it must sit above all three Cargo workspaces.
- **The MQTT default is your own broker, not a public one.** The UI defaulted
  to `test.mosquitto.org` — a public, unauthenticated broker — so a fresh
  install talked to the internet instead of the system it shipped with. Default
  is now this host on `:9001`; the public broker remains as an explicitly
  labelled demo/UI-only preset, and the active preset is highlighted.
- **The two requirements files say why they are not duplicates** —
  `requirements.txt` runs the system, `requirements-deploy.txt` serves the FTPS
  deploy script only, with the `paho-mqtt` bound deliberately identical. The
  install line is corrected to `pip install -r Deployment/requirements.txt`;
  installing the deploy-only file left pyvisa missing and every probe failing.
- **Cache-busters bumped** for `OcaTable.jsx` (v8), `MqttProvider.jsx` (v14),
  and `MqttSettings.jsx` (v3) — these are `text/babel` scripts compiled in the
  browser, so without the bump returning users keep the stale copies and see
  none of the above.

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
  [`contracts/README.md`](../contracts/README.md) (schemas, topic tree, codegen,
  validate/ratchet, and the schema design law that used to live in the
  planning docs), [`BackEnd/ComProtocols/README.md`](../BackEnd/ComProtocols/README.md)
  (the agent fleet with real/stub status, heartbeats + Last Will, discovery
  topics, rescan semantics, how to add a protocol), and
  [`ui/README.md`](../ui/README.md) (the typed frontend and its ratchets).
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
