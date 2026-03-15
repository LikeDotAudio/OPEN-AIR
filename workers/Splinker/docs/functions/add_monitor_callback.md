# add_monitor_callback

Registers a callback function for monitoring Splinker events.

## Role
Allows external modules (like UI or debugging tools) to subscribe to internal Splinker events, such as debug logs or router events.

### Parameters
- `callback`: A function that will be called with `msg_type` and `data`.
