**************************************
Commit: 20ea5f235604b5f4f0bdb4bfad5b792e97f4c698
Date: 2025-09-28 22:10:43 -0400
Message: markers configured but not pushed to mqtt yet
Details: Configured the marker management system to support complex signal categorization, although MQTT publication of marker state remains pending. Synchronized the MARKERS.csv file with a refined set of frequency assignments for Rogers and station Axient mics.
**************************************
Commit: 0a95a707082cb46b490354f50df0a6217cc4a3ee
Date: 2025-09-27 08:52:13 -0400
Message: marker hunter
Details: Introduced the "Marker Hunter" algorithm for automated peak detection and frequency analysis. Expanded the marker database to include a comprehensive set of stage and broadcast frequencies for large-scale event monitoring.
**************************************
Commit: 58c7360f3b6680f08bc97477354f423bf5fdc025
Date: 2025-09-26 00:18:00 -0400
Message: fxing button spacing
Details: Resolved button spacing and text wrapping issues in the Showtime GUI tab, improving the legibility of frequency range labels. Standardized the use of newline characters in dynamic button text generation.
**************************************
Commit: 0b07b7edfe9793e6b10d2c13e99e95c1a00b0e82
Date: 2025-09-26 00:11:02 -0400
Message: must launch with command prompt python "file name"
Details: Updated the application launch instructions to mandate execution via command prompt for better environment variable management. Refined the marker database with updated peak signal data for east and west stage locations.
**************************************
Commit: 12c9ef6a4f2f435da59b266299f157aec04187a6
Date: 2025-09-12 22:59:19 -0400
Message: yak repairs
Details: Conducted extensive repairs on the "Yak" instrument driver library, adding support for the YakBeg command type which allows simultaneous parameter setting and querying. Expanded the YAKETYYAK.json database with detailed SCPI actuator models for N9340B and N9342CN analyzers.
**************************************
Commit: e398ed6b6cec496eeaf5858b013851e96db7f674
Date: 2025-09-10 23:06:41 -0400
Message: refactoring the yak
Details: Initiated a major refactoring of the Yak system, transitioning to a more modular JSON-based architecture for device definitions. Updated SCPI command strings for system reset to improve compatibility across different Keysight hardware versions.
**************************************
Commit: 07a94cde202e9af15772ed8f960ac62df5db625f
Date: 2025-09-10 00:01:49 -0400
Message: working wit the Yak
Details: Successfully integrated the YakityYak agent with the main application, enabling complex SCPI command sequencing for amplitude and attenuation control. Migrated legacy VISA command lists from CSV to the new hierarchical JSON format.
**************************************
Commit: 613a8bd575d7ad0be9a31163a1124f8ed33d7033
Date: 2025-09-07 23:59:36 -0400
Message: refactoring the json of the buttons
Details: Refactored the button JSON schema to support more granular control over actuator behavior and visual feedback. Re-introduced the standard VISA command CSV to facilitate bulk validation of hardware control strings.
**************************************
Commit: 026f8f099d5f76b6c3df8b53c492ce2d4a2449f1
Date: 2025-09-05 00:21:02 -0400
Message: fixing display colours and spacing
Details: Fine-tuned the GUI display by adjusting color themes and widget spacing for better industrial aesthetic consistency. Updated .gitignore to exclude compiled Python files and log artifacts.
**************************************
Commit: 8f86e1052bd5b8357f1b48dec3ce1acce6aef113
Date: 2025-09-04 23:46:07 -0400
Message: gui updated.... devices connecting...   now to yak
Details: Updated the GUI to support real-time device connection status via MQTT. Established the foundation for the Yak-based instrument abstraction layer, removing legacy CSV command files in the process.
**************************************
Commit: c8f5972a3306c28f315116635aa6cfbb75cc86d6
Date: 2025-09-04 01:23:23 -0400
Message: YAK HAS BEGUN RECONSTRUCTION
Details: Commenced the reconstruction of the YaketyYak agent, focusing on a cleaner implementation of the ScpiDispatcher and logging utilities. Standardized the versioning and metadata headers for all Yak-related modules.
**************************************
Commit: a8b40bd36887feaeb7faa746f2f40120d60bc362
Date: 2025-09-03 23:24:48 -0400
Message: connected to device over mqtt
Details: Established device connectivity over MQTT, allowing the GUI to remotely search for and connect to VISA-compatible instruments. Refactored the active instrument configuration to use a more robust listbox-based selection interface.
**************************************
Commit: a69a8428e7ffd9d2495b634efbd3688dee502bb8
Date: 2025-09-03 10:07:29 -0400
Message: connection management over MQTT
Details: Implemented connection management over MQTT, enabling the DynamicGuiBuilder to handle real-time updates to device lists and dropdown options. Resolved an issue where checkbox widgets were incorrectly handled during state updates.
**************************************
Commit: e7bf403a78584195d5e51eb875d8e0414f7b6f97
Date: 2025-09-03 01:27:56 -0400
Message: re-working connection
Details: Refined the Start-Stop-Pause control logic and simplified the instrument averaging configuration by removing redundant JSON definitions. Improved the reliability of the primary program control state machine.
**************************************
Commit: 94762fd29ec8ec788ba725b32c109fa3ef1be23a
Date: 2025-09-02 20:35:58 -0400
Message: active and inactive labels
Details: Added support for active and inactive labels in the YaketyYak agent, providing better visual feedback during long-running VISA operations. Implemented robust error handling and retry logic for the YakBeg query sequence.
**************************************
Commit: 3e9b0bbd0c24847735c66316f6c443fc93f2dd1d
Date: 2025-09-02 12:00:03 -0400
Message: implimenting handler
Details: Implemented the initial SCPI command handler for amplitude and attenuation control, using a standardized CSV-based command dictionary. Established the baseline for cross-manufacturer hardware abstraction.
**************************************
Commit: 5a1acfba72f9f710e3e2e718e2ca91b41649b53d
Date: 2025-09-02 00:02:04 -0400
Message: prest for frequency working
Details: Developed the SpanSettingsManager to handle frequency span presets and synchronization with the main analyzer control. Integrated the new manager into the primary application launch sequence.
**************************************
Commit: 094e63bb48d5d720eec3e155a2065b28f57db2e8
Date: 2025-09-01 23:24:06 -0400
Message: making frequency manager
Details: Established the FrequencySettingsManager and automated the conversion of legacy VISA command sheets into the new Yak-compatible JSON format. Improved the organization of instrument-specific SCPI command strings.
**************************************
