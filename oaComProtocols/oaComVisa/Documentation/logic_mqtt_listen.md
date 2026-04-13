# 🏷️ Manager Logic Mqtt Listen

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
`managers/VisaScipi/manager_visa_mqtt_listen.py`

This manager handles listening to MQTT topics for device connection and control. It acts as the bridge between external MQTT commands (GUI or automation) and the underlying VISA instrument management logic.

**Primary Responsibilities:**
- Monitor MQTT topics for device search, selection, and connection triggers.
- Coordinate resource discovery and session management.
- Offload blocking connection operations to background threads.

Author: Anthony Peter Kuzub

## ⚙️ Assumptions & Constraints
- Assumes a functional MQTT broker is reachable via the `subscriber_router`.
- Payloads are expected to be JSON-encoded (orjson).
- Threaded operations must not exceed system resource limits.

## 📚 API Reference

### Classes
#### `class VisaMqttListener`
Listens for and dispatches instrument-related MQTT commands.

##### `__init__(self, subscriber_router, searcher, connector, disconnector, gui_publisher)`
Initializes the VisaMqttListener with required services and state.

**Parameters:**
- `subscriber_router`: The service used to register for MQTT topic updates.
- `searcher`: The component responsible for discovering VISA resources.
- `connector`: The component that establishes instrument sessions.
- `disconnector`: The component that terminates instrument sessions.
- `gui_publisher`: The service used to broadcast state changes to the UI.

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Assigns service references to internal state and triggers initial subscriptions.

##### `_setup_mqtt_subscriptions(self)`
Registers callbacks for all relevant instrument control topics.

**Parameters:**
- None

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Modifies the `subscriber_router` state by adding multiple subscriptions.

##### `_on_search_request(self, topic, payload)`
Processes a request to search for available VISA instruments.

**Parameters:**
- `topic`: The MQTT topic where the trigger was received.
- `payload`: JSON bytes containing a "value" key (True to trigger search).

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Updates `self.found_resources` with the search results.
- Triggers a GUI update via `gui_publisher`.

##### `_on_device_select(self, topic, payload)`
Updates the selected instrument resource based on GUI selection.

**Parameters:**
- `topic`: The MQTT topic containing the option index.
- `payload`: JSON bytes containing a "value" key (True if selected).

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Updates `self.selected_device_resource`.

##### `_on_gui_connect_request(self, topic, payload)`
Initiates a connection to the selected device from the GUI.

**Parameters:**
- `topic`: The MQTT topic.
- `payload`: JSON bytes containing a "value" key.

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Spawns a background thread to handle blocking I/O during connection.

##### `_connect_and_get_inst(self, resource_name)`
Internal helper to execute connection logic and store the session.

**Parameters:**
- `resource_name`: The VISA resource address.

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Updates `self.inst` with the new resource session.

##### `_on_gui_disconnect_request(self, topic, payload)`
Initiates a disconnection from the current instrument.

**Parameters:**
- `topic`: The MQTT topic.
- `payload`: JSON bytes.

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Spawns a background thread to handle blocking disconnection I/O.

##### `_on_connect_request(self, topic, payload)`
Processes a direct command to connect to a specific VISA resource.

**Parameters:**
- `topic`: The MQTT topic.
- `payload`: JSON bytes containing a "resource" key.

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Spawns a background thread for connection.

## 📝 Focus on Intent (Inline Comments)
- Handle potential retained message cleanup by ignoring empty payloads.
- Extract the index from the topic structure: `.../options/<index>/selected`.
- Offload to thread to prevent MQTT blocking during hardware handshake.
