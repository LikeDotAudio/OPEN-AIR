# oaComProtocols.oaComNmos Module: SAP to NMOS Bridge

This module bridges Session Announcement Protocol (SAP) streams to the NMOS (Networked Media Open Specifications) framework. It discovers audio streams announced via SAP and registers them as NMOS resources, making them discoverable and manageable within an NMOS ecosystem.

## 🏗️ Architectural Overview

The `oaComProtocols.oaComNmos` module has undergone a significant refactoring to adopt a modular, well-organized structure aligned with the project's **12-subfolder standard**. This approach enhances maintainability, testability, and adheres to principles of loose coupling and high cohesion.

The monolithic `SAP2NMOS.py` has been replaced by a collection of specialized modules, each responsible for a distinct part of the application's functionality.

## 📂 Directory Structure & Responsibilities

The module now follows the standard `oa*` module structure:

-   **`oaComProtocols.oaComNmos/`**: Root directory of the module.
    -   **`Entry.py`**: The main orchestrator. Initializes global state, sets up and starts worker threads (SAP listener, heartbeat), launches the NMOS Connection API server, and handles graceful shutdown.
    -   **`__init__.py`**: Makes `oaComProtocols.oaComNmos` a Python package.
    -   **`Constants/`**: Contains configuration settings.
        -   `settings.py`: Holds constants like `PORT`, `SAP_GROUP`, `SAP_PORT`, `STREAM_TIMEOUT`, `HB_INTERVAL`.
        -   `__init__.py`
    -   **`Core/`**: Houses fundamental logic and utilities.
        -   `utils.py`: General helper functions (ID generation, IP fetching, hashing).
        -   `sdp_parser.py`: Logic for parsing SDP messages and building matching keys for sender identification.
        -   `nmos_builder.py`: Functions to construct NMOS resource payloads (Node, Device, Source, Flow, Sender).
        -   `__init__.py`
    -   **`Managers/`**: Contains logic for managing higher-level operations.
        -   `registration_manager.py`: Handles posting NMOS resources (Node, Device, Sources, Flows, Senders) to the NMOS registry.
        -   `sender_cache_manager.py`: Manages caching and retrieving NMOS sender information from the registry to match incoming SAP streams.
        -   `__init__.py`
    -   **`Workers/`**: Implements background tasks.
        -   `sap_listener_worker.py`: Listens for SAP announcements, extracts SDP, and initiates resource registration.
        -   `heartbeat_worker.py`: Periodically sends heartbeats to the NMOS registrar to maintain node presence.
        -   `__init__.py`
    -   **`Interface/`**: Handles external interactions.
        -   `connection_api.py`: Implements the NMOS Connection API server, serving sender status and transport file information.
        -   `__init__.py`
    -   **`Documentation/`**: Placeholder for module-specific documentation.
        -   `__init__.py`
    -   **`Assets/`**: Placeholder for static assets.
        -   `__init__.py`
    -   **`FileReaders/`**: Placeholder for file ingestion logic.
        -   `__init__.py`
    -   **`FileWriters/`**: Placeholder for file export logic.
        -   `__init__.py`
    -   **`Hooks/`**: Placeholder for event listeners and callback registries.
        -   `__init__.py`
    -   **`Tests/`**: Placeholder for unit and integration tests.
        -   `__init__.py`

## 🚀 How to Run

1.  **Prerequisites**: Ensure Python 3 is installed, along with necessary libraries (e.g., `requests`).
2.  **Command Line**: Run the bridge from the project root using:
    ```bash
    python3 oaComProtocols.oaComNmos/Entry.py --registrar <NMOS_REGISTRAR_URL>
    ```
    Replace `<NMOS_REGISTRAR_URL>` with the actual URL of your NMOS registry (e.g., `http://localhost:4000`).

## 💡 Key Components

*   **SAP Listener**: Discovers audio streams announced via SAP multicast.
*   **SDP Parser**: Extracts critical stream information from SDP messages.
*   **NMOS Resource Management**: Dynamically creates and updates NMOS resources (Node, Device, Source, Flow, Sender).
*   **NMOS Registration**: Registers discovered resources with the specified NMOS registry.
*   **NMOS Connection API**: Provides endpoints for NMOS clients to query sender status and retrieve transport information.
*   **Heartbeat Service**: Ensures the node remains registered with the NMOS registry.
*   **Orchestrator (`Entry.py`)**: Manages the overall application lifecycle, threading, and shutdown.

This modular design facilitates easier development, testing, and future expansion of the `oaComProtocols.oaComNmos` module.
