# 🏷️ Manager Visa Proxy

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
`managers/VisaScipi/manager_visa_proxy.py`

This manager provides a safe, low-level interface for executing SCPI write and query commands via PyVISA. It acts as a command queue and execution engine for instrument communication, ensuring that I/O operations are serialized and handled gracefully in a background thread.

**Primary Responsibilities:**
- Maintain a thread-safe command queue for SCPI operations.
- Coordinate background execution of write and query commands.
- Manage the lifecycle of the instrument session proxy.
- Listen for inbound MQTT commands and dispatch results/errors.

Author: Anthony Peter Kuzub

## ⚙️ Assumptions & Constraints
- Assumes only one instrument is active at a time per proxy instance.
- Blocking VISA I/O is offloaded to a dedicated worker thread.
- MQTT payloads must follow the project's standard command format.

## 📚 API Reference

### Classes
#### `class VisaProxy`
Manages the PyVISA connection and provides safe, serial command execution.

##### `__init__(self, mqtt_controller, subscriber_router)`
Initializes the VisaProxy with MQTT and subscription services.

**Parameters:**
- `mqtt_controller`: The service used for MQTT publishing.
- `subscriber_router`: The service used for MQTT topic registration.

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Initializes an internal command queue and state variables.

##### `shutdown(self)`
Terminates the command processor worker thread gracefully.

**Parameters:**
- None

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Signals the worker thread to stop and joins it.
- Resets thread and flag state to `None`.

##### `_command_processor_worker(self)`
Background worker loop that executes queued SCPI commands.

**Parameters:**
- None

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Continuously polls the command queue until shutdown is signaled.
- Executes blocking VISA I/O operations (write/query).
- Handles and logs exceptions during command execution.

##### `_setup_mqtt_subscriptions(self)`
Registers the inbound command inbox topic.

**Parameters:**
- None

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Modifies the `subscriber_router` state.

##### `_on_tx_inbox_message(self, msg)`
Handles inbound MQTT messages intended for instrument execution.

**Parameters:**
- `msg`: The `MqttMessage` object containing the command payload.

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Enqueues command information for the background worker thread.

##### `_publish_proxy_error(self, message, command)`
Logs and publishes proxy-level error information.

**Parameters:**
- `message`: Detailed error description.
- `command`: The SCPI command that caused the error.

**Returns:**
- None.

##### `_publish_proxy_response(self, response, command, correlation_id)`
Logs the response received from an instrument query.

**Parameters:**
- `response`: The raw data returned by the instrument.
- `command`: The original query command.
- `correlation_id`: Optional ID for tracking asynchronous results.

**Returns:**
- None.

##### `set_instrument_instance(self, inst)`
Links a physical instrument session to the proxy and starts worker.

**Parameters:**
- `inst`: The `pyvisa.Resource` instance. If `None`, the proxy is shut down.

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Configures instrument session timeout.
- Manages the lifecycle of the background worker thread.

##### `_reset_device(self)`
Sends a standard IEEE 488.2 reset command (`*RST`) to the device.

**Parameters:**
- None

**Returns:**
- `True` if the command was successfully sent.
- `False` if communication failed.

##### `write_safe(self, command)`
Executes a non-query SCPI command with error handling.

**Parameters:**
- `command`: The SCPI string to write.

**Returns:**
- The result of the external `write_safe` utility.

##### `query_safe(self, command, correlation_id)`
Executes a SCPI query command and returns the response safely.

**Parameters:**
- `command`: The SCPI query string.
- `correlation_id`: Tracking ID for the response.

**Returns:**
- The result of the external `query_safe` utility.

## 📝 Focus on Intent (Inline Comments)
- Using a non-blocking get to allow for rapid shutdown signaling.
- Extract command parameters from the hardened messaging interface.
- Start the worker thread if it's not already running.
- Cleanly shut down if the instrument is disconnected.
