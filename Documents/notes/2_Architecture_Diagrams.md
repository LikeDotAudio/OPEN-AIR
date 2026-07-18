> ## 📌 HISTORICAL SNAPSHOT — 2026-07-17 (v40)
>
> Preserved as written. The "current state" diagrams describe v40. The contract layer, live tree, and agent liveness shown as *target* now exist — see [0_README.md](../Audits/0_README.md#resolution-status).
> How the system works **today**: [`README.md`](../../README.md), [`contracts/README.md`](../../contracts/README.md), [`BackEnd/ComProtocols/README.md`](../../BackEnd/ComProtocols/README.md).
>
> ### ⚠️ §1 and §4 are now materially out of date
>
> Re-verified 2026-07-18 against `964f9d29e`: the discovery pipeline in **§1 has been
> repaired** (the builder runs, on the right topic, to the right path) and the browser
> now fetches the **live** tree. **[§7 — Current state](#7-current-state--2026-07-18)
> is the accurate picture of today**; §1 is kept only as the "before."

# OPEN-AIR Architecture Diagrams

*2026-07-17 · Companion to [1_Design_Audit.md](1_Design_Audit.md). Diagrams are Mermaid — GitHub, VS Code, and most viewers render them inline.*

> **Location note:** this file, [1_Design_Audit.md](1_Design_Audit.md), and
> [yak_protocol_report.md](yak_protocol_report.md) live in `Documents/notes/`;
> the audit index and the plan live in `Documents/Audits/`. Cross-links between
> the two folders broke twice on 2026-07-18 during reorganisation — they are now
> checked on every push by `Deployment/check_doc_links.py`.

---

## 1. Data transfer — as built at v40 *(superseded — see [§7](#7-current-state--2026-07-18))*

Two buses, three topic namespaces, and a discovery pipeline that dead-ends.
Dashed red edges are broken or unwired paths.

> **Superseded 2026-07-18.** Four of the breaks drawn below are fixed: `BUILDER` now
> runs, subscribes to the correct topic, and writes to a derived path, and the browser
> fetches the live `/api/tree`. The `/ws` edges are still accurate — and worse than
> drawn (§7).

```mermaid
flowchart LR
    subgraph HW["Lab Hardware"]
        SA["Spectrum Analyzer N9340B"]
        DMM["DMM 34401A"]
        MIDIH["MIDI Devices"]
        OCA["AES70 Devices"]
    end

    subgraph ORCH["Rust Orchestrator (one process, port 8000)"]
        VISA["VISA agent (tokio task)"]
        MIDI["MIDI agent (tokio task)"]
        AES70["AES70 agent (tokio task)"]
        OSC["OSC agent (tokio task)"]
        AXUM["Axum HTTP + /ws broadcast"]
        PYSH["python3 -c pyvisa subshell"]
    end

    YAKAG["openair-yak agent (separate process)"]
    BROKER[("MQTT broker 1883 / ws 9001 (external, unmanaged)")]
    BUILDER["build_discovered_gui.py (never runs)"]

    subgraph BROWSER["Browser (React UMD + in-browser Babel)"]
        TREE["WindowManager: folders → tabs"]
        WIDGETS["libControl widgets"]
        MQTTJS["MqttProvider: OpenAir/Gui/#"]
    end

    SA --- VISA
    DMM --- VISA
    MIDIH --- MIDI
    OCA --- AES70
    VISA -->|"shells out per command"| PYSH

    VISA -->|"OpenAir/System/Protocols/visa/Device/... (retained)"| BROKER
    MIDI -->|"OpenAir/System/Protocols/midi/Device/... (retained)"| BROKER
    AES70 -.->|"only to /ws, never MQTT"| AXUM
    OSC -.->|"only to /ws, never MQTT"| AXUM

    BROKER <-->|"OpenAir/Gui/# (control values)"| MQTTJS
    BROKER <-->|"OpenAir/Gui/# + yak pub/monitor"| YAKAG

    BROKER -.->|"✗ wrong topic: subscribes visa/Device/#"| BUILDER
    BUILDER -.->|"✗ wrong path: writes to phantom repo"| TREE

    AXUM -->|"static FrontEnd/ + stale api/tree.json snapshot"| TREE
    AXUM -.->|"live /api/tree exists but is never fetched"| TREE
    MQTTJS --> WIDGETS

    style BUILDER fill:#7a2b2b,color:#fff
    style PYSH fill:#7a2b2b,color:#fff
```

Key reading: discovered devices reach the broker and stop. The Discovered tab
is fed by a filesystem-generation pipeline (`BUILDER`) that is broken four
independent ways, and the browser renders a stale tree snapshot regardless.

---

## 2. Data transfer — target (v41)

One bus. One topic grammar. Discovery is live data; folders are authored UI.

```mermaid
flowchart LR
    subgraph HW["Lab Hardware"]
        DEVS["Instruments (SCPI / MIDI / AES70 / OSC / ...)"]
    end

    subgraph SUP["Supervisor (Rust)"]
        AGENTS["Protocol agents (restart w/ backoff, native VISA — no python subshell)"]
        REG["Device Registry service"]
        TREESVC["Tree service: fs-watch on Gui_Frames"]
        HTTP["HTTP: static + /api (serves UI only)"]
    end

    BROKER[("MQTT broker (managed: config in repo, ws listener 9001)")]

    subgraph BROWSER["Browser (TypeScript + Vite, typed contracts)"]
        DISC["Discovered tab = live widget on OpenAir/Discovery/#"]
        TABS["Folders → tabs (live tree, pushed on change)"]
        WIDGETS["Typed widget registry"]
    end

    YAK2["YAK 2 translator (one Rust/WASM core, runs native + in-browser)"]

    DEVS --- AGENTS
    AGENTS -->|"raw finds: OpenAir/Discovery/raw/{proto}/..."| BROKER
    BROKER --> REG
    REG -->|"canonical retained records + TTL: OpenAir/Discovery/{proto}/{deviceId}"| BROKER
    AGENTS -->|"heartbeats: OpenAir/System/Agents/{name}"| BROKER

    BROKER <-->|"MQTT over WebSocket (only bus to browser)"| DISC
    BROKER <--> WIDGETS
    BROKER <--> YAK2
    YAK2 -->|"vendor dialect (SCPI etc.)"| AGENTS

    TREESVC -->|"tree + change events (over MQTT retained topic)"| TABS
    DISC -->|"'Promote to panel' → POST /api/save"| HTTP
    HTTP --> TREESVC
```

---

## 3. YAK translation — as built today

Two sources of truth meet at runtime on a bare string, transmit-only.

```mermaid
sequenceDiagram
    participant W as Widget (browser)
    participant B as MQTT broker
    participant Y as openair-yak (Rust)
    participant R as YakRepository (10_Yak JSON tree)
    participant V as VISA agent

    Note over R: Loaded at boot from hard-coded WRONG path → 0 definitions
    W->>B: publish OpenAir/Gui/.../config (yak_handler: type=set, command="Set_Center_Freq_MHz", converter="mhz_to_hz")
    B->>Y: cached per-widget yak_handler
    W->>B: publish value (user turns knob)
    B->>Y: execute payload
    Y->>Y: converters.rs: mhz_to_hz (hard-coded enum, silent passthrough on unknown)
    Y->>R: get_scpi(model=None, "Set_Center_Freq_MHz")
    Note over Y,R: model is ALWAYS None → fallback searches ALL models (command shadowing)
    R-->>Y: ":FREQuency:CENTer {hz_value}"
    Y->>B: publish OpenAir/System/Protocols/yak/pub + monitor/out
    B->>V: (VISA proxy path)
    V--xY: reply is NEVER parsed back — no receiver ported from Python
    Note over W: Outputs (_GuiValue) never update via YAK
```

## 3b. YAK 2 — target capability model

Class defines the capability **once**; models supply dialect bindings and
overrides. One definition compiles to one validated artifact consumed by the
same translation core everywhere.

```mermaid
flowchart TB
    subgraph DEF["YAK 2 definitions (TypeScript-schema'd, validated at build)"]
        CLASS["Class: SpectrumAnalyzer — capabilities: frequency.center Hz, frequency.span Hz, amplitude.ref dBm, trace.fetch ..."]
        M1["Model N9340B — bindings: frequency.center → ':FREQuency:CENTer {Hz}'"]
        M2["Model N9342CN — inherits N9340B bindings (delta only)"]
        M3["Model HPE4411A — overrides: trace.fetch → legacy HP syntax"]
        CLASS --> M1
        CLASS --> M2
        CLASS --> M3
    end

    COMPILE["yak-compile: validate + flatten → yak.artifact.json (typed, deduped, legacy folders excluded)"]
    DEF --> COMPILE

    subgraph CORE["One translation core (Rust crate)"]
        NATIVE["native: in the YAK agent"]
        WASM["wasm32: in the browser"]
    end
    COMPILE --> NATIVE
    COMPILE --> WASM

    NATIVE -->|"SET/RIG/NAB/DO → dialect + parse replies → typed state"| BUS[("MQTT")]
    WASM -->|"WYSIWYG preview, offline validation, command dry-run"| EDITOR["Editor"]
```

The verb grammar (SET/RIG/NAB/DO) survives unchanged — it is the good part.
What changes: commands address a **capability** (`SpectrumAnalyzer.frequency.center`)
instead of a per-model string; the reply path exists (NAB answers parse into
typed state and publish back); and the *same compiled artifact + same core*
runs natively and in the browser via WASM, so the editor can validate and
dry-run a panel with no hardware attached.

---

## 4. File structure — today vs. target

```mermaid
flowchart LR
    subgraph NOW["v40 (mixed concerns)"]
        A1["openair.py — launcher"]
        A2["build_discovered_gui.py — orphan"]
        A3["BackEnd/Core — Rust orchestrator + 40-module PyO3 lib (mostly stubs/ghosts)"]
        A4["BackEnd/ComProtocols/openair-* — 10 crates (6 are stubs reporting 'online')"]
        A5["FrontEnd/ — 142 JSX via script tags + 197 window globals"]
        A6["FrontEnd/Gui_Frames — authored UI + YAK defs + legacy junk, all mixed"]
        A7["FrontEnd/api/tree.json — 3.4 MB stale snapshot"]
    end

%% 2026-07-18 corrections to the NOW column:
%%   A2 is no longer an orphan — spawned by orchestrator/src/main.rs:381
%%   A4 is 16 crates, not 10; stubs now publish status = stub, not online;
%%      10 still carry a `cargo new` template lib.rs (5 are pyo3 shims with
%%      real sibling modules; 5 — mdns/nmos/rest/sap/websocket — are truly empty)
%%   A5 is 153 script tags / 154 files / 210 window globals (207 still `any`)
%%   A7 is now only a static-host fallback; the browser fetches the live tree
%%   NEW: contracts/ exists and is the keystone B1 called for

    subgraph NEXT["v41 (one concern per top-level dir)"]
        B1["contracts/ — THE keystone: TS types + JSON Schema + Rust codegen (topics, device records, YAK, layout, heartbeats)"]
        B2["agents/ — Rust workspace: supervisor + protocol agents + registry"]
        B3["yak/ — definitions (classes/, models/) + compiler + translation core (native+wasm)"]
        B4["ui/ — TypeScript + Vite app: widget registry, tab engine, editor"]
        B5["panels/ — Gui_Frames successor: ONLY authored UI, schema-validated"]
        B6["broker/ — mosquitto.conf, ws listener, ACLs (managed, in repo)"]
    end

    A1 --> B2
    A3 --> B2
    A4 --> B2
    A5 --> B4
    A6 --> B5
    A6 --> B3
    A7 -->|"deleted — live tree only"| B4
```

## 4b. Folders-make-tabs (the keeper, made live)

```mermaid
flowchart TB
    FS["panels/ on disk"]
    FS --> W0["0_discovered/ → 'Discovered' tab (special: live widget, not files)"]
    FS --> W1["1_Instruments/ → 'Instruments' tab"]
    W1 --> S1["left_50/ → split pane 50%"]
    S1 --> T1["0_Spectrum/ → sub-tab"]
    T1 --> F1["frequency.json → rendered panel (validated against contracts/layout.schema)"]
    FS -. "fs-watch → retained MQTT tree topic → browser redraws live" .-> BROWSER["Browser tab bar"]
```

Same mental model as today (`N_` prefixes order, `left_50` splits, JSON files
are panels) — but the browser follows the *live* tree, so dragging a folder in
a file manager redraws the dashboard within a second. That is the README's
promise, actually delivered.

---

## 5. The WYSIWYG loop

```mermaid
flowchart LR
    RC["Right-click panel (WindowManager)"] --> ED["Editor overlay (inside live app: real renderer, real MQTT)"]
    ED --> PE["PropertyEditor: edits typed layout nodes (incl. yak binding block)"]
    PE --> VAL["validate vs contracts/layout.schema + YAK artifact (WASM, offline)"]
    VAL -->|ok| SAVE["POST /api/save → panels/... (.old backup)"]
    VAL -->|error| PE
    SAVE --> WATCH["fs-watch → tree topic → every connected browser re-renders"]
    WATCH --> RC
```

Today's loop already has the right shape (edit-in-place, save-to-tree); v41
adds the validation gate — the editor becomes the place where the contracts
are *enforced*, so bad JSON can no longer enter the tree — and the fs-watch
push closes the loop for every connected client, not just the editing one.

---

## 6. Library / dependency map

```mermaid
flowchart TB
    subgraph TODAY["v40 runtime libraries"]
        R18["React 18 (UMD, CDN)"]
        BAB["Babel standalone (in-browser JSX compile — the tax)"]
        ECH["ECharts (graphs)"]
        MQJS["MQTT.js (ws client)"]
        WASM0["hand WASM (panel/screw drawing)"]
        RUSTL["Rust: axum, tokio, rumqttc, midir, rosc, nom, prost, pyo3"]
        PYV["pyvisa (via python3 -c subshell)"]
    end

    subgraph TARGET["v41 — keep the loves, drop the taxes"]
        K1["KEEP React 18 → via Vite (same components, precompiled)"]
        K2["KEEP ECharts, MQTT.js, WASM panels"]
        K3["KEEP Rust crate set; VISA goes native (vxi11/visa-rs or own VXI-11 — already half-built in oa_visa_scanner)"]
        N1["ADD TypeScript + Vite (kills Babel-in-browser, script-tag order, window globals, ?v=N)"]
        N2["ADD zod (runtime validation from the same contract types)"]
        N3["ADD wasm-bindgen build of the YAK core"]
        D1["DROP Babel standalone, pyvisa subshell, PyO3 import-hack layer"]
    end

    R18 --> K1
    ECH --> K2
    MQJS --> K2
    WASM0 --> K2
    RUSTL --> K3
    BAB --> D1
    PYV --> D1
```

Nothing the owner loves is lost: the widgets, ECharts, MQTT, React, the WASM
panel art, and the whole folders-make-tabs model all carry forward. What is
dropped is exactly the invisible tax: in-browser compilation, global-variable
wiring, and the Python subshell inside the Rust hot path.

---

# 7. Current state — 2026-07-18

*Added 2026-07-18, verified against the working tree at `964f9d29e`. This supersedes
§1 as the picture of what runs today. Green = repaired since v40. Red = live defect.*

```mermaid
flowchart LR
    subgraph HW["Lab Hardware — verified live: 17 VISA instruments, 42 mDNS services"]
        DEVS["Instruments (SCPI / MIDI / mDNS)"]
        OCADEV["AES70 / OSC devices"]
    end

    subgraph ORCH["Rust Orchestrator (port 8000)"]
        VISA["VISA agent"]
        MIDI["MIDI agent"]
        DNSSD["DNS-SD agent (real mDNS, was a 2+2 stub)"]
        AES70["AES70 agent"]
        OSC["OSC agent"]
        AXUM["Axum HTTP + /ws broadcast"]
        PYSH["python3 -c pyvisa subshell — RCE"]
    end

    YAKAG["openair-yak (binary, 4 verbs, heartbeat+LWT)"]
    BROKER[("MQTT broker — config in repo, but anonymous on ALL interfaces")]
    BUILDER["build_discovered_gui.py — now spawned, right topic, right path"]
    CONTRACTS["contracts/ — zod schemas, topic grammar, golden vectors, Rust codegen"]

    subgraph BROWSER["Browser — still FrontEnd/index.html (in-browser Babel)"]
        TREE["WindowManager: folders to tabs"]
        MQTTJS["MqttProvider: ws 9001"]
        DISCTAB["Discovered tab: sortable tables + RESCAN"]
    end

    UIPKG["ui/ — typed package, BUILDS the app but is NOT served"]

    DEVS --- VISA
    DEVS --- MIDI
    DEVS --- DNSSD
    OCADEV --- AES70
    OCADEV --- OSC

    VISA -->|"retained device records"| BROKER
    MIDI -->|"retained + heartbeat"| BROKER
    DNSSD -->|"retained + heartbeat"| BROKER
    AES70 -.->|"only to /ws — NOBODY LISTENS"| AXUM
    OSC -.->|"only to /ws — NOBODY LISTENS"| AXUM
    AXUM -.->|"zero subscribers"| VOID(["dev/null"])

    BROKER --> BUILDER
    BUILDER -->|"writes panel JSON to Gui_Frames/0_discovered"| TREE
    BROKER <--> MQTTJS
    BROKER <--> YAKAG
    BROKER -->|"any host on 1883 can publish"| PYSH
    VISA --> PYSH

    AXUM -->|"live GET /api/tree"| TREE
    MQTTJS --> DISCTAB
    CONTRACTS -.->|"generates + validates"| YAKAG
    CONTRACTS -.->|"generates + validates"| BROWSER
    UIPKG -.->|"imports 146 untouched .jsx via legacy.ts"| BROWSER

    style PYSH fill:#7a2b2b,color:#fff
    style VOID fill:#7a2b2b,color:#fff
    style BROKER fill:#7a2b2b,color:#fff
    style CONTRACTS fill:#1f5c2e,color:#fff
    style DNSSD fill:#1f5c2e,color:#fff
    style BUILDER fill:#1f5c2e,color:#fff
    style DISCTAB fill:#1f5c2e,color:#fff
```

**What the diagram says that the v40 one did not:**

1. **`contracts/` exists and is load-bearing.** The keystone drawn as `B1` in §4's
   target column is real: it generates the Rust the agents compile against and is
   enforced in CI. This was the audit's central recommendation.
2. **The discovery pipeline is repaired but the wrong shape.** `BUILDER` now runs
   correctly — and still routes live data through a filesystem-generation step. The
   §2 target (Discovered tab as a live widget on `OpenAir/Discovery/#`) is unbuilt.
3. **`/ws` is a bus with zero subscribers.** Only two references exist in the whole
   tree: the route at `orchestrator/src/main.rs:420` and a comment in
   `contracts/src/topics/legacy.ts:21`. MIDI and VISA are dual-homed to MQTT and
   survive; **AES70 and OSC are not, so their discoveries reach nothing at all.**
   §1 drew this as "two buses" — it is really one bus and one drain.
4. **The Python subshell is now the top security defect, not just a tax.** The quote
   escaping at `main.rs:552` is bypassable by a trailing backslash, the payload comes
   raw off MQTT, and `broker/mosquitto.conf:20` sets `allow_anonymous true` with no
   `bind_address` → unauthenticated RCE from any host that can reach port 1883.
5. **`ui/` is drawn as a dotted feeder, not a replacement.** It bundles the whole app
   only by side-effect-importing 146 untouched `.jsx` files through `legacy.ts`. Zero
   modules are actually converted, and `FrontEnd/index.html` is still what is served.

## 7b. Distance from here to the §2 target

| Target element (§2) | Status |
|---|---|
| One topic grammar | ✅ Exists and is enforced |
| Agent heartbeats on the bus | ✅ Real, with MQTT Last Will, live-verified |
| Managed broker config in repo | 🔄 Config is in repo — but anonymous and unbound |
| Native VISA, no python subshell | ❌ Phase 4; the *injection* is fixed at Day 14 |
| Discovery as live retained records | ❌ Still filesystem-generated |
| Device Registry + TTL | ❌ Unbuilt |
| Restart with backoff | ❌ Unbuilt — liveness is *detected*, not *acted on* |
| Typed browser (Vite) | 🔄 Builds, not served, 0 modules converted |
| Live tree pushed on change | 🔄 Live fetch works; fs-watch push unbuilt |
| One bus only | ❌ `/ws` survives |

The honest summary: **the specification layer arrived; the runtime topology has not
moved much.** §2 remains the target, unchanged.
