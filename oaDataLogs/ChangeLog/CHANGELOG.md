# OPEN-AIR Changelog

## [2026.03.28] - 23:55
### Communication Broker Refactoring & SNMP GUI Fixes
- **Refactoring**: Relocated failover_manager.py to Managers/Failover/Manager.py and protocol_router.py proxy to Core/protocol_router/manager.py for better encapsulation.
- **Documentation**: Generated comprehensive narrative 'play-by-play' event lifecycle documentation with Mermaid sequence and block diagrams.
- **Bug Fix**: Resolved project-wide ModuleNotFoundError issues by synchronizing all 25+ ProtocolRouter import references.
- **SNMP GUI**: Optimized the SNMP Delta Monitor to correctly track current vs previous OID values and prevent redundant state refreshes from overwriting history.
- **Loop Prevention**: Refined the Protocol Router strategy to exempt status and monitor topics from reflection rejection, ensuring critical CORE-to-UI telemetry is preserved.

## [2026.03.28] - 17:30
**************************************
Commit: c7f56967f4663fc28d04021025c32005acb6638c
Date: 2026-03-28 23:30:07
Message: Relocation & Structural Alignment
**************************************

**************************************
Commit: 4f454f4fd702a1718df1d8afe60240b1425219f8
Date: 2026-03-28 22:37:32
Message: Structural Audit & Code Hygiene
**************************************

### Structural Audit & Code Hygiene
- **Structural Audit**: Conducted a comprehensive "Bad Class & Objects" audit identifying God Classes and dispatch map violations.
- **Top Offender Identified**: `LayoutParser` in `oaGuiManager` flagged for SRP violations due to multi-strategy layout logic.
- **Quick Win Strategy**: Proposed a dispatch map refactor for `TestsUI` button handling.
- **Cleanup**: Recursively removed all `__pycache__` directories to ensure clean build state.
- **Relocation**: Moved `CHANGELOG.md` from `oaDocumentation/Documentation/` to the mandated `oaDataLogs/ChangeLog/` directory.

## [2026.03.24] - 16:45
### UI Optimization & Syntax Correction
- **Responsive Layout**: Implemented media queries in `oaTests/Interface/TestsUI.py` to reduce button height and label margins when terminal height is below 40 lines.
- **Bug Fix**: Corrected a `NameError` in `oaTests/Interface/TestsUI.py` by renaming `selfself` to `self` in the `record_result` callback.
- **Hygiene**: Ensured proper scaling of sidebar padding and log margins in compact display modes.

## [2026.03.24] - 15:15
### Comment Audit & Hygiene Remediation
- **Audit Analysis**: Conducted a project-wide review of "Bad Comments" as reported by the automated audit.
- **Header Standards Reaffirmation**: Verified and reaffirmed the use of Mandatory File Headers (FolderName/Filename, Author, Version) in alignment with Rule 45 and Rule 46 of the project mandates.
- **Dead Code Cleanup**: 
    - Audited `oaTests/Interface/TestsUI.py`, `oaTests/Methods/FlameGraph/flame_wall_shame.py`, and `oaTests/Methods/FlameGraph/flame_manager.py`.
    - Removed minor legacy commented-out artifacts while preserving functional documentation and disabled feature flags.
- **Deep Search Validation**: Executed a systemic grep search across all local modules to identify and eliminate blocks of dead code (commented-out keywords: `def`, `class`, `if`, etc.).

## [2026.03.24] - 14:30
### MQTT Infrastructure Refactoring & Simplification
- **Architectural Decomposition**: Refactored the MQTT communication layer to resolve high-complexity "God Class" and "Singleton" patterns identified in the system audit.
- **MqttConnectionManager Optimization**:
    - Simplified the Singleton facade to focus strictly on the synchronous/asynchronous bridge.
    - Implemented delegated properties for `loop` and `kick_event` to clean up the interaction with the background worker.
    - Removed redundant internal queues and logic, delegating to specialized managers.
- **MqttAsyncWorker Refactoring**:
    - Decoupled the worker from the manager's internals.
    - Implemented explicit dependency on `MqttQueueManager` for outbound traffic.
    - Optimized the `_queue_task` to use non-blocking `get_nowait()` calls, eliminating event loop stalls.
- **MqttQueueManager Consolidation**:
    - Standardized as the single source of truth for all MQTT message queuing (Publish/Subscribe).
    - Optimized for cross-thread safety and asynchronous worker signaling.
- **MqttManager Rewrite**:
    - Performed a complete structural rewrite to fix corrupted logic and broken method references.
    - Eliminated the redundant `AsyncPublisher` and its associated worker thread/queue, reducing system overhead.
    - Standardized periodic system status publishing and control command handling.
- **Redundancy Elimination**: Deleted `oaComMQTT/Core/async_publisher.py` and consolidated all publishing logic into the core connection manager.

## [2026.03.22] - 11:00
**************************************
Commit: 769b277e1324ab37f16d6a20db23c62cdc6b47e0
Date: 2026-03-22 06:56:48
Message: Code Hygiene & Cleanup - Performed a project-wide audit and remediation of "bad comments" and redundant metadata.
**************************************
### Code Hygiene & Cleanup
- **Code Hygiene & Cleanup**: Performed a project-wide audit and remediation of "bad comments" and redundant metadata.
- **Header Standardization**: Applied the mandated professional header format (`FolderName/FileName.py`, Author, Version, Description) to all `.py` and `.md` files.
- **Journal Noise Removal**: Stripped legacy "journal noise" (Professional services, Blog links, Build logs, etc.) from over 400 files.
- **Obsolete Code Elimination**: Removed extensive blocks of commented-out Python code (`def`, `# if`, `# class`, `# import`) identified in "Top Offender" files such as `oaFileImportShow/FileReaders/loader.py`, `oaComMidi/Core/Hui/scripts/csvWriter.py`, and across `oaGuiElements/`.
- **Formatting Integrity**: Ensured all cleaned files adhere to the project's architectural standards and visibility guidelines.
- **Test Suite Fixes**: Resolved multiple failures in `oaGuiElements` unit tests:
    - Fixed `TclError` (image doesn't exist) in `button_wink` and `button_wink_toggler` tests by patching renderers during creation tests.
    - Resolved `TypeError` in `meter_bar` tests by robustifying mock root and widget configuration (handling `cget` and `winfo` methods).
    - Fixed `button_wink_toggler` redraw logic crash by ensuring mock canvas returns integer dimensions.

## [2026.03.18] - 00:30
**************************************
Commit: 25bd5e36f5895de4981fd198cbb41ee00e1b881c
Date: 2026-03-18 00:30:00
Message: ## [2026.03.18] - 00:30 ### The Supervisor Tree Refactor (Migration Phase 1) - Core Infrastructure: Migrated system-level managers to specialized oaConfiguration, oaLogging, and oaDependencies modules. - Communication Layer: Moved hardware and protocol scripts into dedicated silos. - Data Vaults: Reorganized all DATA/ and assets/ content into oaData* directories. - GUI Engine: Refactored the UI controller and builders into oaGuiManager, oaGuiBuild, and oaGuiElements. - System Integrity: Updated all import paths, path guards, and fixed ModuleNotFoundErrors.
**************************************
### The Supervisor Tree Refactor (Migration Phase 1)
- **Core Infrastructure**: Migrated system-level managers to specialized `oaConfiguration`, `oaLogging`, and `oaDependencies` modules.
- **Communication Layer**: Moved hardware and protocol scripts into dedicated silos: `oaComBroker` (MQTT/Router), `oaComVisa`, `oaComMidi`, `oaComOSC`, and `oaComSNMP`.
- **Data Vaults**: Reorganized all `DATA/` and `assets/` content into `oaData*` directories (RunningFiles, Logs, Cache, SNMP, Splinks).
- **GUI Engine**: Refactored the UI controller and builders into `oaGuiManager`, `oaGuiBuild`, and `oaGuiElements`.
- **System Integrity**: 
    - Updated all absolute and relative import paths project-wide.
    - Corrected path guard logic in dynamic GUI modules to align with the new hierarchy.
    - Fixed `ModuleNotFoundError` by ensuring all refactored directories contain proper `__init__.py` package markers.
    - Verified the Supervisor (`OpenAir.py`) correctly orchestrates the new Partitioned Architecture.

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
