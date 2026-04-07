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
