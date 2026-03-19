# _publish_splinks

Publishes the current list of splinks to the MQTT bus.

## Role
Synchronizes the state of the Splinker system with the rest of the network by broadcasting the full list of active splink configurations to the topic `OPEN-AIR/System/Status/Splinker/List`.

### Details
- Includes a timestamp and the instance GUID in the payload.
- Uses `orjson` for efficient serialization.
