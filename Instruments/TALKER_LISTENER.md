# The Talker / Listener Pattern

**Status:** implemented end-to-end for `Spectrum/` (N9340B verified against hardware). This document is how to apply it to every other instrument in this directory.

---

## The idea

A control declares **what quantity it is**. That one identity serves both directions:

- It **talks** — sends its command when the operator moves it.
- It **listens** — receives the instrument's reported value for that same quantity.

The two halves stay **decoupled**. A talker does not know who listens; a listener does not know who talked. Anything can subscribe to a reading later — a second panel, a graph, a logger, a limit checker — without the writer changing at all.

## Why it exists

A panel that only sends is a panel that drifts. Setting centre frequency moves start, stop and span on the instrument, and nothing told the GUI — so the sliders showed authored defaults (500 MHz) while the hardware sat somewhere else entirely (800 MHz). Worse, a control that never hears back cannot notice when its command did not land. A 0.3 MHz button once set an instrument to 0.3 Hz — a factor of a million — and the panel displayed 0.3 MHz throughout, because nothing ever asked.

**Verification falls out of listening.** The reading arrives under the same name and in a declared unit, so a control can compare what came back with what it asked for. That comparison is the check that catches the wrong-by-a-million class of bug the moment it happens.

---

## How a reply becomes readings

```
control talks ──► YAK ──► VISA daemon ──► instrument
                                              │
                            reply + the query that caused it
                                              ▼
                                      <device>/Reply
                                              │
                    YAK: look up the command, read its `returns` block,
                         split the reply, attach each field's unit
                                              ▼
                  <device>/Reading/<command>/<field>   (retained, ControlValue)
                                              │
                          every control with a matching `yak_listen`
```

Four properties matter:

1. **A reply is attributed.** `/Read` carries a bare string, so replies on one device overwrite each other — the VISA heartbeat's `*IDN?` lands on top of a frequency answer. `/Reply` pairs the answer with the query that caused it, which is what makes decomposition possible at all.
2. **Readings are named, not indexed.** An index into a joined string points at the wrong quantity the day a `returns` block gains a field, and does so silently. A name cannot drift that way.
3. **Readings are retained.** A panel opened an hour later finds the instrument's last answer waiting, rather than a blank control.
4. **Readings carry their unit.** The transmitter declares; the receiver scales. See `contracts/src/control-value.ts`.

---

## What you author

### 1. The command table — `Instruments/<Family>/<Model>/commands.json`

A query declares the shape of its reply. **This already exists on all 1,553 NAB commands** — what is usually missing is `unit`.

```jsonc
"bandwidth_settings": {
  "scpi": ":SENSe:BANDwidth:RESolution?;:SENSe:BANDwidth:VIDeo?;:SENSe:SWEep:TIME?",
  "returns": {
    "count": 3,
    "separator": ";",
    "fields": [
      { "name": "resolution", "type": "NR3", "unit": "Hz" },
      { "name": "video",      "type": "NR3", "unit": "Hz" },
      { "name": "time",       "type": "NR3", "unit": "s"  }
    ]
  }
}
```

- **`unit` is the field that makes a reading usable.** Without it a listener receives a number with no meaning and can only display it raw.
- **Omit `unit` for booleans and enums.** A dimensionless value carries no unit rather than a placeholder one — `""` reads as "unknown", which is a different fact.
- A single-value query needs no `fields`; it publishes under its own command name, using `returns.unit`.
- Prefer ONE compound query per panel over several single queries: one round trip, one reply, and every control on the panel updates together. The N9340B already ships `Frequency_settings`, `amplitude_settings`, `bandwidth_settings` and `all_marker_settings` for exactly this.

### 2. The panel — `Instruments/<Type>/<Type>.json`

Author the **template**, never the generated instance under `FrontEnd/Gui_Frames/1_Instruments/` — that is regenerated per discovered device and your edit will be overwritten.

```jsonc
"center_freq_MHz": {
  "type": "_Horizontal_with_dial_Value",
  "units": "MHz",                                  // what this control DISPLAYS

  "yak_handler": {                                 // ── TALKER
    "yak_type": "set",
    "command": "Set_Center_Freq_MHz",
    "converter": "mhz_to_hz",
    "readback": "Frequency_settings"               // ask what actually stuck
  },

  "yak_listen": "Frequency_settings/center"        // ── LISTENER (by name)
}
```

That is the whole binding. `yak_listen_topic` is stamped per device by `instruments.rs`; never write it by hand.

**Rules that are not optional:**

- **Only scalar controls listen.** A toggler picks between authored options; the instrument cannot hand one back. Give it a `readback` so its siblings update, but no `yak_listen`.
- **A listener never publishes.** Hydration is the instrument telling the panel where it is. If a control echoed it, the value would return through YAK as a fresh command and the panel would command the instrument to the value it just reported — forever.
- **`readback` on the talker, not the listener.** Any control that writes should name the query that confirms it. Several controls naming the same query is normal and cheap: identical queries coalesce in the write queue.

---

## Applying this to a new instrument

1. **Find or add a compound query per panel.** `cargo run -- list` in `openair-yak` prints the reply columns for every command; a blank `Return unit` column is the work.
2. **Declare `unit` on every numeric field.** This is the bulk of the effort — 20% of queries tree-wide currently declare one.
3. **Add `readback` to every `set`/`rig` handler** on that panel, naming the compound query.
4. **Add `yak_listen: "<command>/<field>"` to each scalar control**, and make sure the control declares the `units` it displays.
5. **Regenerate and verify**: restart the orchestrator, then

   ```bash
   mosquitto_pub -h 127.0.0.1 -t '<device>/Write' -m '<the compound query>'
   mosquitto_sub -h 127.0.0.1 -t '<device>/Reading/#' -v -W 5
   ```

   Every field should appear under its own name with its unit. If YAK logs
   `no command in <model> matches reply to: …`, the SCPI in the table does not
   match what went on the wire — usually a long/short form mismatch.

## Coverage today

| | |
|---|---:|
| NAB commands across 16 models | 1,553 |
| declaring a `returns` block | 1,553 (100%) |
| declaring a **unit** | 307 (20%) |

The structure is everywhere; the units are not. That gap is the migration.

| Instrument | Compound queries | Units declared | Talker/Listener wired |
|---|---|---|---|
| `Spectrum/` | ✅ 4 (freq, amplitude, bandwidth, markers) | ✅ | ✅ 23 talkers, 14 listeners |
| `DMM/`, `Power/`, `Load/`, `Generator/`, `Oscilloscope/`, `Counter/`, `DAQ/`, `Distortion/`, `LCR/`, `Router/`, `SMU/`, `VNA/` | mostly single-value | partial | not yet |

---

## Reference

| Piece | Where |
|---|---|
| Reply decomposition, reading topics | `BackEnd/openair-yak/src/readings.rs` |
| `returns` parsing, SCPI→command lookup | `BackEnd/openair-yak/src/repository.rs` |
| Readback dispatch after a write | `BackEnd/openair-yak/src/verbs/mod.rs` (`dispatch_readback`) |
| `/Reply` publication | `BackEnd/Core/orchestrator/src/main.rs` (VISA write worker) |
| `yak_listen_topic` stamping | `BackEnd/Core/orchestrator/src/instruments.rs` (`bind_readout`) |
| Listener + unit conversion in the GUI | `FrontEnd/comMQTT/MqttProvider.jsx` (`window.OaUnits`, `useMqttState`) |
| Value envelope (value/unit/ts/origin) | `contracts/src/control-value.ts` |
