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
