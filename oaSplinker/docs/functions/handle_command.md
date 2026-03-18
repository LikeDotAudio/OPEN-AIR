# _handle_command

Unified command handler for both MQTT and internal Router events.

## Role
Parses command topics and executes the corresponding logic (Create, DirectCreate, Learn, Teach, Delete, Update).

### Parameters
- `topic`: The command topic (e.g., `OPEN-AIR/System/Control/Splinker/SPLINK_ID/Update`).
- `payload`: The data associated with the command.

### Supported Commands
- `Create`: Creates a new empty splink.
- `DirectCreate`: Creates a splink with predefined source and destination.
- `Learn`: Activates Learn mode for a splink.
- `Teach`: Activates Teach mode for a splink.
- `Delete`: Removes a splink.
- `Update`: Updates a splink's configuration.
