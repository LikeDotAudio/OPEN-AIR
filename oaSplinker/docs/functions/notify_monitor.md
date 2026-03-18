# _notify_monitor

Internal helper to broadcast messages to all registered monitor callbacks.

## Role
Iterates through all registered callbacks and executes them with the provided message type and data. It includes error handling to ensure a failing callback does not disrupt the system.

### Parameters
- `msg_type`: The category of the message (e.g., "debug_log", "router_event").
- `data`: The payload associated with the message.
