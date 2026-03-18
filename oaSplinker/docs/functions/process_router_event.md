# process_router_event

Main logic loop for the Splinker brokerage system.

## Role
This function is called for every event moving through the `ProtocolRouter`. It handles:
1. Monitoring notifications.
2. Direct control commands for the Splinker system.
3. Source/Destination "learning" if modes are active.
4. Splice/Link brokerage for active splinks.

### Logic Flow
- Parses the incoming topic.
- Checks if the topic matches any splink source (for SPLICE) or destination (for LINK).
- If a match is found, it instantiates a `SplinkPipeline`, processes the value through configured handlers, and executes the brokerage via `_broker_splice` or `_broker_link`.
