**************************************
Commit: c52a60edcc76e5f52a23562f37d6b15ec88fb140
Date: 2025-08-29 02:01:39 -0400
Message: more and more working
Details: Refactored `dynamic_gui_builder.py` by removing redundant code and simplifying the GUI building process. It also updated the dataset configuration for Start-Stop-Pause operations, enhancing the overall efficiency of the GUI generation.
**************************************
Commit: 60d51398edc1e02bc8f729bdb4569942f655d189
Date: 2025-08-29 01:50:07 -0400
Message: fixed toggle buttons...
Details: Focused on fixing toggle buttons and improving the dropdown option implementation within the dynamic GUI builder. Significant changes were made to `gui_start_pause_stop.py`, streamlining the control logic and preparing for further dropdown enhancements.
**************************************
Commit: 83c38a8d506175bf7431a96c97be5156ec97f376
Date: 2025-08-28 23:53:50 -0400
Message: cleaning up controls
Details: Cleaned up instrument control datasets, including amplitude and bandwidth configurations, to ensure consistency. The commit also updated the toggle button and dropdown creation logic to better handle these refined datasets.
**************************************
Commit: 7befbcfd80d7ad6e9c3b3f1652140e69652f3169
Date: 2025-08-28 22:26:32 -0400
Message: mqtt dynamically creating values .... wow!!!!
Details: Introduced dynamic MQTT value creation, allowing the GUI to automatically adapt to incoming MQTT messages. This innovation involved updates across various GUI component creators, such as actuators and sliders, to support dynamic value binding.
**************************************
Commit: 6817c52d736f9d4767a1e5e7d880af6e60a46d61
Date: 2025-08-28 02:07:13 -0400
Message: GETTING BETTER   ISSUE WITH TOPIC PUBLISHING
Details: Addressed issues with MQTT topic publishing by refining the topic structure and delimiter usage. The commit also expanded the dynamic GUI builder's capabilities, adding more robust handling for sliders, value boxes, and button togglers.
**************************************
Commit: 72d12a431ae06ac01f59962e8ea9ad845cf65ee8
Date: 2025-08-28 00:32:22 -0400
Message: gui fixing
Details: Undertook a massive GUI restructuring by removing numerous legacy worker components and consolidating them into a more centralized dynamic GUI builder system. This commit also involved extensive updates to instrument datasets, including new configurations for averaging, amplitude, and frequency, while streamlining the MQTT subscriber logic.
**************************************
Commit: aeb0e7cb19658e878644d75ed6da8759eb6d3bd7
Date: 2025-08-27 20:11:24 -0400
Message: buttons displaying again
Details: Restored the visibility of GUI buttons by refining the dynamic MQTT subscriber and builder logic. The changes ensured that incoming MQTT messages correctly trigger GUI updates, specifically focusing on the reliable rendering of control elements within the `gui_display.py` module.
**************************************
Commit: 5733d92bd17f4479282f35f7f37e6015081c027e
Date: 2025-08-27 20:02:12 -0400
Message: correcting the gui builder some more
Details: Further corrected the dynamic GUI builder by introducing a dedicated MQTT subscriber utility for GUI elements. This update included a complete overhaul of several GUI sub-tabs, such as connection, frequency, and amplitude, ensuring they are properly initialized and reactive to system state changes.
**************************************
Commit: 60546463150138e782617f42da53f5826626a370
Date: 2025-08-27 18:45:23 -0400
Message: major reversion for MQTT  before rabbit change over
Details: Executed a major reversion of the MQTT system in preparation for a transition to RabbitMQ, involving substantial cleanup of instrument datasets. Many legacy GUI components were simplified or removed, and the application configuration structure was refined to better handle file paths and instrument status.
**************************************
Commit: b5b0a5418f2844369c01174048152be7bbf4c851
Date: 2025-08-27 15:59:51 -0400
Message: cleaning datasets
Details: Continued the dataset cleaning process by splitting the large monolithic instrument configuration into smaller, more manageable JSON files for amplitude, bandwidth, frequency, markers, and traces. This modular approach improves the maintainability of the configuration system and integrates directly with the updated dynamic GUI builder.
**************************************
Commit: 097e406e0adcc950f9e5b5d8dda7e08068c5bfb2
Date: 2025-08-27 15:34:01 -0400
Message: dynamic display much better
Details: Significantly improved the dynamic display by implementing a comprehensive set of GUI component creators, including toggle buttons, sliders, and value boxes. This change involved a major cleanup of legacy GUI files and a restructuring of the dataset repository to support the new dynamic building process.
**************************************
Commit: 320682685e5fd834b00fb41e489a5259c66dfd40
Date: 2025-08-27 01:06:16 -0400
Message: gui from MQTT....
Details: Integrated MQTT-driven GUI updates, allowing the interface to dynamically reflect system state changes received via MQTT. Numerous sub-tabs across the application were updated to support this real-time data binding, enhancing the responsiveness and interactivity of the user interface.
**************************************
Commit: f53fddfb6d7c7aea97bbe63579fc740e3c29065f
Date: 2025-08-27 00:26:38 -0400
Message: gui gnerated from MQTT messages
Details: Established the foundational logic for generating GUI components directly from MQTT messages. This commit added several new GUI scripts and updated existing ones to handle a wide range of instrument settings, from frequency and bandwidth to markers and traces, all powered by MQTT.
**************************************
Commit: 9e03dab41212cccc958600272ecebc42cf387053
Date: 2025-08-26 23:20:34 -0400
Message: aes70 oca structure
Details: Refined the application's data structure to align with AES70/OCA standards, particularly within the JSON dataset configurations. This architectural improvement ensures a more standardized and scalable way to manage instrument settings, presets, and report configurations.
**************************************
Commit: f405c86648eba1041e0827667cf90c41077aba9b
Date: 2025-08-26 00:28:03 -0400
Message: way better data srtructure for control buttons.... steps away from dynamic button and control making
Details: Introduced a much-improved data structure for control buttons, marking a significant step towards fully dynamic control generation. The commit also involved removing legacy CSV-based data files in favor of a more robust and flexible JSON-centric approach.
**************************************
Commit: 527cd118317b5e86f82d7d823c67a1d2f6dc7edd
Date: 2025-08-26 00:00:20 -0400
Message: better json structure
Details: Standardized the JSON structure across the entire dataset collection, ensuring consistency between application, instrument, and plotting configurations. This comprehensive refactoring also included updates to several GUI components and handlers to accommodate the new unified data model.
**************************************
Commit: b6390b07116af2f43793eed72c3f1d072e00da24
Date: 2025-08-25 22:29:11 -0400
Message: better data model - with MQTT
Details: Optimized the data model for MQTT integration, introducing more granular datasets for frequency bands and meta-components. The commit also restructured several GUI sub-tabs to better handle these refined datasets, improving the overall organization of the user interface.
**************************************
Commit: 22d0d4f35e481f487182b4a25eb8d7f8bbc7d5d6
Date: 2025-08-25 19:51:44 -0400
Message: meta data edit pushed to mqtt
Details: Enabled metadata editing with direct synchronization to MQTT, allowing users to update component information that is immediately propagated through the system. This update also included refinements to the application's styling and styling handlers.
**************************************
Commit: e98a9e26926d00f49fc714057b7d8ea954f2cb33
Date: 2025-08-25 19:39:40 -0400
Message: meta data and other datasets being read nicely
Details: Improved the reading and handling of metadata and other complex datasets, particularly for instrument components like amplifiers and antennas. This commit ensured that these datasets are correctly loaded and displayed within the GUI's metadata management section.
**************************************
Commit: b441c2d74d656ee40a28e5b4c7d59edbba81afa7
Date: 2025-08-25 19:03:44 -0400
Message: devices importing now
Details: Implemented a robust device importing mechanism, allowing the application to dynamically load and configure meta-devices. This change also included a major update to the sweeping configuration and the introduction of dedicated GUI sub-tabs for managing different meta-device types.
**************************************
Commit: 759f5e9e4130553dd3239e1baf25b704a60798be
Date: 2025-08-25 18:20:45 -0400
Message: minimalist editor
Details: Introduced a minimalist editor for markers and presets, simplifying the user interface for these common tasks. The commit also added support for VISA and marker CSV files, providing a more direct way to manage these data types.
**************************************
Commit: 9d88efe08a19b64cc606e9e04400aad333a05f99
Date: 2025-08-25 17:15:36 -0400
Message: gui cleanup for flattening
Details: Cleaned up the GUI structure for flattening, removing large debug logs and redundant files to improve performance. This refactoring also focused on simplifying the instrument translator and marker editor, making the codebase more maintainable.
**************************************
Commit: 5017f82654193a12a941170f24ff40d3a8f8f141
Date: 2025-08-25 01:36:22 -0400
Message: more mqtt stuff.... should not pupulate when active = false
Details: Enhanced the MQTT integration by preventing data population for inactive components, thereby reducing unnecessary processing. The commit also included significant updates to the MQTT data flattening worker and several GUI editors to better handle complex datasets.
**************************************
Commit: 0386cb6391c8dcc7c806359139382af53af9b14b
Date: 2025-08-24 21:17:31 -0400
Message: parsed
Details: Refined the MQTT data parsing logic within the flattening worker to improve the accuracy and speed of data processing. This update ensured that incoming messages are correctly interpreted and routed to the appropriate GUI components.
**************************************
Commit: 3ce54e48c83ba9819da364ea55c2263811979569
Date: 2025-08-24 20:50:13 -0400
Message: pivoting mqtt
Details: Pivoted the MQTT implementation to support a more flexible data structure, including the introduction of SCPI-based device configurations. This innovation allows for more direct control of instruments via MQTT, supported by a new logging worker and improved translation logic.
**************************************
Commit: 8138dd57586c66db309722bd3a3c716bd80c5332
Date: 2025-08-24 12:33:52 -0400
Message: visa command parsing
Details: Refined VISA command parsing by introducing a comprehensive SCPI device dataset and a dedicated CSV export utility. The commit also updated the GUI translator and styling to better handle the newly parsed instrument commands and their associated metadata.
**************************************
Commit: a2db143594586f9c733390980c041d9e27f7fc67
Date: 2025-08-24 01:51:19 -0400
Message: learning MQTT
Details: Focused on advanced MQTT learning and integration, specifically refining the MQTT conductor and controller utilities. This work included the addition of a robust CSV export worker and significant cleanup of large debug logs to streamline development.
**************************************
Commit: f0d3e3447bc2e44aad8c1db718009cf73de206e0
Date: 2025-08-24 01:05:22 -0400
Message: first mqtt parse
Details: Performed the first major MQTT data parse, introducing a wide array of program-specific datasets for markers, presets, and scanning. This foundational work also involved a significant restructuring of the application's main loop and worker configuration to support a data-driven GUI.
**************************************
Commit: 3c6084fc734a11acf8519a533374e5092c21257e
Date: 2025-08-23 21:22:16 -0400
Message: more mqtt tie in
Details: Deepened the MQTT integration by tying more GUI elements to the MQTT bus and introducing a dedicated MQTT conductor for orchestration. The commit also included extensive updates to the project's crawl logs and a redesign of the start/stop control logic.
**************************************
Commit: e08d1689388c682e4da2b8cf485de9e2d6c3c24a
Date: 2025-08-23 19:45:36 -0400
Message: with JSON for all datasets
Details: Standardized the use of JSON for all datasets, ensuring that instrument, marker, and sweeping configurations are consistently handled across the application. This commit also involved refinements to the GUI's tab structure and the introduction of more granular control over instrument settings.
**************************************
Commit: 82e4b4e671bf99d1e554d1c2faf6659d359d99e8
Date: 2025-08-23 11:24:12 -0400
Message: data sets in MQTT
Details: Migrated several key datasets to MQTT, enabling real-time synchronization of instrument settings and sweeping configurations. This update also included improvements to the GUI's responsiveness and the introduction of new utility functions for managing MQTT-based data streams.
**************************************
Commit: 92002054665cd9fed0d8ce8b9a3e964cd1a29d85
Date: 2025-08-23 02:18:30 -0400
Message: major progress importing guis
Details: Achieved major progress in importing GUIs dynamically from configuration files, supported by a more robust MQTT-driven architecture. This commit also streamlined the handling of instrument connections and settings, ensuring a more seamless user experience.
**************************************
Commit: 2b1eb9b10065dd670ebb9f482f3b9d8163ff9675
Date: 2025-08-23 00:19:54 -0400
Message: gui elements tied to MQTT
Details: Tied various GUI elements directly to the MQTT bus, allowing for real-time updates and control of instrument parameters. This innovation also involved updates to the styling and layout of the GUI to better accommodate dynamic content.
**************************************
Commit: cf33090dba153720eb54a858ab55839b0f3b37be
Date: 2025-08-22 23:43:13 -0400
Message: now with MQTT
Details: Fully transitioned the application to an MQTT-centric architecture, with a significant overhaul of several GUI sub-tabs and the introduction of a dedicated MQTT controller utility. This shift enables more modular development and better separation of concerns between the GUI and underlying instrument logic.
**************************************
Commit: 14a792998ed0ad64bef80f51d74b836313a7ceb3
Date: 2025-08-22 21:35:47 -0400
Message: befor MQTT rehash
Details: Prepared the codebase for a major MQTT rehash by refining the logging and display logic. This commit also included substantial updates to the instrument translator and the right-side control panel, ensuring they are ready for the upcoming architectural changes.
**************************************
Commit: ccda5da1e5fc04b11562636c12e21bdc1ff48a7d
Date: 2025-08-22 01:41:20 -0400
Message: fixed path
Details: Fixed a path issue within the GUI display module, ensuring that internal references and asset loading are correctly handled. This minor but critical fix improves the stability of the application's visual interface.
**************************************
Commit: a7b15a7c222cbabb7feb291f2091694b9683d0a1
Date: 2025-08-22 01:39:08 -0400
Message: fixed a little
Details: Refined the GUI display and styling logic to improve the overall look and feel of the application. These changes focused on subtle layout adjustments and more consistent application of visual styles across different tabs.
**************************************
Commit: 84bc576dc765f393a2b5537387bf769f1669bc85
Date: 2025-08-22 01:25:47 -0400
Message: magical display
Details: Introduced "magical display" improvements, enhancing the visual rendering and responsiveness of the GUI. This update involved significant refinements to the `gui_display.py` module, optimizing the way elements are drawn and updated.
**************************************
Commit: 0c3795eacc163723f92d0441f9b9db9b2409a372
Date: 2025-08-22 01:22:20 -0400
Message: new gui layout
Details: Implemented a completely new GUI layout, involving a major restructuring of the project's folder hierarchy and the introduction of several new sub-tabs. This layout overhaul also included improvements to configuration management and the way instrument settings are restored.
**************************************
Commit: fd12cc6eac88c7b2416b9d04713056710d21323f
Date: 2025-08-21 18:15:13 -0400
Message: file cleanup
Details: Conducted a thorough file cleanup, removing outdated crawl logs and legacy HTML reports to reduce repository size and clutter. This housekeeping task ensures that the codebase remains focused and easy to navigate.
**************************************
Commit: be755ef76dab5b8fee7cc0036277fc8575921377
Date: 2025-08-21 18:12:59 -0400
Message: wrangling in the modularity
Details: Focused on "wrangling modularity" by restructuring the instrument and VISA interpreter logic into more discrete, manageable modules. This commit also included improvements to preset management and refined the way file paths are handled within the application.
**************************************
Commit: e1b0364bd099aa95b12d3b26c537ad193ace98fb
Date: 2025-08-21 15:41:33 -0400
Message: fixing sash
Details: Fixed an issue with the GUI's sash control, ensuring that resizable panels behave correctly across different screen sizes. This update also included refinements to the configuration file structure and file path handling.
**************************************
Commit: ddf33d5dfa28c223c70ed7b9ba3ac31c7fdc774f
Date: 2025-08-21 15:24:05 -0400
Message: configuration refactoring
Details: Performed a major refactoring of the configuration system, introducing dedicated modules for managing application, instrument, and marker settings. This architectural shift significantly improves the organization and extensibility of the program's configuration logic.
**************************************
Commit: f832c0e5a7112de6977ca205d612821f4d651184
Date: 2025-08-21 13:32:46 -0400
Message: major file moves...
Details: Executed several major file moves to better organize the codebase, particularly around the settings and configuration modules. This structural update ensures that related components are grouped logically, making the project easier to maintain.
**************************************
Commit: 0f44edf86964cac9f7a331e81cdec8e42dec0580
Date: 2025-08-21 13:26:50 -0400
Message: moved out the tabs and saving and config folders
Details: Moved out several key tab and configuration folders to a more centralized location, further improving the project's structural integrity. This refactoring also involved updating numerous internal references to ensure the application remains functional after the move.
**************************************
Commit: 8225fa80904d32cd649f3705ef061bb435cad7dd
Date: 2025-08-21 12:51:26 -0400
Message: configuration saving
Details: Enhanced the configuration saving mechanism, ensuring that application, instrument, and preset settings are reliably persisted. This update also included significant refinements to several experimental sub-tabs and improved the overall initialization process.
**************************************
Commit: 1ed51e5a8adcd45dc44c631a3c583297a62207a3
Date: 2025-08-21 11:04:58 -0400
Message: refactored configuration system
Details: Fully refactored the configuration system by splitting it into specialized managers for different functional areas like scanning, plotting, and report generation. This change also involved a massive cleanup of legacy crawl logs and improvements to the shared value management system.
**************************************
Commit: 4a7e00fbd9d40ee08611a5622b4370640d510eca
Date: 2025-08-21 09:15:12 -0400
Message: marker refactoring
Details: Undertook a refactoring of the marker system, specifically improving the way marker groups and zones are displayed and managed within the GUI. These changes enhance the clarity and usability of the marker-related controls.
**************************************
Commit: 1a1ba1bb008d57742fc16687b5d586efed69dd01
Date: 2025-08-21 02:26:00 -0400
Message: so much refactoring - lots of smaller more manageable files....
Details: Executed an extensive refactoring effort, breaking down large monolithic files into smaller, more manageable units. This work focused on improving the clarity of the configuration manager and the various GUI control components, making the codebase much easier to navigate and understand.
**************************************
Commit: c05acf79507103820ebabc213bb18544307341cf
Date: 2025-08-20 23:48:13 -0400
Message: more configuration fixing
Details: Fixed several issues within the configuration system and refined the program's initialization and shared value management. This commit also streamlined the control logic for markers and improved the reliability of settings restoration.
