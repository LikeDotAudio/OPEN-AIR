# handle_mqtt_command

Entry point for processing Splinker commands received via MQTT.

## Role
Passes the incoming MQTT topic and payload to the unified `_handle_command` method.

### Parameters
- `topic`: The MQTT topic string.
- `payload`: The raw payload data.
