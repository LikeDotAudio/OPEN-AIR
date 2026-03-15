# get_instance

Provides a thread-safe singleton access to the `SplinkerManager`.

## Role
Ensures that only one instance of the `SplinkerManager` exists within the application context.

### Parameters
- `state_cache_manager`: (Optional) The manager responsible for state caching.
- `mqtt_manager`: (Optional) The manager responsible for MQTT communications.

### Returns
The singleton `SplinkerManager` instance.
