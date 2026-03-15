**************************************
Commit: 535779334dcff112406d55c73f96987f8c45f21a
Date: 2025-11-30 00:34:10 -0500
Message: cleaning up
Details: Performed a final cleanup of the YAKETYYAK.json device library, standardizing SCPI trigger flags to use string-based "false" values for improved parsing consistency. Cleared out stale output values for center and span frequency to ensure a clean state upon device initialization.
**************************************
Commit: 060e1da3d423c227787bf00199afcc76b9f56b30
Date: 2025-11-29 23:29:31 -0500
Message: local debug adjusted and date and time adjusted
Details: Adjusted local debug flags across multiple instrument drivers to provide a more focused diagnostic output. Updated the default frequency ranges in the SCPI actuator models to align with common spectrum analyzer hardware limits.
**************************************
Commit: 79863c9e92feeac053f662d017ef74a892d36786
Date: 2025-11-27 00:31:48 -0500
Message: date change
Details: Executed a global version synchronization across all builder components, updating the internal version string to 20251127. Resolved a race condition in the trapezoid button toggler by implementing a mandatory delay between state transitions.
**************************************
Commit: 01c1b6465a52bb22675e9fa10b2c00120595c2bd
Date: 2025-11-27 00:25:33 -0500
Message: date updates
Details: Standardized the versioning and logging headers for the core DynamicGuiBuilder and associated actuator creators. Fixed an issue where actuator buttons were incorrectly publishing to the repository topic instead of the dedicated actions topic.
**************************************
Commit: d2317b267ecbec4b5395aa70c7960a9ca7efe507
Date: 2025-11-27 00:19:44 -0500
Message: date update
Details: Applied versioning updates to the plotting and file path GUI modules, ensuring consistent metadata across all dynamically loaded tabs. Established a standardized revision number for all experimental UI components.
**************************************
Commit: 22724fa6ab63a870442e11ebcbeb85494a8cec66
Date: 2025-11-27 00:18:17 -0500
Message: Date Update
Details: Synchronized the date and revision metadata for the single-trace plotting GUI and associated file loading utilities. Refined the version hash calculation logic to improve the reliability of the system's internal component tracking.
**************************************
Commit: 4deeb6b7912d4ac4b501ca2dd0179e4ebabe1185
Date: 2025-11-27 00:15:23 -0500
Message: date update
Details: Updated the frequency sweeping and setup GUI components with the latest system version markers. Improved the documentation headers for several sub-tab modules to better reflect their role in the RF monitoring workflow.
**************************************
Commit: 573e93b4bd08fe03ee3fc7fa3574d57d7c4dc78a
Date: 2025-11-27 00:14:25 -0500
Message: Date update
Details: Refreshed the version information for the instrument translator and frequency settings GUI. Enhanced the cross-platform path resolution logic to better handle backslashes in Windows environments.
**************************************
Commit: 1f48250a06089d5822e2122f26f0dfcf53dde6b4
Date: 2025-11-27 00:08:41 -0500
Message: panic restore
Details: Performed a "panic restore" of the YAKETYYAK.json configuration, reverting several experimental SCPI trigger changes that caused command sequencing issues. Stabilized the default start and stop frequency values for the handheld analyzer profile.
**************************************
Commit: d326d8c50338dcd87419b12308b64bd3bdad9e50
Date: 2025-11-26 23:25:17 -0500
Message: major overhaul of gui and builds for linux and windows
Details: Conducted a major overhaul of the GUI build system, adding support for native execution on both Linux and Windows. Re-introduced the standard MARKERS.csv dataset to facilitate testing of the new marker management dashboard.
**************************************
Commit: 9f0cde36a72edd1ed99c2dfb49d5d44306a78297
Date: 2025-11-24 22:59:10 -0500
Message: FIX: Resolve layout conflicts in GUI components
Details: Resolved several layout conflicts in the marker importer and peak hunter GUI components by transitioning from fixed grid constraints to more flexible pack-based distribution. Fixed a path manipulation bug that caused issues when loading modules on Windows.
**************************************
Commit: ad9f8e7d048e562e3433acfb79a132693badbc87
Date: 2025-11-24 22:55:15 -0500
Message: FIX: Resolve layout conflicts in GUI components
Details: Fixed layout inconsistencies in the Showtime tab and introduced the MarkerPeakHunterGUI as a new dedicated component for automated signal analysis. Improved the separation of concerns between marker editing and real-time peak detection.
**************************************
Commit: 1678615fc8a230d3d4326f8ff9bacfcc110aba49
Date: 2025-11-24 22:51:12 -0500
Message: FIX: Correct GUI component loading and marker manager logic
Details: Enhanced the Application loader with specialized handling for DynamicGuiBuilder instances, ensuring that theme and topic filters are correctly passed during instantiation. Replaced incorrect frequency logic in the marker manager with a robust MQTT-based placeholder.
**************************************
Commit: f1f54fe43983777826d15398c8cce435913c092b
Date: 2025-11-24 22:48:18 -0500
Message: FIX: Resolve display issues and ImportError
Details: Resolved a critical ImportError by correcting class naming inconsistencies between the loader and the graph component definition. Refactored the plotting engine to be fully embeddable as a standard Tkinter frame, resolving long-standing layout conflicts with the main notebook.
**************************************
Commit: 8cebcc5061be13d33d5a296d2e30ff7cdf46aa30
Date: 2025-11-24 22:43:48 -0500
Message: FEAT: Add MarkerSettingsManager import and instantiation
Details: Integrated the MarkerSettingsManager into the core application launch sequence, enabling centralized management of RF markers. Moved project-specific imports to occur after the system path has been established to improve startup resilience.
**************************************
