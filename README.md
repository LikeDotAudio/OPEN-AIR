# 🏷️ OPEN-AIR

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Rust](https://img.shields.io/badge/rust-1.94-orange)
![TypeScript](https://img.shields.io/badge/typescript-strict-3178c6)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

**A software VEE / LabVIEW: an open, vendor-neutral instrument orchestration
environment.** Discover a lab full of instruments across a dozen protocols,
abstract their dialects into one command vocabulary, compose the cockpit out
of ordinary folders, and watch every byte of it flow across a single
observable bus.

---

## 💡 Why OPEN-AIR?

Traditional instrument software is rigid, vendor-locked, and visually dated.
OPEN-AIR bridges raw hardware capability and high-fidelity visualization,
turning a laboratory into a photorealistic cockpit where a fleet of
instruments is orchestrated as easily as a single device.

### The Four Pillars

1. **Discovery across protocols.** **Working today:** VISA/SCPI, MIDI,
   DNS-SD/mDNS, AES70, OSC — devices announce themselves and appear in the UI.
   **Scaffolded but not implemented:** SNMP, Ember+, SMPTE 2138, PTP (PyO3 shims,
   built only with `--features python`) and NMOS, REST, SAP, WebSocket (stubs).
   Stub agents report `status = stub` on the bus rather than claiming health they
   do not have. See [Protocol management](#-protocol-management--discovery).
2. **YAK — the middleware definition plane.** Multiple instruments that do
   the same thing differently are abstracted into one verb grammar
   (`SET / RIG / NAB / DO`), defined as data, not code.
3. **Your folders are your interface.** `FrontEnd/Gui_Frames/` *is* the
   document model: folders become tabs (`N_` prefixes order them,
   `left_50`-style names split panes), JSON files become panels, and the
   in-app WYSIWYG editor saves back into the same tree. Right-click any tab
   to edit its panel.
4. **One observable bus.** Everything — control values, discovery, agent
   liveness, logs — flows over MQTT, so any component or third-party tool can
   watch, inject, log, or replay traffic. `mosquitto_sub -t 'OpenAir/#' -v`
   is a debugger for the whole system.

### The fifth thing that makes the four work: **contracts**

The pillars were always good ideas; what hurt was the absence of agreements
*between* them — every boundary was an unchecked string, and most subsystems
had grown two sources of truth. That is what
[`contracts/`](#-the-contract-layer) fixes, and it is the reason the current
generation of the platform exists.

---

## 🏛 Architecture at a glance

```
                      ┌───────────────────────────────┐
   Browser (React)    │       MQTT broker             │   Rust agents
   ─────────────────► │  1883 (tcp) / 9001 (ws)       │ ◄─────────────────
   panels, widgets,   │  retained topics = the        │  VISA, MIDI, DNS-SD,
   WYSIWYG editor     │  system's state database      │  AES70, OSC, YAK, …
                      └───────────────────────────────┘
            ▲                       ▲                          ▲
            │                       │                          │
            └───────────────┬───────┴──────────────────────────┘
                            │
                   ┌────────────────────┐
                   │    contracts/      │  ONE definition of every
                   │  TS (zod) → JSON   │  cross-boundary shape,
                   │  Schema → Rust     │  shared by all three sides
                   └────────────────────┘

   Orchestrator (Rust/axum, :8000) — serves the UI, GET /api/tree (live
   filesystem → tabs), POST /api/save (editor writes), spawns the agents.
```

---

## 📜 The contract layer

`contracts/` is a single package that owns every shape crossing a process
boundary. It is TypeScript-first (zod), exports JSON Schema, and generates
the Rust types — so the browser, the Rust agents, and the tooling cannot
disagree about the wire.

**Full documentation: [`contracts/README.md`](contracts/README.md)**

| What it defines | Where |
|---|---|
| **Topic grammar** — typed build/parse for the whole `OpenAir/…` namespace, retain class per family, and a classifier for every legacy v40 topic | `src/topics/` |
| **DeviceRecord** — the canonical discovered-device document (one JSON doc per device, stable derived `deviceId`) | `src/device-record.ts` |
| **AgentHeartbeat** — one liveness shape for every agent *and* every browser session, with the MQTT Last-Will helper | `src/heartbeat.ts` |
| **Layout schema** — the panel JSON as it really is: widget-type classification, the `yak_handler` binding block, folder grammar (`N_`, splits) | `src/layout/` |
| **YAK wire contract** — the runtime `yak_handler` message the agent actually receives | `src/yak/verbs.ts` |

Three properties make it more than documentation:

- **Codegen, not copies.** `pnpm gen` runs zod → JSON Schema → `cargo-typify`,
  and CI fails if the committed output is stale. One source, two languages.
- **Golden vectors.** Hand-written behavior (topic grammar, device-ID
  derivation, time conversion) exists twice — TypeScript and Rust — and both
  sides run the *same* vector files (`contracts/vectors/`). A vector added on
  one side fails the other side's CI until implemented.
- **A ratchet, not a cliff.** `pnpm validate` walks every panel, the YAK tree,
  the folder grammar, and every `config.ini`. Day-one drift was **169 errors
  and 2,093 named deprecations** — all baselined in
  `contracts/validate.baseline.json`, so CI fails only on debt that *isn't*
  in the baseline. Old debt is an inventory; new debt is impossible; the
  number only goes down.

```bash
pnpm validate                    # ratchet report (exit 1 on NEW debt)
pnpm validate -- --report json   # the full machine-readable inventory
pnpm gen && pnpm gen:check       # regenerate schemas + Rust; verify freshness
```

---

## 🔌 Protocol management & discovery

Protocol agents are Rust crates under `BackEnd/ComProtocols/`, spawned by the
orchestrator. Each one announces itself, publishes what it finds, and says
honestly whether it is real.

**Full documentation: [`BackEnd/ComProtocols/README.md`](BackEnd/ComProtocols/README.md)**

- **Liveness is data on the bus.** Every agent publishes a retained
  `AgentHeartbeat` to `OpenAir/System/Agents/{agent}` and registers an MQTT
  **Last Will**, so a crashed agent (or a killed browser tab) flips to
  `offline` automatically instead of lying forever. Browser sessions are
  agents too (`web-{guid}`).
- **Stubs admit they are stubs.** Placeholder crates publish
  `status = stub`, never `online` — the system no longer reports health it
  does not have.
- **Discovery flows to the UI as data.** VISA and DNS-SD agents publish
  retained device topics; the Discovered tab renders them as sortable tables
  (`OcaTable`), one row per device, grouped by category — DMM, Oscilloscope,
  Generator, Spectrum, dnssd, midi.
- **Rescan on demand.** The Discovered tab's **RESCAN DEVICES** button
  publishes to `OpenAir/System/Protocols/visa/Device/Rescan`; the VISA agent
  re-probes the fleet, refreshes retained state, and regenerates the panels.
  Retained and zero-value payloads deliberately never trigger a scan.
- **DNS-SD browses continuously.** The `openair-dnssd` agent enumerates every
  advertised service type on the network and publishes each resolved
  instance; vanished services clear their own retained topics.

---

## 🗂 Repository layout

```
OPEN-AIR/
├── contracts/          # THE contract layer — zod schemas, topic grammar,
│                       #   golden vectors, generated JSON Schema + Rust crate,
│                       #   the openair-validate CLI and its ratchet baseline
├── BackEnd/
│   ├── Core/           # orchestrator (axum): /api/tree, /api/save, agent spawn
│   └── ComProtocols/   # one Rust crate per protocol (visa, midi, dnssd, yak, …)
├── FrontEnd/
│   ├── Gui_Frames/     # YOUR INTERFACE: folders → tabs, JSON → panels
│   ├── libControl/     # the widget library (faders, knobs, meters, tables, …)
│   ├── comMQTT/        # MQTT provider + hooks
│   ├── frameLayout/    # loader, widget factory, field dispatch
│   ├── tabManager/     # tab engine, splits, window manager
│   └── editorWYSIWYG/  # in-app panel editor
├── ui/                 # the typed frontend package (Vite + TypeScript) —
│                       #   builds the app today, becomes the runtime at cutover
├── broker/             # mosquitto.conf (1883 + websockets 9001, persistence)
│                       #   + acl.example — the policy for exposing the bus
├── docker/             # the one-command startup path: launch.py, compose,
│                       #   Dockerfile, container broker config
├── Deployment/         # launcher, deploy scripts, discovered-GUI builder,
│                       #   requirements.txt (Python is glue here, not the product)
├── Documents/          # audits (historical analysis) + strategies (historical plans)
└── TESTS/              # protocol test harnesses
```

**Root files are deliberately few, and every one is load-bearing** — each is
found by a tool that only looks in the repo root:

| File | Why it must be at the root |
|---|---|
| `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml` | the pnpm workspace root; `pnpm -r` / `pnpm --filter` resolve from here |
| `rust-toolchain.toml` | rustup searches upward from the crate — this sits *above* all three Cargo workspaces, so one pin covers them all |
| `.nvmrc` | `node-version-file: .nvmrc` in every CI job |
| `.gitignore`, `README.md`, `CHANGELOG.md` | git and GitHub read them from the root |

---

## 🚀 Quick start

**One command. Only Docker required.**

```bash
git clone https://github.com/LikeDotAudio/OPEN-AIR
cd OPEN-AIR
python3 docker/launch.py
```

Then open **http://localhost:8000**.

That preflights Docker, brings up the broker and the orchestrator, installs the
Python VISA dependencies inside the image, waits for the broker to be healthy
before starting the agents, and opens a browser when it is ready. Everything it
uses lives in [`docker/`](docker/README.md); plain
`docker compose -f docker/docker-compose.yml up` works too. `FrontEnd/Gui_Frames/` is bind-mounted, so panels you edit
in the WYSIWYG editor land on your disk and show up in `git diff`.

> **Everything binds to host loopback.** The bus is not a passive transport —
> publishing to the VISA `Write` topics executes SCPI on real instruments, and the
> HTTP API can write panel files. Before exposing any port on a network, enable
> broker authentication and an ACL (`broker/acl.example`) and put auth in front of
> the HTTP API.

<details>
<summary><b>Running without Docker</b> (native toolchain)</summary>

Needs Rust 1.94 (`rust-toolchain.toml`), Python 3, and a `mosquitto` broker
installed on the host.

```bash
# 1. The broker (the spine — start it first)
mosquitto -c broker/mosquitto.conf

# 2. Python deps (the VISA probe path shells out to pyvisa)
python3 -m venv venv && source venv/bin/activate
pip install -r Deployment/requirements.txt
#   plus OS packages pip cannot install — see Deployment/requirements.txt:
#   sudo apt-get install mosquitto mosquitto-clients python3-tk libasound2-dev

# 3. The system
python3 Deployment/openair.py        # launcher: builds the Rust core + starts everything
#   …or run the orchestrator directly:
cargo run --manifest-path BackEnd/Core/Cargo.toml
```

Useful flags: `--bind` (default `127.0.0.1`), `--mqtt-host` / `MQTT_HOST`
(default `127.0.0.1`), `--osc-bind`, `--port`.

</details>

Watch the whole system talk:

```bash
mosquitto_sub -t 'OpenAir/#' -v            # everything
mosquitto_sub -t 'OpenAir/System/Agents/#' -v   # who is alive
```

## 🛠 Development

The repo is a pnpm workspace (`contracts` + `ui`) alongside two Cargo
workspaces (`BackEnd/Core`, `BackEnd/ComProtocols`) and the standalone
`contracts/rust` crate.

```bash
corepack enable && pnpm install   # Node 24 (.nvmrc), pnpm pinned in package.json
pnpm test                         # contracts vector suites
pnpm typecheck
pnpm validate                     # panel/YAK/config drift, ratcheted
cargo test --manifest-path contracts/rust/Cargo.toml   # same vectors, Rust side
pnpm --filter ui build            # the typed frontend bundle
pnpm --filter ui dev              # Vite dev server (proxies /api to :8000)
```

CI (`.github/workflows/contracts-ci.yml`) runs all of the above on every PR:
Node tests, the Rust vector suite, both-workspace compilation, codegen
freshness, and the validate ratchet.

---

## 📈 Status

| Area | State |
|---|---|
| Contract layer (topics, device records, heartbeats, layout, codegen, validate + ratchet) | ✅ Complete |
| Protocol liveness (heartbeats, LWT, honest stub status) | ✅ Complete |
| Discovery → Discovered tab (VISA + MIDI + DNS-SD, tables, rescan) | ✅ Working |
| Live folder tree (`GET /api/tree`) driving the UI | ✅ Complete |
| Typed frontend package (`ui/`) | ✅ Builds the whole app · ⏳ cutover pending |
| YAK 2 capability model (class/model split, reply parsing, WASM core) | ⏳ Planned |
| Device Registry service + supervisor (restart, TTL aging) | ⏳ Planned |
| Native Rust VISA (retire the `python3` subshell) | ⏳ Planned |

Detailed history lives in [`Documents/CHANGELOG.md`](Documents/CHANGELOG.md); every file moved,
retired, or deleted during the migration is recorded in
[`Documents/Strategies/Migration_Ledger.md`](Documents/Strategies/Migration_Ledger.md).

## 📚 Documentation

| Where | What |
|---|---|
| [`contracts/README.md`](contracts/README.md) | The contract layer: schemas, topic tree, codegen, validate/ratchet, and the schema design law |
| [`BackEnd/ComProtocols/README.md`](BackEnd/ComProtocols/README.md) | Protocol agents: what each crate does, discovery topics, heartbeats, adding a protocol |
| [`ui/README.md`](ui/README.md) | The typed frontend package and the migration mechanics |
| [`Documents/Audits/`](Documents/Audits/) | The 2026-07-17 design audit — historical analysis; resolved findings now live in the READMEs above |
| [`Documents/Strategies/`](Documents/Strategies/) | The migration plans — historical; the shipped parts are documented as features above |

---

*Developed by Anthony Peter Kuzub (LikeDotAudio)*

## MIT License

Copyright (c) 2026 Anthony Peter Kuzub

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
