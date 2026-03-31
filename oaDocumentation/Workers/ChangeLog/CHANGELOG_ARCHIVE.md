# OPEN-AIR Evolutionary Changelog Archive

This document provides a high-level summary of the architectural and functional evolution of the OPEN-AIR project, consolidating monthly logs into key milestones.

---

## August 2025: Foundations of Dynamic GUI and MQTT
- **Key Tool Developments**: Transitioned from static UI definitions to the `dynamic_gui_builder.py` system. Introduced specialized component creators for sliders, value boxes, and toggle buttons.
- **Architectural Shifts**: Commenced the move to an MQTT-centric architecture. Integrated AES70/OCA standards for data structuring and transitioned from legacy CSV files to robust JSON configurations for instrument and application state.
- **Major Feature Milestones**: Implemented real-time GUI updates driven by MQTT. Established the first automated device importing and metadata synchronization workflows.

## September 2025: Instrument Abstraction and "The Yak"
- **Key Tool Developments**: Introduced the "Yak" (YaketyYak) instrument driver library for SCPI command sequencing. Developed the `FrequencySettingsManager` and `SpanSettingsManager` for precise hardware control.
- **Architectural Shifts**: Modularized device definitions into hierarchical JSON. Implemented the `ScpiDispatcher` to abstract hardware interactions. Refined connection management to support real-time device discovery over MQTT.
- **Major Feature Milestones**: Launched the "Marker Hunter" algorithm for automated peak detection. Successfully integrated hardware abstraction for N9340B and N9342CN spectrum analyzers.

## October 2025: Optimization and Peak Hunting
- **Key Tool Developments**: Enhanced the "Marker Hunter" with improved noise floor estimation and peak detection accuracy. Implemented automated bandwidth rounding logic to match instrument-specific step sizes.
- **Architectural Shifts**: Introduced asynchronous marker processing, decoupling the signal analysis loops from the main UI thread to improve responsiveness. Added a "stand-alone" mode to allow operation without an active MQTT broker.
- **Major Feature Milestones**: Implemented peak signal level publication across the system. Resolved cross-platform SCPI dispatch issues, ensuring stability on Linux environments.

## November 2025: Cross-Platform Stability and Versioning
- **Key Tool Developments**: Conducted a major overhaul of the GUI build system to support native execution on both Linux and Windows. Introduced the `MarkerPeakHunterGUI` as a dedicated analysis dashboard.
- **Architectural Shifts**: Standardized versioning and logging headers across all system components. Transitioned to a pack-based layout distribution to resolve GUI scaling conflicts across different display environments.
- **Major Feature Milestones**: Integrated the `MarkerSettingsManager` into the core application launch sequence. Stabilized SCPI trigger sequencing following a period of experimental shifts.

## December 2025: Performance and Authoritative Blueprints
- **Key Tool Developments**: Refactored the `DynamicGuiBuilder` to establish local JSON blueprints as the authoritative source for UI structure, significantly reducing startup latency. Introduced "Map" event listeners for single-instance tab building.
- **Architectural Shifts**: Implemented a `StateMirrorEngine` with early-boot state caching. Standardized the directory-based GUI tab loading system (e.g., `1_Connection`, `2_Frequency`) for better project organization.
- **Major Feature Milestones**: Implemented graceful fallbacks for missing image dependencies (PIL). Achieved significant performance gains in tab switching and high-frequency MQTT update handling.

## January 2026: Fleet Management and Visual Analytics
- **Key Tool Developments**: Introduced the `VisaFleetManager` and `FleetMqttBridge` for comprehensive hardware inventory tracking. Implemented the `OcaTable` GUI for structured device management.
- **Architectural Shifts**: Moved the oaDataRunningFiles/ directory to `.gitignore` to maintain a clean repository. Automated the publication of the entire VISA hardware fleet state directly to the MQTT bus.
- **Major Feature Milestones**: Executed a comprehensive rebuild of bar graphs and needle meters with dynamic range scaling. Implemented multi-threaded hardware discovery for TCP/IP and USB-based instruments.

## February 2026: Process Partitioning and High-Performance UI
- **Key Tool Developments**: Implemented the "Ghost Frame" protocol and "State Tree Pre-Warming" to eliminate UI lag. Introduced a WYSIWYG JSON Editor workspace with syntax highlighting for real-time UI customization.
- **Architectural Shifts**: **Major Milestone**: Partitioned the application into separate Core and UI processes. Introduced "Broker Silence" and "Asynchronous GUI Yielding" to optimize main thread performance.
- **Major Feature Milestones**: Transitioned to `orjson` for high-speed JSON processing. Implementation of asset caching and background rendering. Introduced collapsible "OcaFold" panels for complex layout management.

## March 2026: Inter-Process Communication and Protocol Expansion
- **Key Tool Developments**: Introduced the "Splinker" system for bidirectional data links and loop prevention. Developed the `CommandRouter` with GUID-based packet tracking for forensic data analysis.
- **Architectural Shifts**: Integrated SNMP, OSC, and AES70 agents into a unified, protocol-agnostic discovery framework. Implemented a file-based state mirror for O(1) SNMP reads.
- **Major Feature Milestones**: Launched bidirectional OSC support with source tagging for external control. Developed a hierarchical OID tree view for SNMP monitoring. Integrated the `WorkStealingPool` for optimized multi-threaded task management across partitions.
