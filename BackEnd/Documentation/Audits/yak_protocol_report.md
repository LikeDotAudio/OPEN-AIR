# Report: The YAK Protocol Translator

## Current State of `openair-yak`
Currently, the directory `/home/anthony/Documents/OPEN-AIR/BackEnd/ComProtocols/openair-yak` is an empty scaffold for a Rust project. 
- It contains a basic `Cargo.toml` file (v0.1.0) and a `src/lib.rs` boilerplate with a simple `add` function. 
- The `config.ini` file indicates that this module is intended to run as a microservice on the system's MQTT message bus, subscribing to `OpenAir/System/Protocols/yak/sub` and publishing to `OpenAir/System/Protocols/yak/pub`.

## Historical Context (`EVERYTHING.py.LOG`)
The `EVERYTHING.py.LOG` file preserves the historical Python codebase of OPEN-AIR. It reveals that the "Yak Protocol Translator" (`yak_translator.py` and previously `yakety_yak.py`) was once a central translation layer in the application.

### What It Did
The Yak (Yet Another Kommander) Translator acted as an intermediary between the application's high-level GUI interactions and the low-level VISA Proxy. Its main responsibilities were to:
1. Load **YAK JSON command definitions** (`yak_repository`).
2. Listen for GUI events over MQTT.
3. Translate those high-level events into **SCPI (Standard Commands for Programmable Instruments)** strings by substituting parameters into predefined templates.
4. Publish the fully-formed SCPI commands to the VISA Proxy's MQTT `Tx_Inbox` for hardware execution.
5. Provide a routing layer (`yak_receiver.py`) to handle returning data and update the application state cache.

### How It Worked (The Verbs)
The YAK protocol was organized into four main functional categories (or "verbs"), which mapped to different architectural JSON patterns:

1. **NAB (Status/Observation)**: 
   - Used for measurements and status queries (e.g., retrieving the current voltage). 
   - SCPI Syntax typically ended with a `?`.
   - Used "Pattern A" (Setting Construct) containing an `OcaBlock` with `Outputs`.

2. **RIG (System Configuration)**: 
   - Used for global hardware instrument settings, such as Timebase, Trigger, and Acquisition configurations.
   - Used "Pattern A" (Setting Construct) where an `Input` field provided parameters to the `Execute Command` actuator.

3. **SET (Component Parameters)**: 
   - Used for channel-specific settings, like Vertical Scale or Offset (e.g., `:CHANnel1:SCALe <scale>`).
   - Functionally identical to `RIG`, utilizing parameterized `Input` fields.

4. **DO (Execution)**: 
   - Used for immediate, parameter-less actions, instant triggers, or toggles (e.g., Run, Stop, Auto, Clear).
   - Used "Pattern B" (Action Construct) where the `Execute Command` object directly contained the SCPI message (e.g., `:RUN`) with no nested inputs.

### Evolution
The architecture was actively undergoing modernization. The original translation logic existed in a file called `manager_yakety_yak.py`. Over time, this was deprecated and migrated to `yak_translator.py`, establishing a cleaner object-oriented architecture (`YakTranslator`, `YakReceiverManager`, `YakTransmitterManager`) before presumably being refactored entirely into the Rust `openair-yak` crate you are building today.
