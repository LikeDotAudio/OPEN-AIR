# _save_splink

Saves a single splink configuration to the filesystem.

## Role
Persists a splink's data to a JSON file named after its unique ID in the `DATA/splink/` directory.

### Parameters
- `splink`: The dictionary containing the splink's configuration.

### Details
- Uses `orjson.OPT_INDENT_2` for human-readable output.
- Triggers `_publish_splinks()` to broadcast the update.
