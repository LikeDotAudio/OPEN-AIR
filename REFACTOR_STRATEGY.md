# OPEN-AIR Refactor Strategy: The Supervisor Tree

## 1. Vision
Transition OPEN-AIR from a monolithic/partitioned architecture to a **Modular Supervisor Tree**. In this model, `oaThreadManager` acts as the root, overseeing independent "Watchdog" Managers that maintain specialized "Blind Worker" threads.

## 2. The Hierarchy
1.  **oaThreadManager (Root):** Orchestrates system boot, reads configuration, and spawns/kills Module Managers.
2.  **Module Managers (Watchdogs):** Protocol-specific (e.g., `oaComVisaManager`). Responsible for thread lifecycle, error handling, and MQTT status heartbeats.
3.  **Workers (Laborers):** The actual logic loops (e.g., `visa_worker.py`). Blind to the rest of the system, communicating only via MQTT.

## 3. Phase 1: The Great Migration (File Moving & Path Resolution)
**Goal:** Move existing code into the new `oa*` structure without breaking functionality.
**Mandate:** DO NOT refactor logic yet. Move files, update imports, and verify stability.

### Data Vault Separation
- All state, cache, logs, and definitions move to `oaData*` silos.
- No code lives in Data Vaults.

### Communication Silos
- Protocols (VISA, MIDI, SNMP, OSC) move to `oaCom*` folders.
- Each silo will eventually house a `manager.py` and a `worker.py`.

### GUI Engine
- Display logic moves to `oaGuiManager`, `oaGuiBuild`, and `oaGuiDestroy`.
- Assets move to `oaGuiElements` and `oaStyle`.

## 4. Communication Handshake
- **Status:** Workers/Managers publish to `oa/status/<module>` (e.g., `{"status": "running"}`).
- **Control:** Supervisor sends to `oa/control/<module>` (e.g., `{"command": "restart"}`).
- **UI:** The GUI reacts to status topics (e.g., turns red on "Error").

## 5. Recovery Protocol
- A task list (`REFACTOR_TASKS.md`) will track progress.
- Each step must be verified by a successful boot before proceeding.
- Critical files (`OpenAir.py`, `config.ini`) will be the last to be fully replaced.
