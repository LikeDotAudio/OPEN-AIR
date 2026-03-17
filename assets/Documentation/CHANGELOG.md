# OPEN-AIR Changelog

## [2026.03.17] - 01:15
### Security & Cleanup
- Refactored all `xxx_Commands` directories to `_Legacy_Commands` and updated system-wide path references.
- Renamed `xxxx_5_indicators` to `5_Indicators` for standardized ordering.
- Performed a security sweep: verified no dangerous `exec()` or `eval()` calls in critical paths.
- Updated `Documentation_Map.md` to remove legacy `XXX` prefixes from worker documentation.

### Performance Optimization
- Implemented `BatchLogSink` in `logger.py` to cache logs and write in chunks, reducing I/O and lock contention.
- Optimized `MqttConnectionManager` by replacing idle-polling with an `asyncio.Event` driven bridge.
- Set `LOCAL_DEBUG = False` globally to reduce telemetry overhead in production-ready paths.
- Implemented throttled restart backoff in the Supervisor (`OpenAir.py`) to prevent CPU spikes during persistent failures.

## [2026.03.16] - 23:00
**************************************
Commit: 24d142473c50ae3cf4073103135171b85c4c98c1
Date: 2026-03-17 00:40:32
Message: ## [2026.03.16] - 23:00 ### Fixed - Fixed  in background panel generation by updating  calls to . - Fixed  in  graph initialization by correctly referencing the  module. - Resolved multiple thread failures occurring during dynamic GUI building.
**************************************
### Fixed
- Fixed `AttributeError` in background panel generation by updating `PanelGenerator` calls to `generate_procedural_panel`.
- Fixed `NameError` in `FluxPlotter` graph initialization by correctly referencing the `graph` module.
- Resolved multiple thread failures occurring during dynamic GUI building.
