## [V3.3.8] - 2026-04-26
### Fixed
- **TestsUI AttributeError:** Resolved `AttributeError: 'function' object has no attribute 'identify_test_directories'` in `oaTests/Interface/TestsUI.py` by correcting the shadowed import and usage of `identify_test_directories`.
## [V3.3.7] - 2026-04-16
### Fixed
- **WYSIWYG Menu Bindings:** Resolved `AttributeError: 'WysiwygEditor' object has no attribute '_save_and_close'` by implementing the missing method in the main controller.
- **Core Test Restoration:** Corrected `ModuleNotFoundError` in `test_core_components.py` by aligning import paths and mock patches with the recent `overlay_manager` modularization.

## [V3.3.6] - 2026-04-16
### Fixed
- **TreeRefactor Initialization Race:** Resolved `AttributeError: 'TreeRefactor' object has no attribute '_last_clean_path'` by reordering the constructor sequence. All internal state variables are now defined before triggering any downstream logic or UI updates.
- **Boot Stability:** Ensured standard attribute availability for all UI components during the bootstrap sequence.

## [V3.3.5] - 2026-04-16
### Fixed
- **UI Path Resolution Hardening:** Resolved systemic focus synchronization failures across `JsonEditor`, `ElementProperties`, and `TreeRefactor` caused by inconsistent path formatting (e.g., leading dots or missing root keys).
- **Unified Normalization Logic:** Implemented a robust path-cleaning heuristic that standardizes dot-notation and automatically resolves root-key mismatches based on the current state.
- **Tree View Sync:** Enhanced `TreeRefactor` to visually mirror selections made in the interactive layout by subscribing to global focus events and implementing automatic node expansion.

## [V3.3.4] - 2026-04-16
### Fixed
- **WYSIWYG Editor ModuleNotFoundError:** Resolved `ModuleNotFoundError: No module named 'oaGuiEditorWYSIWYG.Interface.Core'` caused by broken relative imports after the `Interface` directory reorganization.
- **Import Standardization:** Surgically updated `oaGuiEditorWYSIWYG/Interface/overlays/selection.py` to point to the new `layout_engine` location.
- **Test Suite Hardening:** Updated absolute import paths and patch targets in `Tests/Core/test_snap_logic.py` and `Tests/test_core_components.py` to align with the new modular hierarchy.

## [V3.3.3] - 2026-04-15
### Critical System Recovery & Protocol Initialization Fixes
- **Syntax Error Remediation:** Fixed multiple `SyntaxError: unterminated string literal` and `unterminated f-string literal` across `oaComManager` and all protocol `Entry.py` modules (Midi, REST, SMPTE2138, SNMP, NMOS) caused by inappropriate newlines in print/log calls.
- **Architectural & Path Corrections:** Fixed `project_root` calculation in `oaComManager` to correctly point two levels up, enabling proper dynamic module discovery and registration.
- **Namespace & Attribute Hardening:** Resolved `AttributeError` by initializing core dependencies (`state_cache_manager`, `protocol_router`, etc.) to `None` in the `ComProtocolManager` constructor. Fixed `NameError` for `matrix_log` and `DEVICE` in several modules.
- **Interface & Dependency Integrity:** Standardized `start()` signatures across protocols to accept `mqtt_connection_manager` and `subscriber_router`. Updated `MqttConnectionManager` and `Is07Bridge` with required lifecycle methods (`start`, `stop`, `is_running`).
- **Supervisor Refactoring:** Refactored `openair.py` to use the centralized `start_all_protocols()` entry point, simplifying the bootstrap sequence and ensuring consistent dependency injection.

## [V3.3.2] - 2026-04-14
### REST Core MQTT Transport Integration
- **Native REST MQTT:** Implemented `RestMqttTransport` in `oaComREST/Core/rest_mqtt_transport.py` and a common `EventTransport` base class.
- **Manager Refactoring:** Updated `RESTManager` to utilize the core transport for heartbeat status reporting when system-level managers are missing (Standalone Mode).
- **Public API Hardening:** Updated `oaComREST/Core/__init__.py` and `oaComREST/Entry.py` to properly export the new core transport.

## [V3.3.1] - 2026-04-14
### Fixed
- **SNMP Manager Attribute Error:** Resolved `AttributeError: 'SNMPBridge' object has no attribute 'run_verification'` by implementing the `run_verification` method in the `SNMPManager` base class. This method correctly delegates verification tasks to the `SnmpTester.verify_oid_tree` worker, restoring functionality to the MIB and OID verification UI tabs.

### Core MQTT Transport Integration
- **Native Core Transports:** Integrated MQTT into the `Core` of `oaComNmos`, `oaComMidi`, and `oaComOSC` modules to maintain architectural consistency and fulfill the "Gatekeeper" mandate.
- **NMOS Core:** Added `Is07MqttTransport` to `oaComNmos/Core/is07_transport.py` and updated `IS07/transports.py` to utilize the core implementation.
- **MIDI Core:** Implemented `MidiMqttTransport` in `oaComMidi/Core/midi_mqtt_transport.py` and refactored `MidiMqttWorker` into a slim wrapper for the core transport.
- **OSC Core:** Implemented `OscMqttTransport` in `oaComOSC/Core/osc_mqtt_transport.py` and refactored `OSCManager` to eliminate internal MQTT client logic in favor of the new core transport.
- **Public API Hardening:** Updated `Entry.py` and `Core/__init__.py` for all three modules to properly export the new core transports, ensuring they are recognized as part of the module's public API.
- **Verification:** Created `test_is07_transport.py` for NMOS and verified all communication modules pass their respective test suites.

## [V3.3.0] - 2026-04-12
**************************************
Commit: a7d35765be7c921d7a33275cb4f4a66137781d25
Date: 2026-04-13 00:14:46
Message: GitHub Actions CI/CD Integration
**************************************
### GitHub Actions CI/CD Integration
- **Automated Workflow:** Implemented `.github/workflows/ci.yml` for automated testing, linting, and structural auditing on every push and pull request.
- **Structural Audit:** Created `.github/scripts/structural_audit.py` to enforce the "12-subfolder standard" and the "Entry.py Gatekeeper" mandate across all `oa*` modules.
- **Native Build Pipeline:** Added `.github/scripts/build_rust_modules.py` to automatically find and build all Rust-based extensions using `maturin develop --release`.
- **Ruff Standardization:** Introduced `.ruff.toml` with strict rules for complexity and style, ensuring adherence to the project's single-responsibility and named-argument mandates.
- **CI Caching:** Implemented Cargo registry caching to significantly reduce build times for native components in the CI environment.

## [V3.1.14] - 2026-04-09
### GUI Manager Logging & Stability
- **Blueprint Validation Fix:** Demoted `FileNotFoundError` (missing blueprint) in `UniversalGuiLoader` from `ERROR` to `WARNING`. This prevents CI/CD log clutter for handled validation failures while maintaining visibility in the UI.
- **Logging Standardization:** Standardized all logs in `oaGui/Core/loader/gui_from_json.py` to use `matrix_log` with the "exactly three emojis" visual grepping rule and bracketed categories (e.g., `[VALIDATION]`, `[BUILDER]`, `[SUCCESS]`, `[CATASTROPHIC]`).
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
- Handled KeyboardInterrupt in UI partition (oaGui) to ensure graceful shutdown without tracebacks.
- Added synchronous shutdown() method to ShutdownCoordinator to handle non-GUI-event-driven termination.

## [20260404.2245.1] - 2026-04-04
- Fixed redundant traceback logging in Bootstrap sequence.
- Standardized shutdown calls in AsyncBootstrapEngine using root.after.
## [20260404.2300.1] - 2026-04-04
- Fixed X11 BadValue (0x0) crashes during UI build and background sync.
- Implemented robust dimension checks in DynamicGuiBuilder, BuilderBackgroundManager, TransparencyMixin, and OverlayManager.

### [2026-04-04 23:35:00] - Bug Fix: X11 BadValue Crash (Geometry Sanitization & Hardening)
- Implemented geometry sanitization in `WidgetContext` to enforce a 1x1 minimum pixel size for all materialized containers.
- Hardened `UniversalGuiLoader` in `oaGui/Core/loader/gui_from_json.py` with 1x1 floor and `try...except` wrapper during builder instantiation.
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

## [20260411.0020.1] - 2026-04-11
### Fixed
- **SNMP Installer Noise:** Removed automated 'snmpwalk' test from the end of the generated SNMP installer script. This prevents raw telemetry data from being output to the console during installation, which was causing "command not found" errors in shells misinterpreting the output.
- **SNMP Manager Scope:** Resolved a 'NameError' for 'matrix_log' in 'snmp_manager.py' by correctly importing it at the module level.
- **SNMP Manager Syntax:** Fixed a syntax error in 'snmp_manager.py' imports (dots vs slashes).

## [20260429.0105.1] - 2026-04-29
### Fixed
- **Vertical Rendering:** Fixed a bug in DynamicGuiBuilder where it only tracked width changes. It now correctly reacts to height changes, ensuring the preview fills the vertical space.
- **Transparency Support:** Changed default render tier to 'High-Res' in the Interactive Layout to ensure transparency (alpha channel) is visible by default.
- **Panel Visibility:** Robustified the sash positioning logic in the WYSIWYG editor to prevent the center panel from collapsing on launch.
- **Telemetry Link:** Updated the WYSIWYG editor and PreviewEngine to accept and use the system's subscriber_router and state_mirror_engine, allowing real device telemetry to be displayed in the builder.
- **Flat Texture Rendering:** Fixed a bug in PanelGenerator where 'flat' textures were still applying streak overlays.
### Added
- **Background Rendering Test:** Added a new integration test 'oaGuiElements/Tests/images/test_procedural_bg_engine.py' to verify the background rendering pipeline.

## [20260429.0125.1] - 2026-04-29
### Fixed
- **DynamicGuiBuilder Vertical Height**: Fixed a critical bug in  where it was using stale  instead of the current event height. Also updated  to pass both dimensions to the resize handler. This ensures that GUI components fill the full vertical space in the main application.
- **PreviewEngine Aggressive Stripping**: Refined  in the editor's  to only remove dimensions from the structural root object. This prevents child widgets from having their intended sizes stripped away while still allowing the preview container to resize fluidly.

## [20260429.0125.1] - 2026-04-29
### Fixed
- **DynamicGuiBuilder Vertical Height**: Fixed a critical bug in `_perform_canvas_resize` where it was using stale `winfo_height()` instead of the current event height. Also updated `_on_canvas_configure` to pass both dimensions to the resize handler. This ensures that GUI components fill the full vertical space in the main application.
- **PreviewEngine Aggressive Stripping**: Refined `_strip_constraints` in the editor's `PreviewEngine` to only remove dimensions from the structural root object. This prevents child widgets from having their intended sizes stripped away while still allowing the preview container to resize fluidly.

## [20260429.0135.1] - 2026-04-29
### Added
- **Global Telemetry Footer**: Implemented a real-time dimension footer for all `DynamicGuiBuilder` windows. This footer displays the current `Viewport` (telemetry size) and `Content` (scrollable frame size) dimensions.
- **Configurable Footer**: Added `FOOTER_ENABLED` setting to `config.ini` and `ConfigDefaults` to allow global toggling of the telemetry footer.
### Fixed
- **Resize Integrity**: Corrected a `NameError` in `_perform_canvas_resize` and ensured the footer updates dynamically during window manipulation.

## [20260429.0140.1] - 2026-04-29
### Fixed
- **Footer Initialization**: Added an initial resize pass in the `_on_visibility` handler of `DynamicGuiBuilder` to ensure the footer is populated with non-zero dimensions as soon as the UI is physical.
### Added
- **Command Telemetry in Footer**: Hooked into `_transmit_command` to display the active MQTT transmission (widget name and value) directly in the footer. Added visual highlighting to the TX label to confirm successful command dispatch.

## [20260429.0150.1] - 2026-04-29
### Added
- **Dedicated GUI Log Partition**: Implemented a new log sink in `oaLogging` that automatically redirects all graphics, rendering, and editor-related logs to `oaDataLogs/Gui/`. This partition captures events from `oaGui`, `oaGuiElements`, and `oaGuiEditorWYSIWYG`, as well as any logs tagged with GUI-specific categories.

## [20260429.0155.1] - 2026-04-29
### Fixed
- **Footer Sync in Notebooks**: Renamed visibility handler to `_on_gui_visible` to ensure compatibility with `TabManagerMixin`. This ensures that footer dimensions are correctly updated when switching tabs in a `Notebook` (e.g., the Zoo window).
- **Activity Pulse Visibility**: Added a forced UI update call during command transmission to ensure the TX label's color pulse is visible during heavy rendering tasks.
### Added
- **Enhanced Render Logging**: Updated `oaGuiElements/Core/background.py` to use the `RENDER` category for background generation events. These events are now correctly captured and redirected to the `oaDataLogs/Gui/` forensic logs.

## [20260429.0160.1] - 2026-04-29
### Fixed
- **Telemetry Discrepancy**: Updated `UITrackingService` to report actual widget (viewport) dimensions instead of the `toplevel` window size. This ensures MQTT telemetry aligns perfectly with the GUI footer display.
- **Local Telemetry Sync**: Implemented a callback system where MQTT geometry transmissions are mirrored back to the local footer's `GEO:` label for immediate verification.
### Added
- **Detailed Command Monitoring**: The footer now separates `GEO:` (Geometry) and `TX:` (Command) telemetry into dedicated labels. This allows you to monitor window movement and widget interactions simultaneously.

## [20260429.0165.1] - 2026-04-29
### Fixed
- **Resize Signature Mismatch**: Corrected a `TypeError` in `oaGui/Managers/gui_re.py` where `_final_settle` was calling `_perform_canvas_resize` with the old single-argument signature. It now correctly passes both `width` and `height`.
- **Bin-Level Footer Sync**: Updated `oaGui/Core/structural_assembler.py` to trigger the builder's `_update_footer` during structural resizing. This ensures that nested containers (bins) report their viewport and content dimensions to the telemetry footer.
### Added
- **Structural Render Tracing**: Redirected structural assembler logs to the `RENDER` category to ensure they are captured in the `oaDataLogs/Gui/` forensic stream.

## [20260429.0170.1] - 2026-04-29
### Changed
- **Increased UI Responsiveness**: Reduced `RESIZE_WIDTH_THRESHOLD` from 20px to 5px. This ensures the GUI footer and background engine react much earlier to small growth or shrinkage of the window.
- **Visual Feedback on Resize**: Updated the telemetry footer to pulse white whenever `Viewport` or `Content` dimensions change, providing immediate confirmation of layout scaling.

## [20260429.0175.1] - 2026-04-29
### Fixed
- **Grid Expansion Integrity**: Corrected multiple instances where `tk.Frame` containers were defaulting to restricted sizes. Forced `grid_rowconfigure(0, weight=1)` on all tab frames and universal loaders to ensure the `DynamicGuiBuilder` can expand to fill the full vertical space.
- **Root Geometry Protection**: Refined the `_strip_constraints` logic in the `PreviewEngine`. It now only removes dimensions from the structural root object, preserving the intended height/width of widgets defined within your JSON (like `OcaBin`).
- **Forced Geometry Realization**: Added `self.update()` calls during the initial visibility pass of the builder. This forces the OS to calculate physical dimensions immediately, ensuring the footer and background engine don't initialize with "0x0" values.

## [20260429.0180.1] - 2026-04-29
### Fixed
- **Container Height Collapse**: Eliminated a hardcoded 200px height default in `structural_assembler.py` for `OcaBin` objects. This allows containers to respect parent expansion weights and fill the full vertical height of the screen.
- **Grid Expansion Reliability**: Replaced the `ttk.Frame` main content container in `DynamicGuiBuilder` with a standard `tk.Frame`. This bypasses style-based height clamping and ensures that `grid_rowconfigure(0, weight=1)` is respected by the OS rendering engine.

## [20260429.0185.1] - 2026-04-29
### Fixed
- **TclError (Unknown Option -bg)**: Resolved a crash in the `DynamicGuiBuilder` by changing its inheritance from `ttk.Frame` to `tk.Frame`. This allows the builder to accept standard background configurations and ensures full compatibility with the industrial background engine.

## [20260429.0190.1] - 2026-04-29
### Fixed
- **Telemetry Event Gating**: Implemented strict event source validation across `DynamicGuiBuilder`, `StructuralAssembler`, and `UITrackingService`. This prevents "Event Bubbling" where child widgets (like the footer or buttons) were accidentally triggering the parent's resize logic with their own small dimensions.
- **Viewport/GEO Alignment**: Updated the resize handler to use a "Throttled Settle Pass" (`_trigger_final_resize`). This ensures that the dimensions reported in the footer and transmitted via MQTT are always derived from the physical, settled state of the window, eliminating the `42px` height discrepancy.

## [20260429.0195.1] - 2026-04-29
### Fixed
- **Core Geometry Logic Restoration**: Surgically restored `oaGui/Workers/builder.py` to fix method corruption where `_perform_canvas_resize` and `_update_footer` logic had partially merged.
- **Physical Pixel Synchronization**: Updated the footer calculation to query physical OS dimensions via `winfo_height()` during the throttled settle pass. This ensures that the `Viewport` height in the footer always matches the `GEO` height transmitted to MQTT.
- **Expansion Weight Reinforcement**: Added mandatory parent-level grid row/column weight configuration during the visibility settle pass. This prevents nested containers from clamping the builder to a default 42px or 200px height.
