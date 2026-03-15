# _update_splink

Updates an existing splink's configuration.

## Role
Locates a splink by its ID, merges the new data into the existing configuration, and saves the result to disk.

### Parameters
- `splink_id`: The unique identifier of the splink.
- `new_data`: A dictionary containing the fields to update.
