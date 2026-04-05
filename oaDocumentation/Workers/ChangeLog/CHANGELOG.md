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
