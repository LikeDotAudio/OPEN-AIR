**************************************
Commit: 2e2babb3b67bf469dc51bc27868d8fd966660913
Date: 2025-12-31 22:33:10 -0500
Message: lots of synch errors solved....
Details: Resolved a series of synchronization errors related to inconsistent method resolution orders (MRO) in the GUI button mixins. Improved the reliability of module loading by standardizing the inheritance hierarchy for trapezoid-style buttons across several control panels.
**************************************
Commit: eeb0607ef5e12a48aef87aae20b53a056029e600
Date: 2025-12-31 21:27:23 -0500
Message: fixed loaders
Details: Fixed several issues in the module loader where __builtins__ were missing in dynamic imports, causing instantiation failures for key UI components. Cleared out a large volume of stale error logs to provide a cleaner diagnostic environment.
**************************************
Commit: 052f50ae42d3c5a31559b5d8a106a18ffedbe341
Date: 2025-12-31 01:23:11 -0500
Message: linker fixed....
Details: Resolved a critical bug in the dynamic GUI wrapper where missing JSON blueprints for the distortion manager caused application-wide instantiation failures. Improved the forensic trace logging to provide better visibility into file system resolution errors.
**************************************
Commit: f9afa240a742d98c26d2334e1979c952cfc6c005
Date: 2025-12-31 00:59:24 -0500
Message: publish and mirror fixes.   state cache created on load up
Details: Implemented state cache initialization during the early boot sequence, ensuring that the StateMirrorEngine has a valid baseline before MQTT listeners are established. Removed legacy CSV markers and deactivated redundant MQTT utility instances to reduce background processing overhead.
**************************************
Commit: dc5d778fead0adcfe4bceb290e876e5532b6d4d2
Date: 2025-12-08 00:08:13 -0500
Message: Debug: Add print statement to Application.__init__ in gui_display.py.
Details: Added strategic debug print statements to the Application constructor to diagnose a persistent issue where the main window failed to appear during startup. This change helps confirm that the entry point for the Tkinter engine is being reached correctly.
**************************************
Commit: 74d2542783294877cbb2ade72f325170dffec27e
Date: 2025-12-08 00:07:02 -0500
Message: Debug: Use print after MQTT connect in main.py.
Details: Enhanced the main entry point with additional console logging following the MQTT connection attempt, verifying that the supervisor thread is proceeding to the display opening sequence.
**************************************
Commit: 25c1cd04d65fc98445f526f68cbe6602c49437ac
Date: 2025-12-08 00:06:01 -0500
Message: Debug: Add log after MQTT connect in main.py.
Details: Added a debug log entry to confirm the return from connect_mqtt(), facilitating more granular troubleshooting of the initial handshake between the application and the local message broker.
**************************************
Commit: 88ca1dfb87036aa652ba49d26b360d144f94e252
Date: 2025-12-08 00:04:17 -0500
Message: Debug: Disable window topmost and add mainloop log
Details: Temporarily disabled window "topmost" attributes and bypassed the splash screen during development to more easily diagnose GUI rendering issues. Added a "mainloop" debug marker to track the transition into the Tkinter event loop.
**************************************
Commit: 72431b168f7c7a5c95ec4c76d4b328f381a6fa62
Date: 2025-12-08 00:01:55 -0500
Message: Fix: Simplify splash_screen.py import logic for robust startup
Details: Simplified the import logic in splash_screen.py to improve startup robustness, ensuring that project-level paths and logging utilities are correctly resolved even if Pillow is missing. Established a module-level project root definition to prevent path resolution hangs.
**************************************
Commit: e75cb7e80da0312f9b2a0d225bf848bc75fe4d24
Date: 2025-12-08 00:00:24 -0500
Message: Fix: Gracefully handle PIL ImportError in splash_screen.py
Details: Implemented a graceful fallback for the splash screen when the PIL/Pillow library is unavailable, preventing application crashes on systems with incomplete imaging dependencies. Added text-based status updates for developer attribution and initialization progress.
**************************************
Commit: 46552c60374751a804a4a43e20295fb291b633fe
Date: 2025-12-07 23:58:44 -0500
Message: Fix: Improve JSON file path resolution for DynamicGuiBuilder
Details: Significantly improved JSON file path resolution in the DynamicGuiBuilder, adding robust handling for MQTT topics with repository or configuration prefixes. Implemented a more reliable string-to-filename mapping strategy that handles nested topic structures.
**************************************
Commit: 4d7d01750770519afce249843b661d2667b926c1
Date: 2025-12-07 23:53:36 -0500
Message: Refactor: DynamicGuiBuilder - Local JSON for GUI structure, MQTT for updates
Details: Refactored the DynamicGuiBuilder to establish local JSON files as the authoritative source for GUI structure, while MQTT remains the source for real-time value updates. This change prevents unnecessary GUI rebuilds when receiving full configuration messages via the message broker.
**************************************
Commit: 0658b232bca71e2acccd04df291cc3bfbd0d705f
Date: 2025-12-07 23:48:56 -0500
Message: Feat: Implement GUI build from local JSON and optimize MQTT updates
Details: Optimized the initial GUI build sequence by prioritizing local JSON blueprints over MQTT-sourced configurations, dramatically improving tab loading times. Introduced the DATASET_ROOT_DIR constant to centralize the location of JSON-based instrument definitions.
**************************************
Commit: c836ca3ef115c441028b3f50b08b67de03df7621
Date: 2025-12-07 23:41:26 -0500
Message: Fix: Optimize GUI tab loading performance
Details: Implemented a "Map" event listener that ensures each GUI tab is only built once upon its first activation. This optimization significantly reduces UI lag when switching between complex control panels.
**************************************
Commit: 7ecbf8519e48ee5696f0a67c2972787873d7cb73
Date: 2025-12-07 23:35:17 -0500
Message: Refactor: Rename tab directories and update GUI display logic
Details: Standardized the directory naming convention for GUI tabs using numerical prefixes (e.g., 1_Connection) and updated the Application class to dynamically load modules from these new paths. This refactor improves the organization and discoverability of the application's layout.
**************************************
Commit: 90c08c0a1b2e4d1665500eca11677ca1a699837e
Date: 2025-12-07 23:03:30 -0500
Message: more splitting things up
Details: Conducted a major thinning of the PRESET.csv file, removing legacy instrument presets in favor of more modular JSON-based definitions. Standardized the package-level __init__.py files across several core modules.
**************************************
Commit: 64e12b9a7837d4770bfc669c12acb82e29c4027a
Date: 2025-12-07 21:44:36 -0500
Message: splitting it up into smaller files...
Details: Refactored the YAKETYYAK.json instrument definition to use more consistent boolean representation for SCPI trigger flags. Standardized several frequency and bandwidth settings to improve compatibility with legacy hardware drivers.
**************************************
Commit: 7baae8734bbf342573ddaf09e19f288a523187a5
Date: 2025-12-01 00:46:04 -0500
Message: cleaned up
Details: Cleaned up SCPI trigger logic in YAKETYYAK.json, transitioning several actuator entries to use explicit boolean flags for improved predictability during command transmission.
**************************************
Commit: 2a229dd125f75d5b8b0427209801b8a4201a8e3b
Date: 2025-12-01 00:44:17 -0500
Message: cleanup
Details: Performed a general cleanup of the YAKETYYAK.json device library, resolving type inconsistencies between integer and string representations of frequency values. Improved the clarity of generic SCPI models for center and span control.
**************************************
