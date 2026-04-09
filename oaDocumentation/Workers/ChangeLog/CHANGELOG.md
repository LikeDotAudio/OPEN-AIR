## [V3.1.14] - 2026-04-09
### GUI Manager Logging & Stability
- **Blueprint Validation Fix:** Demoted `FileNotFoundError` (missing blueprint) in `UniversalGuiLoader` from `ERROR` to `WARNING`. This prevents CI/CD log clutter for handled validation failures while maintaining visibility in the UI.
- **Logging Standardization:** Standardized all logs in `oaGuiManager/Core/loader/gui_from_json.py` to use `matrix_log` with the "exactly three emojis" visual grepping rule and bracketed categories (e.g., `[VALIDATION]`, `[BUILDER]`, `[SUCCESS]`, `[CATASTROPHIC]`).
- **Improved Error Visibility:** Enhanced the `Exception` block in `_construct_dynamic_gui` to follow the project's visual standards while preserving full tracebacks via `logger.exception`.

## [V3.1.13] - 2026-04-07
### Cross-Protocol Namespace Hardening
- **ST2138 Reflection Fix:** Modified `smpte2138_bridge_manager.py` to explicitly ignore the `System/` and `Monitor/` namespaces. This prevents internal MIDI status and core telemetry from being mirrored onto the SMPTE 2138 bus.
- **Prefix Guard Implementation:** Added a `Prefix Guard` to the Protocol Router's `get_topic` logic in `dispatch.py`. This prevents the router from incorrectly prepending protocol namespaces (e.g., `MIDI/`) to topics that already belong to the global `System` or `Monitor` namespaces.

## [V3.1.12] - 2026-04-07
### Final Topic Tree Sanitization
- **Tx Namespace Removal:** Permanently removed the automatic `/Tx/` (Acknowledgement) namespace logic from MQTT dispatch. All status and control messages now reside in their primary topic paths to eliminate tree clutter.
- **Redundant OSC Reflection Fix:** Updated `osc_manager.py` and `dispatch.py` to prevent redundant `OSC/` prefixing for `MIDI`, `GUI`, and `System` namespaces. Feedback reflections for these protocols now correctly map to their native topic paths.
- **oaGui Namespace Kill:** Finalized the consolidation of `oaGui` by re-routing its internal source to the unified `OPEN-AIR/GUI` MQTT namespace in the Protocol Router.

## [V3.1.11] - 2026-04-07
### Deep Namespace Sanitization
- **OSC Namespace Exclusion:** Modified `osc_manager.py` and `dispatch.py` to strictly exclude `GUI`, `oaGui`, and `System` namespaces from automatic OSC mirroring. This eliminates redundant `OPEN-AIR/OSC/GUI/...` reflections while maintaining explicit OSC control when an address is provided.
- **Improved Loop Protection:** Hardened the OSC re-transmission logic to better distinguish between functional control intent and protocol-level status mirroring.

## [V3.1.10] - 2026-04-07
### Protocol & Reflection Hardening
- **OSC System Reflection Fix:** Updated `osc_manager.py` to explicitly ignore the `OPEN-AIR/System/` namespace. This prevents system status and monitor messages from being mirrored back to OSC and re-published as reflections.
- **Improved Filtering:** Hardened protocol-level event listeners to better distinguish between functional control topics and system-level diagnostics.

## [V3.1.9] - 2026-04-07
### Final Namespace Consolidation
- **Namespace Mapping:** Updated `mqtt_topic_utils.py` and `topic_calculator.py` to map legacy `oaGui` paths to the standardized `GUI` namespace.
- **Telemetry Alignment:** Fixed an issue where UI telemetry (visibility/geometry) was publishing to `OPEN-AIR/oaGui/`. All telemetry is now unified under `OPEN-AIR/GUI/`.
- **Token Filtering:** Refined topic generation to preserve the `GUI` token while continuing to strip forbidden layout tokens like `display`, `left`, `right`, etc.

## [V3.1.8] - 2026-04-07
### Monitor Observability & Reflection
- **Monitor Reflection Fix:** Updated `strategy.py`, `midi_manager.py`, and `osc_manager.py` to allow self-authored messages returned from the MQTT bus to reach local observers. This ensures protocol-specific monitors (MIDI Dashboard, OSC Activity) correctly "receive themselves" for visual confirmation of global bus delivery.
- **Hardware Gating:** Maintained strict hardware-level echo cancellation by ensuring that while reflections reach monitors, they do not trigger redundant re-transmission to physical devices unless flagged as a settled status update.

## [V3.1.7] - 2026-04-07
### Protocol Mandates
- **Always-Online REST API:** Formalized the `oaComREST` module as a mandatory system service. Removed the ability to disable the API via global state or manual stop requests.
- **Service Resilience:** Enhanced the REST health monitor to automatically restart the local FastAPI worker if the port is cleared, ensuring 100% availability.
- **Auto-Boot Integration:** Updated the core launcher to explicitly start the REST service during the bootstrap sequence.

## [V3.1.6] - 2026-04-07
### Cache & State Hardening
- **Cache Purge Hardening:** Updated `Clear_cache.py` to target all stateful data directories (`oaDataCache`, `oaDataRunningFiles`, `oaDataSplinks`, etc.) to ensure a clean slate for MQTT-driven state synchronization.
- **Structural Integrity:** Integrated `path_initializer` into the purge sequence to automatically recreate a sane directory structure after a nuke.

## [V3.1.5] - 2026-04-07
### GUI Stability & Aggressive Sanitization
- **GUI KeyError Fix:** Updated `router.py` to ensure boot-sequence messages are correctly normalized through the pipeline, resolving `KeyError: 'guid'` in the Command Router.
- **Aggressive Topic Sanitization:** Hardened `ingest.py` to recursively strip redundant protocol prefixes (OSC, MIDI, GUI) from the entire topic path.
- **Pipeline Synchronization:** Unified silent and standard ingestion paths to guarantee metadata consistency for all UI observers.

## [V3.1.4] - 2026-04-07
### Router Logic Refinement
- **Echo Remover Fix:** Refined `dispatch.py` to allow MQTT Broadcast (🚀) and Cache (💾) updates to bypass the self-author filter. This ensures local GUI and internal logic changes are correctly published to the global bus while still preventing hardware-level feedback loops.
- **Topic Visibility:** Exempted Status and Monitor topics from the Echo Remover to ensure system diagnostics are always visible across all nodes.

## [V3.1.3] - 2026-04-07
### GUI Namespace Consolidation
- **Standardized Fallbacks:** Replaced `GENERIC_GUI_TOPIC` and `FALLBACK_TOPIC` with a unified `GUI` namespace in `gui_mqtt.py`.
- **Unified Prefix Detection:** Updated the Protocol Router to map both `OPEN-AIR/GUI` and `OPEN-AIR/oaGui` to the `GUI` logical source.
- **Ingest Resilience:** Enhanced `ingest.py` to support list-based prefix matching for protocols with multiple legacy entry points.

## [V3.1.2] - 2026-04-07
### Router Stability & Path Sanitization
- **Topic Sanitization:** Implemented a recursive prefix filter in `ingest.py` to prevent redundant protocol strings (e.g., `OSC/OSC/`).
- **Namespace Exclusion:** Modified `dispatch.py` to exclude `OSC`, `GUI`, and `Monitor` namespaces from automatic `/Tx/` (Acknowledgement) topic suffixing.
- **Monitor Forensic Fix:** Resolved `AttributeError` in the Monitor class by properly initializing telemetry counters and importing the `time` module.

## [V3.1.27] - 2026-04-09
### Fixed
- **Supervisor Log Scrubbing:** Implemented ANSI escape sequence removal in the `openair.py` supervisor. This prevents "command not found" errors in the terminal caused by the shell misinterpreting console color codes.

## [V3.2.4] - 2026-04-09
### Fixed
- **Test Discovery:** Fixed `ImportError` during automated test runs by ensuring all `Tests` directories and their sub-packages (e.g., `oaComNmos/Core/IS12`) contain mandatory `__init__.py` files. 
- **Package Integrity:** Standardized the presence of package markers across the module tree to ensure reliable `unittest` discovery.

## [V3.2.3] - 2026-04-09
### Fixed
- **Log Noise Reduction (Layout):** Downgraded file-path fallback warnings in `layout_parser.py` to `DEBUG`. This prevents log bloat during GUI construction for directories using numerical file naming.
- **Log Noise Reduction (YAK):** Downgraded YAK repository creation message to `INFO`. 
- **Log Noise Reduction (PTP):** Downgraded PTP permission denied message to `INFO` for non-root users, acknowledging this as a standard deployment state.

## [V3.2.2] - 2026-04-09
### Deprecated & Consolidated
- **oaGui Namespace Deprecation:** Formally deprecated the `oaGui` entry in the Protocol Matrix. 
- **Unified GUI Source:** Consolidated all User Interface traffic into a single logical source: `GUI`.
- **Backward Compatibility:** Maintained auto-mapping for `OPEN-AIR/oaGui` topic roots to the `GUI` source to ensure legacy asset folders and third-party integrations continue to function without modification.
- **Config Cleanup:** Removed redundant `ingest_oagui` and `egress_oagui` keys from `config.ini`.

## [V3.2.1] - 2026-04-09
### Iron Oxide - Phase 2: Stateless Logic
- **High-Speed Manifest Generation:** Replaced Python's `create_manifest` builder with a high-performance native Rust extension (`oaManifestGen_rs`).
- **UUID & Float Offloading:** Moved UUIDv4 generation, epoch timestamping, and aggressive float conversion off the Python GIL into Rust, drastically reducing payload construction latency during heavy `SPLICE/LINK` events.

## [V3.2.0] - 2026-04-08
### Iron Oxide - Phase 1: Zero-Risk Sandbox
- **Universal Rust Gating:** Finalized `oaLoggingGate_rs` integration across all protocols.
- **Global Filter Injection:** Implemented `rust_gate_filter` directly into Loguru's `initialize_logging` pipeline, ensuring every system-wide `logger.debug` or `logger.info` call is evaluated by nanosecond-latency Rust checks before reaching the sinks.

## [V3.1.26] - 2026-04-08
### Enhanced
- **UI Persistence:** Implemented automatic window geometry persistence. The application now saves its window size and screen position upon user exit and restores them on the next boot.
- **Layout Caching:** Integrated `layout_cache.json` for lightweight UI state management, separate from the functional device state cache.

## [V3.1.25] - 2026-04-08
### Fixed
- **Code Integrity (SNMP):** Fixed a critical `IndentationError` in `snmp_manager.py` that caused a system-wide startup crash.
- **Architectural Restoration:** Restored the `routing_matrix` N x N data structure to the `ProtocolRouter` class. This ensures compatibility with diagnostic UI components that require granular cross-point visualization.
- **Boot Stability:** Resolved several cascading instantiation errors during the UI composition phase.

## [V3.1.24] - 2026-04-08
### Fixed
- **SNMP Visibility:** Fixed a bug where SNMP status and activity were missing from the UI when running in Observer mode.
- **Status Reporting:** Moved MQTT status publishing to the base `SNMPManager` class, ensuring consistent reporting across both Bridge and Observer modes.
- **Activity Monitoring:** Standardized activity notification logic to ensure SNMP-originated topics are correctly displayed in the diagnostic UI.

## [V3.1.23] - 2026-04-08
### Fixed
- **Recursive Topic Guard:** Implemented a definitive block in `StateRegistry` (`set_value`) to prevent any topics with repeated protocol segments (e.g., `OSC/OSC/`) from ever entering the cache.
- **Cache Purification:** Updated system initialization to automatically filter and remove legacy corrupted topics during the disk-load phase.
- **Ingest Hardening:** Standardized all ingestion paths (`MQTT`, `DISK`, `EXTERNAL`) to use the new guarded commit logic.

## [V3.1.22] - 2026-04-08
### Fixed
- **State Cache Flush:** Manually purged the corrupted `device_state_cache.json` to eliminate legacy bloated topics.
- **Restoration Guard:** Hardened `gui_state_restorer.py` with a recursion filter to automatically skip any cached topics containing repeated protocol segments (e.g., `OSC/OSC/`).
- **Topic Matching:** Refined restoration logic to correctly replay all valid `OPEN-AIR/` functional state topics while excluding volatile System and Monitor paths.
### Deprecated
- **JSON Lines Sink:** Disabled and deprecated the high-volume JSON Lines (`.jsonl`) logging sink. Structured log files are no longer generated in `oaDataLogs/JsonLines/`.

## [V3.1.21] - 2026-04-08
### Fixed
- **Infinite Loop / Reflection Purge:** Fixed a critical bug where self-authored Status and Monitor messages from MQTT were re-dispatched, causing infinite feedback loops and GUI freezes.
- **Strategy Hardening:** Updated `strategy.py` to tag ALL reflections from MQTT as `IGNORE (REFLECT)`, blocking them from the outbound queue while preserving Firehose visibility.
- **Echo Remover Hardening:** Removed `Status/Monitor` topic exemptions from the `Echo Remover` in `dispatch.py` to ensure reflections are dropped before reaching hardware drivers.

## [V3.1.20] - 2026-04-07
### Enhanced
- **Log Rotation:** Implemented 1-minute file rotation for all application, error, and protocol logs.
- **TOD Timestamping:** Modified log filenames to use Time of Day (TOD) based timestamps in `YYYYMMDDHHMM` format.
- **Log Segregation:** Introduced protocol-specific log routing. Communications for **OSC**, **MIDI**, **MQTT**, **SNMP**, **VISA**, **AES70**, **REST**, **EMBER**, **SMPTE2138**, and the **BROKER** are now stored in dedicated, timestamped folders within `oaDataLogs/Comms/`.
- **Batch Processing:** Updated `BatchLogSink` to dynamically handle rotating file patterns while maintaining high-performance asynchronous writes.

## [V3.1.19] - 2026-04-07
### Fixed
- **Attribute Error Fix:** Restored the `routing_matrix` attribute to the `ProtocolRouter` class.
- **GUI Stability:** Resolved an instantiation crash in the `ProtocolMatrix` GUI component caused by the missing routing matrix data structure.

## [V3.1.18] - 2026-04-07
### Fixed
- **Architectural Purity (State Cache Isolation):** Removed the `State Cache` (DISK/CACHE) as an input source and output destination for the `Protocol Router`.
- **Mirroring Logic:** Finalized the design where `StateRegistry` mirrors state strictly by subscribing to MQTT traffic, decoupling it from the router's internal event pipeline.
- **Boot Optimization:** Removed redundant boot-time ingestion of disk state into the router, further reducing startup log noise.

## [V3.1.17] - 2026-04-07
### Fixed
- **Boot Ingest Optimization:** Switched `DISK` state ingestion to `_ingest_silent` in `StateRegistry`.
- **Log Noise Reduction:** Prevented console log flooding of `[INBOUND] DISK` messages during system initialization while preserving Firehose visibility.

## [V3.1.16] - 2026-04-07
### Fixed
- **Reflection Detection:** Implemented explicit identification of self-authored MQTT reflections in `StateRegistry` and `ProtocolRouter`.
- **Forensic Visibility:** Added `is_reflection` metadata tag to ensure echoes are identifiable in the Firehose and forensic logs.
- **Cache Integrity:** Ensured that MQTT reflections do not trigger redundant local cache writes, preserving purity of the state tree.

## [V3.1.15] - 2026-04-07
### Fixed
- **Topic Bloat / Recursion Guard:** Fixed a critical bug in `dispatch.py` where topics were recursively prefixed (e.g., `OPEN-AIR/OSC/OSC/...`). 
- **Namespace Stripping:** Implemented aggressive root stripping in the `get_topic` helper to ensure clean topic paths.
- **OSC Address Guard:** Prevented forced namespace prefixing for OSC addresses unless explicitly configured in the routing matrix.

## [V3.1.0] - 2026-04-07
### Protocol Behavior & Path Completion
- **Heartbeat Generator:** Implemented dedicated 1Hz asynchronous pulse on `OPEN-AIR/SYSTEM/HB` for system-wide watchdog safety.
- **SPLINKER "Ghost Touch" Logic:** Refined the consumer update engine to handle interaction locking and fader motor "unlock" during active user input.
- **Discovery Protocols:** Completed integration for **SAP** and **Bonjour**, populating the `NMOS/` and `Proxy/` namespaces with live network stream data.
- **Industrial Monitoring:** Hardened the **SNMP** module with Matrix-defined trap triggers and static OID tree translation.
- **Decoupled Control Logic:** Finalized the **SPLICE/LINK/SPLINKER** micro-logic for absolutely decoupled, non-blocking hardware interaction.
- **Ember+ Tree Mirroring:** Optimized high-density parameter scanning with delta-only MQTT publishing.

## [V3.0.0] - 2026-04-07
### Architecture Refinement & Logic Hardening
- **State-Aware Logic Engine:** Formalized transition from "Message Passthrough" to a state-aware engine centered on the Protocol Matrix.
- **Protocol Matrix:** Implemented the central Virtual Patchbay to map topics across protocols without direct coupling.
- **Metadata Hardening:** Ensured every packet is tagged with a consistent `src` identity (Source ID) for robust echo cancellation.
- **Asynchronous I/O:** Verified and refined non-blocking publication paths for MQTT and hardware output drivers.
- **Heartbeat Filter:** Implemented a logic gate between MQTT Storage and State Cache to prevent high-frequency pulse data from bloating the persistent state snapshot.
- **Monitor Telemetry:** Enhanced the Protocol Monitor with real-time PPS, bit-rate, and latency tracking for inbound and mid-stream traffic.

## [20260406.2020.1] - 2026-04-06
### Added
- Implemented N x N Cross-Point Routing Matrix in 'ProtocolRouter' Core and 'CommandRouter' GUI.
- Added granular source-to-destination routing control ("Anything to Anything").
- Integrated loopback prevention (diagonal False by default) while allowing user override.
- Updated 'dispatch.py' to perform cross-point enablement checks before outbound transmission.

## [20260406.2010.1] - 2026-04-06
### Fixed
- Resolved 'ModuleNotFoundError' in MIDI GUI Assets by standardizing imports via the 'oaComProtocols.oaComMidi.Interface' package.
- Updated 'Interface/__init__.py' to export 'get_input_gui' and 'get_output_gui' for robust cross-module access.
- Corrected ProtocolMatrix instantiation error by safely handling 'config' and 'json_path' arguments in the constructor.

## [20260406.2005.1] - 2026-04-06
### Changed
- Modularized the Protocol Router Interface Matrix into a standalone component 'ProtocolMatrix' in 'oaComBroker/Interface/'.
- Refactored 'CommandRouter' to utilize the new 'ProtocolMatrix' component.
- Added a dedicated GUI Asset pointer at 'oaGui/Assets/right_50/bottom_90/3_Commands/1_Router/2_Matrix/' for the Protocol Matrix.

## [20260406.2000.1] - 2026-04-06
### Added
- Protocol Enablement Matrix in 'CommandRouter' GUI for granular control of protocol Ingest and Dispatch.
- Added 'protocol_enablement' state to 'ProtocolRouter' to gate communication traffic.
- Integrated protocol gating into 'router.py' and 'dispatch.py'.

## [20260406.1955.1] - 2026-04-06
### Changed
- Split 'oaComProtocols.oaComMidi/Interface' into 'Input' and 'Output' subdirectories for better organization.
- Updated 'Entry.py' and 'Interface/__init__.py' to reflect the new directory structure.
- Updated relative imports in 'midi_output_generator.py', 'midi_feed.py', and 'midi.py'.
- Added and updated mandatory file headers in the moved Interface files.
- Replaced hardcoded 'LOCAL_DEBUG' flags with dynamic 'is_debug_allowed()' checks across several protocol managers to respect the 'config.ini' debug matrix.

## [20260406.1950.1] - 2026-04-06
### Fixed
- Handled KeyboardInterrupt in UI partition (oaGuiManager) to ensure graceful shutdown without tracebacks.
- Added synchronous shutdown() method to ShutdownCoordinator to handle non-GUI-event-driven termination.

## [20260404.2245.1] - 2026-04-04
- Fixed redundant traceback logging in Bootstrap sequence.
- Standardized shutdown calls in AsyncBootstrapEngine using root.after.
## [20260404.2300.1] - 2026-04-04
- Fixed X11 BadValue (0x0) crashes during UI build and background sync.
- Implemented robust dimension checks in DynamicGuiBuilder, BuilderBackgroundManager, TransparencyMixin, and OverlayManager.

### [2026-04-04 23:35:00] - Bug Fix: X11 BadValue Crash (Geometry Sanitization & Hardening)
- Implemented geometry sanitization in `WidgetContext` to enforce a 1x1 minimum pixel size for all materialized containers.
- Hardened `UniversalGuiLoader` in `oaGuiManager/Core/loader/gui_from_json.py` with 1x1 floor and `try...except` wrapper during builder instantiation.
- Added recursive build guards and `try...except` around `sashpos` calls in `oaGuiBuildShell/Core/directory.py`.
- Enabled `element_gui_builder` debug flag in `config.ini` for enhanced layout tracing.

## [20260406] - 2026-04-06
- Set all debug flags to False in config.ini and updated system version to 20260406.
- Suppressed non-critical logs. Set LOCAL_DEBUG=False project-wide. Refined matrix_log to respect matrix for INFO/SUCCESS. Gated configuration and OSC bridge logs.
- Updated defaults to ensure full debug mode is active on all elements if config.ini is missing. Updated config_defaults.py and config_builder.py.
- Restructured config.ini. Moved [UI] to the top. Added language_selection to [System] section. Updated config_builder.py, config_reader.py, and config_defaults.py.
- Performance Optimization: Reduced router queue timeouts (100ms -> 1ms) and MIDI loop sleep (5ms -> 1ms). Excluded MIDI from router settling to prevent feedback lag. Backgrounded network services in core launcher for faster startup reactivity.
- Fixed test_config failure by updating expected version to 20260406. Updated hardcoded version in oaOchestration/Constants/config.ini.
- Optimized Protocol Router boot reactivity by defaulting FailoverManager to active=True. Excluded Failover heartbeats from router settling to reduce startup noise.

- 20260406.0215.1: Enforced Leadership Mode on boot. Defaulted ProtocolRouter to PRIMARY state and enabled start/stop lifecycle for SMPTE2138BridgeManager.

- 20260406.0220.1: Corrected ImportError in matrix_gate.py by ensuring it calls ensure_compiled() instead of build(). Added more robust error handling for Rust extension compilation.

- 20260406.0225.1: Fixed Command Router UI to display full, structured messages instead of placeholder data by replacing get_dpi_report with get_message_by_utp.

- 20260406.0230.1: Fixed IndentationError in oaComBroker/Core/protocol_router/router.py.

- 20260406.0235.1: Corrected potential UTF-8 encoding issue in router strategy and dispatch files by rewriting them. Ensured all managers are correctly subscribed.

- 20260406.0240.1: Fixed message routing by updating OSC dispatch to handle complex payloads and adding the missing topic-to-OID mapping for center_freq_MHz in the SMPTE2138 bridge.
