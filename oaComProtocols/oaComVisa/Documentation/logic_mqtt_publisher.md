# 🏷️ Manager Logic Mqtt Publisher

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
`managers/VisaScipi/manager_visa_transmit.py`

This manager handles publishing device status and information to the MQTT broker. It synchronizes the internal VISA state with the external GUI and monitoring layers by formatting and dispatching telemetry updates.

**Primary Responsibilities:**
- Update the GUI list of discovered VISA instruments.
- Broadcast real-time instrument connection and metadata status.
- Maintain proxy-level connectivity status for system-wide health monitoring.

Author: Anthony Peter Kuzub

## ⚙️ Assumptions & Constraints
- Assumes the `mqtt_controller` provides a valid, connected paho-mqtt client.
- Supports a fixed maximum of 40 GUI device slots (`MAX_GUI_DEVICE_SLOTS`).
- Dispatches messages with QoS 0 to minimize latency.

## 📚 API Reference

### Classes
#### `class VisaGuiPublisher`
Dispatches instrument telemetry and GUI state updates via MQTT.

##### `__init__(self, mqtt_controller)`
Initializes the VisaGuiPublisher with an MQTT controller.

**Parameters:**
- `mqtt_controller`: The service providing access to the MQTT client.

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Generates a unique 16-bit GUID for session identity.

##### `_update_found_devices_gui(self, resources)`
Updates the GUI's device selection list based on search results.

**Parameters:**
- `resources`: A list of strings containing VISA resource addresses.

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Performs multiple non-blocking MQTT publish operations.

##### `_publish_status(self, topic_suffix, value)`
Publishes a device-specific status value to the broker.

**Parameters:**
- `topic_suffix`: The sub-topic under Device_status (e.g., 'connected').
- `value`: The data to publish (can be bool, string, or number).

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Publishes with the 'retain' flag set to True to ensure persistent state.

##### `_publish_proxy_status(self, status)`
Publishes the high-level proxy connection status.

**Parameters:**
- `status`: A string representing the proxy state (e.g., 'CONNECTED', 'DISCONNECTED').

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Publishes to the `OPEN-AIR/Proxy/Status` topic.

## 📝 Focus on Intent (Inline Comments)
- Populate active slots with discovered resource addresses.
- Clear unused slots to ensure the GUI list reflects the current search.
- Auto-select the first device for user convenience.
- ANTI-FEEDBACK SPEC: Define identity and origin to prevent recursive message loops.
