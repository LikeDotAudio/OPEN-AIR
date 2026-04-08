# OPEN-AIR System Architecture: The State-Aware Logic Engine
# Version: 20260407.1930.1

## 1. Executive Summary
OPEN-AIR has evolved from a linear "Message Passthrough" system into a distributed **State-Aware Logic Engine**. By utilizing a central MQTT Storage as a shared "Source of Truth," individual protocol modules operate as independent, asynchronous agents. The system utilizes metadata tagging, asynchronous non-blocking I/O, and the **Protocol Matrix** as the central decision-making hub to ensure absolute decoupling and hardware stability.

---

## 2. Functional Phases

### A. Inbound Phase: Generators & Ingest
*   **Metadata Tagging (`src` ID):** Every receiver and generator wraps raw hardware data in a JSON envelope. For example, a MIDI fader move publishes to `OPEN-AIR/MIDI/` with a unique `src` identifier, critical for downstream echo cancellation.
*   **MQTT Change Detector:** A delta-based "Change Detector" ensures that messages are only asynchronously written to the **MQTT Storage** if the value has changed beyond a defined dead-band (Source Debouncing).
*   **Protocol Monitor (Inbound):** Intercepts traffic between the detector and storage to provide real-time diagnostic telemetry (PPS, bit-rate, and latency) for the GUI.

### B. Core Phase: The Decision Engine
*   **Protocol Matrix (The Virtual Patchbay):** This is the central logic bridge. It maps topics between protocols (e.g., `OSC/Master` → `AES70/Gain`) without direct module coupling. It watches the **MQTT Storage** and publishes "Intents" back to the system.
*   **Protocol Monitor (Mid-Stream):** Monitors the health of the Matrix. If the Matrix logic hangs, the system identifies the failure point without stopping the underlying MQTT traffic.

### C. Outbound Phase: Filtering & Execution
*   **Self-Filter / Echo Remover:** Acts as a gatekeeper for **Output Commands**. It compares the incoming message's `src` tag against the local module ID. If they match, the message is dropped to prevent feedback loops.
*   **MQTT to Protocol Translator:** Translates normalized JSON state values back into physical protocol strings (SCPI for VISA, Hex for MIDI, UDP for OSC).
*   **Asynchronous Output Drivers:** All hardware writes are non-blocking. High-latency devices (like VISA) are handled in dedicated threads to prevent GUI stutter.

---

## 3. The Event Lifecycle: SPLICE, LINK, and SPLINKER
To handle the physical reality of hardware control (e.g., motorized faders and "Ghost Touches"), the system employs three primary micro-logic gates.

### A. The SPLICE (Update Partner)
*   **Role:** The entry gate for a new event.
*   **Behavior:** Identifies the `origin_source` and pairs it with its intended `target_parameter`.
*   **Action:** Triggers **Ghost Touch Unlock**. If a user physically touches a fader, software control is unlocked to prevent the motor from fighting the human hand.

### B. The LINK (The Payload Generator)
*   **Role:** The data packager.
*   **Behavior:** Creates a unique `msg_guid` and attaches state flags:
    *   `is_locked`: Prevents low-priority sources from interrupting the stream.
    *   `is_settled`: Communicates if the value is moving (False) or at its destination (True).
*   **Output:** An **Event Stamp** published to MQTT.

### C. The SPLINKER (Consumer Update)
*   **Role:** The distribution engine.
*   **Behavior:** Receives the **Update Stamp** from MQTT and splits it into two paths:
    1.  **Maker Update:** Updates the GUI and displays in real-time.
    2.  **Consumer Update:** Physically commands hardware (only after passing through Ghost Touch Lock logic).

---

## 4. Protocol Behavioral Matrix
The system supports a wide array of protocols, each with specific asynchronous handling requirements.

| Module | Expected Behavior | Primary Topic Path |
| :--- | :--- | :--- |
| **GUI** | Aggressively debounced; high-priority `src: "oaGui"`. | `OPEN-AIR/GUI/#` |
| **OSC** | Multi-client support; translates `/paths` to `/topics`. | `OPEN-AIR/OSC/#` |
| **MIDI** | Echo-cancellation enabled; 7-bit/14-bit normalization. | `OPEN-AIR/MIDI/#` |
| **ST2138** | High-bandwidth monitoring; Protobuf decoding. | `OPEN-AIR/st2138/#` |
| **VISA** | Query/Response logic; timeout protection. | `OPEN-AIR/Proxy/#` |
| **NMOS** | REST-based registration; SAP discovery. | `OPEN-AIR/NMOS/#` |
| **EMBER** | **Tree Mirroring:** Scans remote trees; only publishes deltas (Lazy Load). | `OPEN-AIR/EMBER/#` |
| **AES70** | **Object Map:** OCA device objects mapped to internal topics. | `OPEN-AIR/AES70/#` |
| **REST** | **Stateless Injection:** Triggers **SPLICE** via HTTP POST. | `OPEN-AIR/REST/#` |
| **SAP** | **Discovery:** Injects multicast stream data into `NMOS/`. | `OPEN-AIR/SAP/#` |
| **Bonjour** | **Zero-Conf:** Finds IP devices and populates `Proxy/`. | `OPEN-AIR/Bonjour/#` |
| **SNMP** | **Legacy Trap:** Translates state to OID for IT monitoring. | `OPEN-AIR/SNMP/#` |
| **HEARTBEAT** | **System Pulse:** 1Hz pulse for Link-State verification. | `OPEN-AIR/SYSTEM/HB` |

---

## 5. Persistence & State Mirroring
*   **State Cache Mirroring:** The Cache only mirrors "Functional State," ignoring volatile telemetry.
*   **Boot:** Injects `last_known_good` from disk to prevent state-shock.
*   **Quit:** Snapshots the functional tree to **Quit Storage**, ensuring a clean state for the next session.
*   **Heartbeat Filter:** Prevents high-frequency heartbeats from bloating the persistent storage.

---

## 6. Summary of System Behavior
*   **Asynchronous:** No module waits for hardware. The **LINK** fires and forgets; the **SPLINKER** catches and executes.
*   **Decoupled:** Modules interact only via the MQTT backbone and the **Protocol Matrix**.
*   **Deterministic:** `src` tags and `msg_guid` ensure traceable, feedback-free communication across the entire ecosystem.
