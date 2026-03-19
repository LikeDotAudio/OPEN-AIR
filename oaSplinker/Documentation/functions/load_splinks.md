# _load_splinks

Loads splink configurations from the local filesystem.

## Role
Reads all `.json` files from the `oaDataRunningFiles/splink/` directory and populates the `self.splinks` list. This ensures that splink configurations persist across application restarts.

### Details
- Creates the storage directory if it doesn't exist.
- Triggers `_publish_splinks()` after loading to update the network status.
