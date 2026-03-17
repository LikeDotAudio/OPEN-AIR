# OPEN-AIR Changelog

## [2026.03.17] - 02:15
**************************************
Commit: b2856ee249f11ff24f01bc9b07895c730a54e1ec
Date: 2026-03-17 09:04:09
Message: ## [2026.03.17] - 02:15 ### Quality Assurance & Testing Suite - Implemented a Unified Test Launcher (tests/generate_and_log_tests.py) that automatically discovers and executes tests with HTML/JSON reporting. - Created 9 comprehensive unit test modules covering critical Top Offender components. - Established the Network Chaos suite to verify MQTT reconnection logic and message idempotency. - Developed the Hardware Boundary suite to test VISA timeout handling and command buffer overflow stability. - Implemented File & Environment tests for permission denial scenarios and corrupt state recovery. - Added UI Rendering Edge Case tests for malformed GUI definitions and font fallback mechanisms. - Conducted a successful Round Trip E2E test verifying the path from MQTT input to VISA output. - Fixed TopicCalculator logic to strip structural layout tokens (display, gui). - Performed a comprehensive Quality Assurance audit, identifying and removing legacy mock-testing-mock anti-patterns.
**************************************
### Quality Assurance & Testing Suite
- Implemented a Unified Test Launcher (`tests/generate_and_log_tests.py`) that automatically discovers and executes tests with HTML/JSON reporting.
- Created 9 comprehensive unit test modules in `tests/assets_tests/` (now consolidated into `tests/managers/` and `tests/workers/`) covering critical "Top Offender" components.
- Established the "Network Chaos" suite to verify MQTT reconnection logic and message idempotency.
- Developed the "Hardware Boundary" suite to test VISA timeout handling and command buffer overflow stability.
- Implemented "File & Environment" tests for permission denial scenarios and corrupt state recovery.
- Added UI Rendering Edge Case tests for malformed GUI definitions and font fallback mechanisms.
- Conducted a successful "Round Trip" E2E test verifying the path from MQTT input to VISA output.
- Fixed `TopicCalculator` logic to strip structural layout tokens ('display', 'gui') as per engineering standards.
- Performed a comprehensive Quality Assurance audit, identifying and removing legacy mock-testing-mock anti-patterns.

## [2026.03.17] - 01:25
**************************************
Commit: 6d434891bbb7c5aa991c6fdb4815d2b3c4d8c54e
Date: 2026-03-17 01:36:07
Message: ## [2026.03.17] - 01:25 ### WYSIWYG Editor Fixes - Resolved ImportError: Renamed state to state_manager and updated all 16 module files to use the correct singleton export. - Resolved ModuleNotFoundError: Corrected relative import depths across wysiwyg_editor/workspaces/core/ and layout_overlays/ to align with the modular package structure. - Refactored run.py to run_builder.py for standalone process consistency. - Updated context_menu.py with file-existence checks and un-gated error logging for better forensic traceability.
**************************************
### WYSIWYG Editor Fixes
- Resolved `ImportError`: Renamed `state` to `state_manager` and updated all 16 module files to use the correct singleton export.
- Resolved `ModuleNotFoundError`: Corrected relative import depths across `wysiwyg_editor/workspaces/core/` and `layout_overlays/` to align with the modular package structure.
- Refactored `run.py` to `run_builder.py` for standalone process consistency.
- Updated `context_menu.py` with file-existence checks and un-gated error logging for better forensic traceability.

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
