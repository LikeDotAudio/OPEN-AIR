# oaComBroker/Documentation/oaComBroker.md
#
# Deep-dive architectural documentation for the Protocol Router.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260328.1510.1

# 🧠 The Protocol Router Pipeline: Architectural Deep Dive

The `ProtocolRouter` is a singleton orchestrator that relies on a multi-threaded 
`ThreadPoolExecutor` (defaulting to 4 threads) to dispatch traffic. When a 
message arrives from *any* transport, it travels through a strict data pipeline.

---

## 🛠️ The Processing Pipeline

### 1. Ingestion & Normalization (`ingest.py`)
*   **Unified Schema**: Raw data is immediately normalized into a strict 
    dictionary schema containing timestamps, logical sources, topics, and values.
*   **Identity Tagging**: The system injects `msg_guid`, `msg_type` (e.g., 
    `SPLICE_ACTION`), and `origin_source` to prevent infinite network loops.
*   **Silent Boot**: Messages tagged with `boot: True` bypass normal logging and 
    are ingested silently to prevent log flooding during startup.

### 2. Settling & Anti-Feedback (`settle.py`)
*   **Interaction Locks**: To prevent jitter when a user moves a physical fader, 
    the parameter is temporarily "locked."
*   **Debounce Timer**: A 50ms silence timer is started.
*   **Terminal Feedback**: Once 50ms passes without new data, the router fires 
    a final `LINK_FEEDBACK` message marked as `is_settled: True`, unlocking 
    the parameter.

### 3. Deep Packet Inspection (`dpi.py`)
*   **Metadata Enrichment**: The system executes DPI to append rich forensic data.
*   **Protocol Translation**: It resolves SNMP OIDs from a MIB cache, unpacks raw 
    MIDI bytes (flagging clock signals vs. CCs), and detects large configuration 
    blobs (over 1000 bytes).

### 4. Strategy & UI Tagging (`strategy.py`)
*   **Emoji Routing Map**: The router uses a visual emoji string to dictate 
    where the packet needs to go. 
*   **Reflection Prevention**: Messages matching the router's own 
    `FULL_INSTANCE_ID` coming from MQTT are flagged as `IGNORE (REFLECT)` 
    to stop echo loops.

| Source | Default Emoji Strategy | Description |
| :--- | :--- | :--- |
| **GUI** | `Ⓖ 🚀 💾 Ⓜ️ 🅾️ Ⓢ 🎹` | Broadcasts everywhere. |
| **OSC** | `🅾️ 🚀 💾 Ⓖ` | Goes to UI, Cache, and MQTT. |
| **MIDI** | `🎹 🚀 💾 Ⓖ` | Goes to UI, Cache, and MQTT. |

### 5. Outbound Dispatch (`dispatch.py`)
*   **Protocol Guards**: Outbound functions are wrapped in `@protocol_guard` 
    decorators for robust error handling.
*   **Network Delivery**: Depending on the strategy string, the payload is 
    handed to the respective network manager (`_dispatch_mqtt`, `_dispatch_osc`, 
    etc.) for remote transmission.

---

## 🔬 Telemetry & Forensics (`monitor.py`)
The router never hides its work. The `Monitor` class maintains a 2000-message 
rolling buffer (the `firehose`). 

It exposes tools for UI dashboards, including:
*   **`get_dpi_report(ts)`**: Generates a formatted, human-readable forensic 
    report for any specific packet, showing its lifecycle, session origin, and 
    pretty-printed JSON payload.
*   **`get_splink_relationship(ts)`**: Correlates a message with its connected 
    "Splink" partner across the network.
