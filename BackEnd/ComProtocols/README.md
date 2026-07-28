# Protocol agents

One Rust crate per protocol. The orchestrator (`BackEnd/Core`) spawns them;
they announce themselves on the bus, publish what they discover, and say
honestly whether they are real.

**Everything an agent knows reaches the rest of the system as MQTT.** There is
no side channel, no shared memory, no direct call — which is why
`mosquitto_sub -t 'OpenAir/#' -v` is a complete debugger.

> `openair-yak` used to be listed here. It is not a wire protocol — it is the
> definition plane that translates GUI intent into vendor SCPI — so it now lives
> as its own back end at [`BackEnd/openair-yak/`](../openair-yak/), with its own
> Cargo workspace and its own CI invocation.

---

## The fleet

| Crate | Status | What it does |
|---|---|---|
| `openair-visa` | **live** | Scans the subnet/gateways for VISA/SCPI instruments, probes `*IDN?`, categorizes against the knowledge base, publishes retained device topics, and serves live SCPI writes/queries. Re-runs on demand (see [Rescan](#rescan)) |
| `openair-midi` | **live** | Enumerates MIDI in/out ports, publishes device topics, routes note/CC/program/pitch-bend both directions |
| `openair-dnssd` | **live** | Browses DNS-SD/mDNS continuously: enumerates every advertised service type, publishes each resolved instance, clears retained topics when a service vanishes |
| `openair-ravenna` | **live** | Discovers RAVENNA/AES67 streams: browses `_ravenna._tcp`/`_rtsp._tcp`, fetches each session's SDP over RTSP DESCRIBE, and files a stream only once its own SDP says it carries audio |
| `openair-sap` | **live** | The other half of AES67 discovery: passively listens on the well-known SAP multicast groups (UDP 9875) for the raw SDP that Dante-in-AES67-mode pushes, publishes each audio session, and clears it on a SAP deletion or announcement timeout. Listen only — never announces |
| `openair-avb-milan` | **live** | AVB/Milan discovery via AVDECC (IEEE 1722.1) — the only Layer 2 agent: captures raw Ethernet ADP announcements on `91:E0:F0:01:00:00`, decodes entity capabilities and gPTP grandmaster, expires entities on their own `valid_time`. Needs `CAP_NET_RAW`. Ships `avdecc-probe` (find entities) and `avdecc-identify` (blink a device's LED, like Hive's Identify button) |
| `openair-osc` | **live** | OSC agent (UDP) |
| `openair-aes70` | **live** | AES70/OCA parser (`nom`) |
| `openair-ptp` | **live** | Watches PTPv1, PTPv2 and gPTP simultaneously on one NIC (UDP 319/320 + raw Ethernet 0x88F7), correlates Sync↔Follow_Up and the delay exchanges, and publishes one row per PTP port. Needs `CAP_NET_RAW` + `CAP_NET_BIND_SERVICE`. Ships `ptp-monitor` for the live packet view. Never transmits — an Announce could win a BMCA election |
| `openair-snmp` | **live** | SNMP polling |
| `openair-ember` | **live** | Ember+ |
| `openair-smpte2138` | **live** | SMPTE 2138 (protobuf) |
| `openair-mqtt` | config | Broker connection settings consumed by the orchestrator |
| `openair-mdns` | **stub** | 25-line placeholder — publishes `status = stub` |
| `openair-nmos` | **stub** | ″ |
| `openair-rest` | **stub** | ″ |
| `openair-websocket` | **stub** | ″ |

**Stubs tell the truth.** The orchestrator publishes `status = stub` for
placeholder crates rather than `online` (`Core/orchestrator/src/mqtt.rs`).
When a stub becomes real, delete it from `STUB_PROTOCOLS` in the same change
that implements it — as `dnssd` did.

---

## Liveness: heartbeats and the Last Will

Every agent publishes a retained
[`AgentHeartbeat`](../../contracts/src/heartbeat.ts) and registers an MQTT
**Last Will**:

```
OpenAir/System/Agents/{agent}
  {"schemaVersion":1,"agent":"yak","status":"online","version":"0.1.0",
   "startedAt":"…","lastBeat":"…","pid":1234}
```

`status` is a closed enum: `starting | online | degraded | stub | stopping |
offline`. Because the will is registered at connect time, a *crashed* agent
flips to `offline` on the broker within keepalive — no supervisor required,
no ghost that claims health forever. Browser sessions are agents too, as
`web-{guid}`.

```rust
let (topic, lwt) = openair_contracts::heartbeat::heartbeat_lwt("yak", &iso_now, None)?;
mqttoptions.set_last_will(rumqttc::LastWill::new(&topic, serde_json::to_vec(&lwt)?, QoS::AtLeastOnce, true));
```

Watch it: `mosquitto_sub -t 'OpenAir/System/Agents/#' -v`

---

## Discovery

Discovery is **live data on the bus**, not a filesystem generation step. Agents
publish retained topics per device; the Discovered tab renders whatever is
retained.

```
OpenAir/System/Protocols/visa/Device/{type}/{model}/Dev{n}/{key}
OpenAir/System/Protocols/midi/Device/{Input|Output}/Dev{n}/{key}
OpenAir/System/Protocols/dnssd/Device/{service_type}/{instance}/{key}
```

> **Transitional shape.** This is the v40 field-per-topic layout. The contract
> target is one `DeviceRecord` document per device at
> `OpenAir/Discovery/{protocol}/{deviceId}`, published by a Device Registry
> service that ages records out by `lastSeen`. The mapping between the two is
> already written and vector-proven
> ([`contracts/src/device-record.ts`](../../contracts/src/device-record.ts));
> the registry is the next step.

### The VISA knowledge base

`BackEnd/openair-yak/Yak/knownDevices.json` maps model →
`{manufacturer, type, notes}`, and is what turns a bare `*IDN?` string into a
category (DMM, Oscilloscope, Generator, Spectrum…). It used to be duplicated at
`openair-visa/assets/visa_devices.json`; the two were byte-identical, so that
copy is gone and this is the only one. It is **compiled into the binary** as a fallback and
resolved from disk by walking up from the working directory, so it is found
no matter where the process starts. To teach the system a new instrument, add
its model key — no recompile needed when running from the repo.

### Rescan

The Discovered tab's **RESCAN DEVICES** button publishes to:

```
OpenAir/System/Protocols/visa/Device/Rescan      payload {"value":1}   NOT retained
```

The VISA agent then clears the previous scan's retained topics, re-probes,
republishes, and regenerates the Discovered panels. Trigger semantics are
deliberate:

- **retained payloads never trigger** — otherwise every page load and broker
  replay would start a scan storm;
- **zero/false payloads never trigger** — a button release is not a command;
- repeat triggers arriving *during* a scan are coalesced.

---

## Adding a protocol

1. `cargo new --lib openair-<name>` under this directory, add it to the
   workspace members.
2. Give it a `config.ini` with a `topic` key that **parses against the topic
   grammar** — `pnpm validate` lints every one of these.
3. Publish a retained `AgentHeartbeat` and register the Last Will at connect
   (`heartbeat_lwt`). Use `openair-contracts` types; never hand-roll a payload
   shape that already exists.
4. Build topics with the contracts builders, not `format!("OpenAir/…")`.
5. Publish discovery as retained per-device state; publish events
   non-retained.
6. Remove the crate from `STUB_PROTOCOLS` in `Core/orchestrator/src/mqtt.rs`
   once it genuinely works.

## Conventions worth keeping

- **Retain class follows the topic family**, not the call site: device state,
  configs, and heartbeats are retained; control values, monitor traffic, and
  events are not.
- **Empty retained payload = delete.** That is how vanished devices and
  services clear themselves (dnssd `ServiceRemoved`, VISA pre-scan cleanup).
- **rumqttc's sync `Connection::iter()` blocks** — drive it on a dedicated
  thread, and drive it until the queue drains. A bounded drain that stops
  early silently discards publishes (this bug once ate 14 of 16 retained
  protocol statuses).
