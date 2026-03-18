# 🏷️ Manager Fleet Mqtt Bridge

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
`managers/Visa_Fleet/fleet_mqtt_bridge.py`

Bridges the internal state and control operations of the Visa Fleet Manager with the MQTT ecosystem.

**Primary Responsibilities:**
- Subscribing to fleet-wide control topics (e.g., Scan triggers).
- Publishing discovered device inventory as a hierarchical MQTT structure for observability.
- Facilitating the distribution of device-specific data via a shared MQTT manager.

## ⚙️ Assumptions & Constraints
- **Library Dependencies:** Requires `orjson` for fast JSON serialization.
- **Network Interface:** Relies on a shared `mqtt_connection_manager` for network I/O.
- **Message Routing:** Uses a `subscriber_router` to manage incoming control message handlers.
- **Data Structure:** Hierarchical publishing is designed for nested dictionaries and lists; other types are converted to strings.

## 📚 API Reference

### Classes
#### `class MqttFleetBridge`
Handles the MQTT representation of the instrument fleet and its remote control hooks.

##### `__init__(self, mqtt_connection_manager, subscriber_router, topic_prefix=None)`
Initializes the MQTT bridge and sets up initial communication parameters.

**Parameters:**
- `mqtt_connection_manager`: The shared instance used for message publication.
- `subscriber_router`: The instance used to register for incoming control messages.
- `topic_prefix`: The root MQTT topic for all fleet-related messages.

**Returns:**
- A new `MqttFleetBridge` instance.

**Side Effects & Thread-Safety:**
- Automatically registers MQTT subscriptions via the provided `subscriber_router`.

##### `_setup_subscriptions(self)`
Configures the internal MQTT listeners for fleet control operations.

**Parameters:**
- None.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Modifies the state of the `subscriber_router`.

##### `is_connected(self)`
Checks the connection status of the underlying MQTT manager.

**Parameters:**
- None.

**Returns:**
- `True` if the MQTT manager is connected; `False` otherwise.

##### `_on_scan_message(self, msg)`
Processes incoming MQTT messages that trigger a fleet-wide instrument scan.

**Parameters:**
- `msg`: An `MqttMessage` object containing the trigger payload (expects "TRIGGER").

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Invokes the `on_scan_trigger` callback if it has been assigned.

##### `publish_inventory(self, inventory_data)`
Publishes the entire fleet inventory to the MQTT broker using a hierarchical topic structure.

**Parameters:**
- `inventory_data`: A dictionary representing the organized fleet inventory.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Performs a series of recursive MQTT publication operations.

##### `_publish_flattened_dict(self, data, base_topic)`
Recursively maps nested data structures (dicts and lists) to a hierarchy of MQTT topics.

**Parameters:**
- `data`: The data node (dict, list, or value) to be processed.
- `base_topic`: The current MQTT topic path for this node.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Performs recursive network I/O.
- Sanitizes keys by replacing "/" with "_" to maintain valid MQTT topic paths.

##### `disconnect(self)`
Gracefully shuts down the bridge's local listeners.

**Parameters:**
- None.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Does **not** disconnect the shared MQTT manager, as it may be in use by other components.

## 📝 Focus on Intent (Inline Comments)
- **Sanitized Keys:** We replace forward slashes in dictionary keys with underscores to ensure that internal data keys do not inadvertently create unwanted MQTT sub-topic hierarchies.
- **Device Blobs:** When a dictionary is identified as a complete device record (containing serial, model, etc.), we publish it as a single indented JSON blob to make it easier for external subscribers to consume the full device state in one message.
- **Shared Manager:** The bridge uses a shared MQTT manager to minimize resource consumption and avoid redundant network connections.
- **Recursive Mapping:** Flattening the inventory into topics allows fine-grained observability, where a subscriber can listen to a specific attribute of a specific device without parsing a massive JSON blob.
