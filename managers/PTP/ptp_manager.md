# 🏷️ Ptp Manager

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
`managers/PTP/ptp_manager.py`

Monitors Precision Time Protocol (PTP) traffic on the network.

**Primary Responsibilities:**
- Sniffing PTP packets (IEEE 1588) on UDP ports 319 and 320.
- Parsing PTP headers to extract domain, sequence ID, and message type.
- Distributing parsed data to registered observers and MQTT.
- Providing a system heartbeat based on PTP traffic activity.

Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)
Version 20260218.Optimization.1

## ⚙️ Assumptions & Constraints
- **Library Requirement:** Requires the `scapy` library for packet sniffing and parsing.
- **Privileges:** Packet sniffing typically requires root/administrative privileges or specific capabilities (e.g., `CAP_NET_RAW`).
- **Platform:** Optimized for Linux environments where `libpcap` is available for low-level packet capture.
- **Performance:** Sniffing is isolated to a background thread to prevent UI lock contention and ensure real-time packet processing.

## 📚 API Reference

### Global Functions
#### `register_ptp_callback(callback_func)`
Registers a callback function to receive parsed PTP packet data.

**Parameters:**
- `callback_func`: A callable (function or method) that accepts a single dictionary argument containing the parsed PTP data. Must not be `None`.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Modifies the global `_ptp_observers` list by appending the provided callback.
- Not explicitly thread-safe; it is recommended to call this during application initialization.

#### `unregister_ptp_callback(callback_func)`
Unregisters a previously registered PTP callback function.

**Parameters:**
- `callback_func`: The callable instance to remove from the observer list.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Modifies the global `_ptp_observers` list by removing the specified callback.

### Classes
#### `class PtpManager`
Background manager that sniffs PTP traffic and distributes parsed data.

##### `__init__(self, mqtt_connection_manager=None, subscriber_router=None)`
Initializes the PTP manager instance and sets up communication hooks.

**Parameters:**
- `mqtt_connection_manager`: Optional instance of the MQTT manager used for publishing heartbeat messages.
- `subscriber_router`: Optional instance used for subscribing to external PTP data streams.

**Returns:**
- A new `PtpManager` instance.

**Side Effects & Thread-Safety:**
- Initializes internal threading events (`stop_event`) and state variables.

##### `start(self)`
Starts the PTP sniffing worker thread and subscribes to relevant MQTT topics.

**Parameters:**
- None.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Spawns a new daemon thread named `PTP_Sniffer_Worker`.
- Registers a subscription in the `subscriber_router` if one was provided during initialization.

##### `_on_external_ptp_router_data(self, msg)`
Processes PTP data received via MQTT instead of local network sniffing.

**Parameters:**
- `msg`: An `MqttMessage` object. The `payload` should contain PTP data (either as a dictionary or a JSON string/bytes).

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Decodes the payload and invokes all registered callback functions in the global `_ptp_observers` list.

##### `stop(self)`
Signals the background sniffer thread to terminate and waits for its exit.

**Parameters:**
- None.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Sets the internal `stop_event`, which causes the sniffing loop to terminate.
- Joins the sniffer thread with a 1-second timeout.

##### `_run_sniffer(self)`
Executes the continuous packet sniffing loop in a dedicated background thread.

**Parameters:**
- None.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Performs continuous network I/O.
- Will catch and log permission errors if the process lacks the necessary rights to sniff packets.

##### `_process_packet(self, pkt)`
Analyzes a single captured packet to extract PTP-specific information.

**Parameters:**
- `pkt`: A `scapy` packet object captured from the network.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- If a PTP layer is identified, it extracts data, triggers the heartbeat handler, and notifies all registered callbacks.

##### `_tear_apart_ptp(self, pkt, ptp)`
Extracts specific PTP header fields into a simplified dictionary format.

**Parameters:**
- `pkt`: The original `scapy` packet containing network layers (IP, UDP).
- `ptp`: The identified PTP layer object.

**Returns:**
- A dictionary containing: `timestamp`, `source_ip`, `dest_ip`, `udp_port`, `message_type`, `domain`, `sequence_id`, and `clock_identity`.

**Side Effects & Thread-Safety:**
- None.

##### `_format_clock_id(self, raw)`
Converts raw 10-byte `sourcePortIdentity` into a human-readable string.

**Parameters:**
- `raw`: The 10-byte `sourcePortIdentity` field from the PTP header.

**Returns:**
- A string representing the EUI-64 Clock Identity and the Port Number (e.g., "00:11:22:33:44:55:66:77 (Port 1)").

**Side Effects & Thread-Safety:**
- None.

##### `_handle_heartbeat(self, data)`
Publishes a status heartbeat to MQTT if a sufficient interval has passed.

**Parameters:**
- `data`: A dictionary containing the most recently parsed PTP message information.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Performs network I/O by publishing to the `OPEN-AIR/System/PTP/Heartbeat` topic.
- Updates the internal `last_heartbeat` timestamp to enforce the 1Hz rate limit.

## 📝 Focus on Intent (Inline Comments)
- **Scapy Binding:** We explicitly bind `PTP` to UDP ports 319 and 320 to ensure `scapy` correctly identifies these packets even if they don't follow standard heuristic patterns.
- **Thread Isolation:** Sniffing is a blocking I/O operation; running it in a daemon thread prevents it from stalling the main application or GUI.
- **Heartbeat Rate Limiting:** We limit heartbeats to 1Hz to provide "liveness" information to the rest of the system without overwhelming the MQTT broker with redundant traffic.
- **Error Handling:** Permission errors are common when sniffing; we handle them gracefully to allow the application to continue running even if local sniffing is unavailable.
