> ## 📌 HISTORICAL SNAPSHOT — 2026-07-17 (v40)
>
> Preserved as written. The "current state" diagrams describe v40. The contract layer, live tree, and agent liveness shown as *target* now exist — see [0_README.md](0_README.md#resolution-status).
> How the system works **today**: [`README.md`](../../README.md), [`contracts/README.md`](../../contracts/README.md), [`BackEnd/ComProtocols/README.md`](../../BackEnd/ComProtocols/README.md).

# OPEN-AIR Architecture Diagrams

*2026-07-17 · Companion to [1_Design_Audit.md](1_Design_Audit.md). Diagrams are Mermaid — GitHub, VS Code, and most viewers render them inline.*

---

## 1. Data transfer — as built today (v40)

Two buses, three topic namespaces, and a discovery pipeline that dead-ends.
Dashed red edges are broken or unwired paths.

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
