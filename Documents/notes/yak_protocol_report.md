# Report: The YAK Protocol Translator

> **Revised 2026-07-18** against the working tree at `964f9d29e`. The previous
> revision described `openair-yak` as "an empty scaffold … `src/lib.rs` boilerplate
> with a simple `add` function." **That is no longer true** — the crate is a working
> binary with 427 lines across seven modules. §1 has been rewritten from source; the
> historical Python material in §3 is preserved as written because it remains the
> best record of what the reply path used to do.

*Companion to [1_Design_Audit.md](1_Design_Audit.md) (§4.3, §5.3) ·
[2_Architecture_Diagrams.md](2_Architecture_Diagrams.md) (§3, §3b) ·
[1 Plan of attack.md](../Audits/1%20Plan%20of%20attack.md)*

---

## 1. Current state of `openair-yak` — as built

`BackEnd/ComProtocols/openair-yak/` is a **working binary crate**, not a scaffold. It
has **no `lib.rs` at all** — it is a `main.rs` binary, so the `2+2` template finding
that applies to ten sibling protocol crates does *not* apply here.

| Module | Lines | Responsibility |
|---|---:|---|
| `main.rs` | 62 | Boot, config load, MQTT connect |
| `mqtt.rs` | 137 | Subscribe loop, `yak_handler` caching, verb dispatch, heartbeat + LWT |
| `repository.rs` | 123 | Loads the `10_Yak/**` JSON tree into `HashMap<model, HashMap<command, scpi>>` |
| `converters.rs` | 43 | Unit conversion (`mhz_to_hz`, `v_to_mv`, …) |
| `models.rs` | 33 | `YakHandler`, `IncomingMessage` |
| `config.rs` | 29 | Parses `config.ini` |
| `verbs/` | 197 | `set.rs` (58), `rig.rs` (58), `nab.rs` (39), `do_cmd.rs` (38) |

**What now works** (and did not at the time of the original report):

- All four verbs are implemented and dispatched.
- The repository loads from a **runtime-derived path** — the hard-coded phantom path
  that caused it to load zero definitions is gone.
- The agent publishes a retained `AgentHeartbeat` and registers an MQTT Last Will, so
  a killed YAK agent flips to `offline` on its own (`mqtt.rs:40-44`).
- Monitor traffic is published to `{topic}/monitor/out`, which is why
  `CommandRouter.jsx` is the best log viewer in the project — the pattern the design
  audit §4.6 recommends generalizing.
- Unknown converters now emit `log::warn` rather than passing through in silence
  (`converters.rs:24`). Still a hard-coded enum, but no longer mute.

## 2. Defects confirmed in the current tree

These are live findings, each verified by reading the source. They are the reason
§4.3 of the design audit is still open.

### 2.1 The listen topic has *three* competing values

The debt inventory's "three-way YAK listen-topic divergence" is exact:

| Source | Value |
|---|---|
| `config.ini` | `OpenAir/Gui/Protocols/Yak/#` |
| `config.rs:18` (fallback default) | `OpenAir/System/Protocols/yak/sub` |
| `mqtt.rs:46` (**what actually runs**) | `OpenAir/Gui/#` — hard-coded |

`config.topic_listen` is parsed into the struct and then **used zero times**
(`grep` → 0 references). The agent subscribes to a string literal. This is design
audit §4.1 ("two sources of truth") with a third source, and it is why the INI is
described as declared-but-dead.

Nuance the inventory understates: for *this* crate the rest of the triple is **live** —
`topic_publish` has 4 real uses and `topic` has 10. Only `topic_listen` is dead
(hard-coded past) and `topic_ignore` is near-dead (one comparison, `mqtt.rs:55`). Any
fix must therefore delete the *divergence*, not the whole triple.

### 2.2 Model is deliberately `None` on every execute — and now collides

`mqtt.rs:102-104` sets the model to `None` **on purpose**, with a comment:

> *"We no longer guess the model from parts[5] because the GUI hierarchy for
> Instruments doesn't contain it. By leaving it None, verbs will pass `""` to
> `get_scpi()`, which triggers the 'search all models' fallback."*

This was a reasonable local decision. It becomes a correctness bug the moment two
models share a command name — which is exactly the duplicate 34401A
(`4_DMM_YAK/1_34401A` vs `8_Multimeter_YAK/1_34401A`). Whichever loads last wins, silently.

The proper fix is the YAK 2 class/model split (Phase 3, frozen). The **interim** fix
is cheap and should ship at Day 45: `8_Multimeter_YAK/1_34401A/` contains exactly one
file (`1_MEASure/MEASure.json`) against a full tree in `4_DMM_YAK`. Port anything
unique, delete the class, and the collision disappears along with 5
`yak-duplicate-definition` + 1 `yak-duplicate-model` findings.

### 2.3 Still transmit-only — but the hook now exists

Design audit §5.3 stands: no module parses replies. `nab.rs` publishes the query and
returns; there is no receiver, no `Outputs`/`_GuiValue` update path. Grepping the crate
for a reply parser finds nothing.

**What changed for the better:** `nab.rs:25-31` now wraps the outbound command in a
`correlation_id` envelope when `full_id` is present. That is the missing half of the
request/response pair, already on the wire. The reply path is no longer a from-scratch
build — it needs a receiver that matches on `correlation_id` and publishes typed state
back. The Python `yak_receiver.py` described in §3 is the behavioural spec for it.

---

## 3. Historical context (`EVERYTHING.py.LOG`) — preserved

> **Provenance warning.** This section was derived from `EVERYTHING.py.LOG` inside
> `.crawler/`, a 210 MB untracked archive of the previous generation that the Day-14
> plan proposes to evict from the working tree. **Extract anything still needed before
> it goes** — this report is currently the only in-repo record of the reply-path
> design, and §2.3 depends on it.

The `EVERYTHING.py.LOG` file preserves the historical Python codebase of OPEN-AIR. It
reveals that the "Yak Protocol Translator" (`yak_translator.py`, previously
`yakety_yak.py`) was once a central translation layer in the application.

### What it did

The Yak (Yet Another Kommander) Translator acted as an intermediary between the
application's high-level GUI interactions and the low-level VISA Proxy. Its main
responsibilities were to:

1. Load **YAK JSON command definitions** (`yak_repository`).
2. Listen for GUI events over MQTT.
3. Translate those high-level events into **SCPI** strings by substituting parameters
   into predefined templates.
4. Publish the fully-formed SCPI commands to the VISA Proxy's MQTT `Tx_Inbox` for
   hardware execution.
5. Provide a routing layer (`yak_receiver.py`) to handle returning data and update the
   application state cache.

> **Note (2026-07-18):** items 1–4 are ported to Rust and working. **Item 5 was never
> ported** — that is the transmit-only defect in §2.3, and this line is its
> specification.

### How it worked (the verbs)

The YAK protocol was organized into four functional categories ("verbs"), mapping to
two architectural JSON patterns:

1. **NAB (Status/Observation)** — measurements and status queries (e.g. retrieving the
   current voltage). SCPI syntax typically ended with `?`. Used "Pattern A" (Setting
   Construct) containing an `OcaBlock` with `Outputs`.
2. **RIG (System Configuration)** — global instrument settings: Timebase, Trigger,
   Acquisition. Used "Pattern A" where an `Input` field supplied parameters to the
   `Execute Command` actuator.
3. **SET (Component Parameters)** — channel-specific settings such as Vertical Scale or
   Offset (e.g. `:CHANnel1:SCALe <scale>`). Functionally identical to `RIG`.
4. **DO (Execution)** — immediate, parameter-less actions, triggers, or toggles (Run,
   Stop, Auto, Clear). Used "Pattern B" (Action Construct), where `Execute Command`
   directly contained the SCPI message (e.g. `:RUN`) with no nested inputs.

All four survive unchanged in the Rust port, and the verb grammar is explicitly a
*keeper* — design audit §3.3 calls it "the good part."

> **See [yak_verbs.md](yak_verbs.md)** for how the four differ *as built* —
> per-verb walkthroughs of `verbs/*.rs`, the two axes that actually separate them
> (placeholder filling, correlation envelope), and why the vocabulary is worth
> keeping even where two verbs currently share a code path.

### Evolution

The original translation logic lived in `manager_yakety_yak.py`, later deprecated in
favour of `yak_translator.py` and a cleaner object-oriented architecture
(`YakTranslator`, `YakReceiverManager`, `YakTransmitterManager`), before being
refactored into the Rust `openair-yak` crate. Of those three managers, the translator
and transmitter made it across; **`YakReceiverManager` did not**.

---

## 4. Next steps

| Horizon | Action |
|---|---|
| **Day 14** | Extract this report's source material before `.crawler/` is evicted (§3 provenance warning). |
| **Day 45** | Collapse the three-way listen-topic divergence to one contract-validated value (§2.1). Merge the duplicate 34401A and delete `8_Multimeter_YAK` (§2.2). |
| **Phase 3 (frozen)** | YAK 2 class/model split, so capability is defined once and models supply dialect — retiring the `model: None` fallback entirely. Build the receiver against the existing `correlation_id` envelope (§2.3), restoring what `yak_receiver.py` did. Converters move from a hard-coded enum to declared, validated units. |

See [1 Plan of attack.md](../Audits/1%20Plan%20of%20attack.md) for sizing and sequencing.
