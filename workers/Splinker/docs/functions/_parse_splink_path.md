# _parse_splink_path

Parses a splink path string into a topic and an optional key.

## Role
Supports sub-path mapping within JSON payloads. Splink paths can be formatted as `topic:key` (e.g., `OPEN-AIR/Device/Status:volume`).

### Parameters
- `path`: The path string to parse.

### Returns
A tuple of `(topic, key)`. Key is `None` if no colon is present.
