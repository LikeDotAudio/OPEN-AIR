# Phase 1 Step 3 Deep Dive — AgentHeartbeat + DeviceRecord: Payload Schemas, Codegen Turn-On, First Live Consumer

*2026-07-17 · Companion to [Phase 1.md](Phase%201.md) §7 (rollout step 3) and
[4_Contracts_Structural_Guidelines.md](4_Contracts_Structural_Guidelines.md)
§3–§4. Steps 1–2 shipped schemas of* behavior *(the topic grammar). Step 3 is
the first* payload *contract — and the first step that changes a running
component (`MqttProvider.jsx`). That is why it gets its own deployment
strategy: the blast radius is no longer zero.*

---

## 0. Ground truth (verified in code, 2026-07-17)

1. **The browser heartbeat has no Last Will.** `MqttProvider.jsx:53-63` builds
   `connectOptions` with `keepalive/reconnectPeriod/connectTimeout` only — no
   `will`. The retained `active:false` tombstone publishes solely from the
   React cleanup (`:122-137`), i.e. on *clean* unmount. A killed tab, crashed
   browser, or dropped network leaves `active:true` retained **forever**.
   MQTT.js supports `will` in the very options object already being built —
   the mechanism is unused, not unavailable.
2. **Heartbeat payload today** (1 Hz, retained, `MqttProvider.jsx:85-93`):
   `{guid, full_id, partition:'WEB', active, start_ts, timestamp}` at
   `OpenAir/System/Failover/WEB/Heartbeat/{guid}` — unix-seconds floats,
   boolean liveness flag. Failover partition election *reads this shape*;
   it cannot simply change.
3. **The VISA record** (orchestrator `main.rs:267-311`): merge object
   `{manufacturer, model, serial, firmware, raw_idn, resource,
   status: "found"|"identified", device_type, notes, last_online(unix secs,
   stamped once), connected: 0|1}` — exploded one-field-per-retained-topic
   under `OpenAir/System/Protocols/visa/Device/{type}/{model}/Dev{n}/{key}`,
   plus empty retained `/Write` and `/Read` topics. Identity is `Dev{n}` —
   scan order.
4. **Codegen is stubbed.** `pnpm gen`/`gen:check` are echoes; `schemas/` and
   `rust/src/gen/` don't exist yet. zod is pinned at 4.4.3 (native
   `z.toJSONSchema`, draft 2020-12). No Rust codegen tool is installed.
5. **Nothing consumes DeviceRecord yet** — its Phase 4 publisher (the Device
   Registry) doesn't exist. Its step-3 "first consumer" must therefore be a
   *proof*, not a runtime: a replay test that maps today's VISA fields
   losslessly into the new shape.

## 1. Rulings this plan bakes in

- **R-A: Additive, dual-topic heartbeat.** The legacy Failover topic, payload,
  and cadence are **untouched** (failover election depends on them). The
  browser *adds*: (a) an MQTT LWT registered at connect, and (b) a second 1 Hz
  retained publish of the new `AgentHeartbeat` shape at
  `OpenAir/System/Agents/web-{guid}`. The legacy channel retires only when
  Phase 2 converts `MqttProvider` and the failover logic together
  (ledger-tracked, not now). Cost: one extra 1 Hz retained topic per session —
  negligible; benefit: the new tree gets real traffic and the ghost-tab bug
  dies on the new channel first.
- **R-B: DeviceRecord ships as schema + mapping + replay proof.** No VISA
  agent changes in this step (that's Phase 4, per the anti-scope-creep rule).
  The deliverable is `mapV40VisaRecord()` in contracts (both languages) with a
  fixture captured from the real merge-object shape, proving lossless
  conversion — the same "prove consumption without rewriting the producer"
  trick as step 2's topicMaker pinning.
- **R-C: The codegen pipeline turns on with these two schemas** — real
  `pnpm gen`, committed `schemas/*.schema.json`, committed
  `rust/src/gen/*.rs` via **cargo-typify (version-pinned)**, and `gen:check`
  becomes a genuine diff gate in CI. Turning it on with two small documents
  (not the huge layout schema) is deliberate: pipeline bugs surface on 40
  lines of schema, not 400.
- **R-D: Boundary conversions are explicit helpers.** `fromUnixSeconds()` →
  ISO-8601 UTC, `deviceIdFor()` implementing the D2 identity rule
  (serial → protocol-native address → **FNV-1a 64-bit content hash** of
  make+model+address, chosen because it is implementable dependency-free and
  identically in TS and Rust). Both are vector-pinned like the grammar —
  two agents deriving different IDs for one instrument recreates the
  duplicate-34401A bug on the bus, so the derivation is a contract, not a
  convention.

## 2. Step-by-step deployment

Each sub-step is one PR-sized commit: CI green before and after, one ledger
row, additive only. Order matters — every row's check exists before the next
row starts.

| # | Deliverable | Check that gates it | Ledger |
|---|---|---|---|
| **3a** | `heartbeat.ts` + `device-record.ts` zod schemas (H1/D1 field sets, closed enums, `schemaVersion: 1`) + shared `time.ts`/`identity.ts` helpers + payload vectors (`vectors/payloads/{AgentHeartbeat,DeviceRecord}/{valid,invalid}/*.json`, including labeled **legacy-v0 samples** of today's Failover payload and VISA merge object) | vitest: every valid vector parses, every invalid rejects, legacy samples classify as v0 by *name* | add row |
| **3b** | Codegen ON: `scripts/gen.ts` (runs via tsx) emits `schemas/*.schema.json` (draft 2020-12); `cargo-typify` (pinned in `package.json` script + CI) emits `rust/src/gen/*.rs`; both committed; `gen`/`gen:check` become real; CI node job runs the diff gate; cargo job compiles `gen` + parses the same payload vectors | `pnpm gen:check` fails on stale output; `cargo test` parses every valid vector through the generated types (this is the typify-fidelity proof) | add row |
| **3c** | `deviceIdFor()` + `fromUnixSeconds()` in TS **and** Rust, vector-pinned (serial case, VISA-resource case, hash-fallback case, unicode/space hostile cases) | both vector suites green — same file, both languages, like step 2 | add row |
| **3d** | `MqttProvider.jsx` (smallest possible additive diff): `will:` block in `connectOptions` targeting `OpenAir/System/Agents/web-{guid}` with retained `{schemaVersion:1, agent, status:'offline', …}`; second 1 Hz publish of the valid `AgentHeartbeat` (status `online`, `partition:'WEB'` carried, ISO timestamps); clean-unmount publishes `stopping` then the LWT shape | **live-broker verification** (the step-3 equivalent of "tests are not enough"): `mosquitto_sub -t 'OpenAir/System/Agents/#' -v` while (1) opening a tab → `online` beats; (2) killing the tab process → broker delivers the LWT `offline` within keepalive (60 s); (3) clean close → `stopping`→`offline`. Legacy Failover topic byte-identical before/after (capture-diff) | add row |
| **3e** | `mapV40VisaRecord()` (TS + Rust) + replay fixture: the exact merge-object JSON → one valid `DeviceRecord`; mapping table: `manufacturer→make`, `device_type→deviceClass`, `raw_idn→rawIdn`, `resource→extra.visa.resource`, `last_online→lastSeen` (ISO), `connected/status→status` enum (`identified`), `Dev{n}` **discarded** in favor of `deviceIdFor()` | both suites prove: no source field dropped (lossless assertion iterates the fixture's keys), output validates against DeviceRecord | add row |
| **3f** | Docs close-out: Phase 1 §7 table row checked, CHANGELOG entry, debt notes (legacy Failover channel + field-per-topic explosion left in place *by design*, retire in Phase 2 / Phase 4) | ledger + changelog rows exist (the standing archive-markers ruling) | add row |

## 3. What step 3 deliberately does NOT do

- No VISA/MIDI agent edits, no Device Registry, no TTL aging (Phase 4 — D4's
  semantics are *documented* in the schema now, enforced later).
- No layout schema, no validate-CLI walking (step 4).
- No `ui/` package, no MqttProvider conversion — the jsx edit is additive
  lines inside the legacy file, revertible by deleting them.
- No retirement of the Failover heartbeat — dual-publish until Phase 2.

## 4. Risks and counters

- **Typify fidelity** (ISO datetime → plain `String`, branded ids flatten,
  closed enums must survive): counter = 3b's rule that the *same payload
  vectors* parse through the generated Rust types in CI; anything load-bearing
  that the schema translation loses gets a vector, not trust.
- **Touching MqttProvider destabilizes v40**: counter = additive-only diff
  (a `will:` key and one `setInterval`), legacy topic capture-diffed
  byte-identical, and the 3d live-broker kill-tab test script recorded in the
  PR description. Rollback = revert one commit.
- **LWT vs. reconnect flapping** (MQTT.js re-registers the will on every
  reconnect; a flappy network briefly publishes `offline`): acceptable — the
  status enum has no in-between, and `lastBeat` disambiguates; noted in the
  schema docs so the Phase 4 supervisor doesn't treat one `offline` blip as a
  crash.
- **cargo-typify availability in CI**: pinned version installed via
  `cargo install --locked` with cache (or a prebuilt-binary action); local
  devs get it from `contracts/README` — and because `rust/src/gen/` is
  committed, *builds never need it*, only regeneration does.
- **Retained ghosts on the new Agents channel from dev experiments**: the LWT
  itself is the cleanup mechanism; a `mosquitto_pub -r -n` one-liner in the
  README is the manual eraser until Phase 4 TTL aging.

## 5. Definition of done — closed out 2026-07-17

- [x] Both schemas exported from `@openair/contracts` with H1/D1 field sets,
      closed enums, `schemaVersion: 1`
- [x] `pnpm gen` writes `schemas/` + `rust/src/gen/`; `gen:check` is a real CI
      diff gate (dedicated `codegen` job, typify 0.7.0 cached); generated Rust
      committed and compiling
- [x] Payload vectors (valid/invalid/legacy-v0) pass in **both** languages,
      including through the generated Rust types (93 TS / 13 Rust assertions)
- [x] `deviceIdFor()` and `fromUnixSeconds()` vector-pinned in both languages
- [x] Browser registers a real MQTT LWT; LWT delivery verified live against
      the local broker with the browser's exact will registration (SIGKILL →
      broker publishes retained schema-valid `offline`); legacy Failover
      channel behavior unchanged. *Residual manual check for Anthony: kill a
      real browser tab and watch `mosquitto_sub -t 'OpenAir/System/Agents/#'
      -v` flip it to `offline`.*
- [x] VISA replay fixture maps losslessly; `Dev{n}` identity provably replaced
      by the D2 derivation in the mapped output
- [x] Ledger rows, CHANGELOG entry, Phase 1 §7 row links here

**Deviations from plan, logged:** (1) crate rule amended — `regress`
(cargo-typify's validation regex engine, no I/O) is now an allowed dependency
of `openair-contracts`, in exchange for Rust-side pattern enforcement on
deviceId/agent/ISO fields; (2) datetime `format` is stripped from the typify
input only, so Rust sees pattern-validated strings instead of chrono types —
the committed JSON Schemas keep `format` for other consumers.
