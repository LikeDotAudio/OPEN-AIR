# 🏷️ Visa Fleet Manager

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
`managers/Visa_Fleet_Manager/visa_fleet_manager.py`

Orchestrates the discovery and management of VISA-compatible instruments across the network.

**Primary Responsibilities:**
- Coordinating instrument discovery via the `DiscoveryOrchestrator`.
- Managing a persistent inventory of fleet devices in JSON and CSV formats.
- Bridging fleet data and commands between the core logic and MQTT.
- Providing a thread-safe interface for sending SCPI commands to specific devices.

## ⚙️ Assumptions & Constraints
- **Library Dependencies:** Relies on `orjson` for high-performance JSON serialization and `loguru` for structured logging.
- **Component Availability:** Assumes the existence of `VisaJsonBuilder`, `VisaCsvBuilder`, and `MqttFleetBridge` within the same package.
- **Persistence:** Standardizes on local JSON files for state persistence, with CSV exports for external tool compatibility.
- **Threading:** Uses a thread-safe command queueing model to allow multiple components to interact with instruments without blocking the main event loop.

## 📚 API Reference

### Classes
#### `class VisaFleetManager`
Commander for the VISA instrument fleet, managing discovery, inventory, and communication.

##### `__init__(self, mqtt_connection_manager=None, subscriber_router=None, aes70_manager=None)`
Initializes the `VisaFleetManager` and its constituent components.

**Parameters:**
- `mqtt_connection_manager`: Instance of the MQTT connection manager for network communication.
- `subscriber_router`: Instance for routing MQTT subscriptions to local handlers.
- `aes70_manager`: Optional manager for AES70-specific device discovery logic.

**Returns:**
- A new `VisaFleetManager` instance.

**Side Effects & Thread-Safety:**
- Loads the initial fleet inventory from local JSON storage.
- Initializes the MQTT bridge and registers scan trigger callbacks.

##### `set_callbacks(self, on_inventory_update, on_device_response, on_device_error, on_proxy_status)`
Links external listeners (such as a GUI or higher-level automation logic) to internal fleet events.

**Parameters:**
- `on_inventory_update`: Callable that receives the updated flat inventory list.
- `on_device_response`: Callable that receives SCPI query responses.
- `on_device_error`: Callable that receives error notifications from device proxies.
- `on_proxy_status`: Callable that receives device status changes (e.g., Online/Offline).

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Updates internal callback references.

##### `start(self)`
Activates the fleet manager and its orchestrator.

**Parameters:**
- None.

**Returns:**
- `None`.

##### `stop(self)`
Gracefully shuts down the discovery orchestrator and disconnects from the MQTT broker.

**Parameters:**
- None.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Stops all background threads managed by the `DiscoveryOrchestrator`.
- Disconnects the `MqttFleetBridge`.

##### `trigger_scan(self)`
Initiates a comprehensive network scan to discover and manage VISA instruments.

**Parameters:**
- None.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Clears the `initial_scan_complete_event`.
- Publishes scan status messages (Start/Complete) to the MQTT broker.

##### `wait_for_initial_scan(self, timeout=None)`
Blocks the calling thread until the first device scan is complete.

**Parameters:**
- `timeout`: Maximum number of seconds to wait. Use `None` for an infinite wait.

**Returns:**
- `True` if the scan completed successfully; `False` if the timeout was reached.

**Side Effects & Thread-Safety:**
- Synchronously blocks the execution of the calling thread.

##### `_publish_scan_status(self, status, payload)`
Publishes the current progress of a fleet scan to the MQTT status topic.

**Parameters:**
- `status`: A string representing the scan phase (e.g., "Start", "Complete").
- `payload`: A dictionary of data to be serialized as JSON and sent as the MQTT payload.

**Returns:**
- `None`.

##### `enqueue_command(self, serial, command, query=False, correlation_id="N/A")`
Sends a SCPI command or query to a specific instrument identified by its serial number.

**Parameters:**
- `serial`: The unique serial number of the target instrument.
- `command`: The SCPI string to be executed by the instrument.
- `query`: A boolean indicating if a response is expected from the instrument.
- `correlation_id`: An optional tracking ID to match responses to requests.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Queues the command in the appropriate device proxy's worker thread.
- Triggers the error callback if the specified serial number is not found in the fleet.

##### `_notify_inventory(self, inventory_data)`
Receives raw inventory data from the orchestrator, augments it with metadata, and persists it.

**Parameters:**
- `inventory_data`: A list of raw device dictionaries discovered by the orchestrator.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Persists the augmented inventory to both JSON and CSV files.
- Triggers the `cb_inventory` callback and publishes grouped inventory data to MQTT.

##### `_notify_response(self, serial, response, command, corr_id)`
Handles an incoming SCPI query response from a device proxy.

**Parameters:**
- `serial`: The serial number of the responding device.
- `response`: The raw string response from the instrument.
- `command`: The original query command that prompted the response.
- `corr_id`: The correlation ID associated with the request.

**Returns:**
- `None`.

**Side Effects & Thread-Safety:**
- Persists the response to a timestamped JSON file for audit logging.
- Triggers the `cb_response` callback.

##### `_notify_error(self, serial, message, command)`
Relays an error reported by a device proxy to the registered error callback.

**Parameters:**
- `serial`: The serial number of the device reporting the error.
- `message`: A description of the error encountered.
- `command`: The command that was being executed when the error occurred.

**Returns:**
- `None`.

##### `_notify_status(self, serial, status)`
Relays a status change reported by a device proxy to the registered status callback.

**Parameters:**
- `serial`: The serial number of the device.
- `status`: The new status string (e.g., "Online", "Disconnected").

**Returns:**
- `None`.

##### `current_inventory(self)`
Returns the most recent list of discovered instruments.

**Parameters:**
- None.

**Returns:**
- A list of dictionaries representing the current fleet inventory.

## 📝 Focus on Intent (Inline Comments)
- **JSON Augmentation:** We augment raw device data with human-friendly metadata (manufacturer, model) to improve the usability of the UI and exported files.
- **Standalone Orchestration:** The manager is designed as a standalone orchestrator to ensure that core instrument management logic remains decoupled from specific UI or communication protocols.
- **Persistent State:** By loading inventory on startup, we ensure that the system has immediate knowledge of the fleet even before a new network scan is completed.
- **CSV Regeneration:** CSV files are automatically regenerated alongside JSON updates to support users who integrate fleet data with external spreadsheet software.
