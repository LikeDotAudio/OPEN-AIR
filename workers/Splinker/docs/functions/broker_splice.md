# _broker_splice

Executes the "Splice" operation: forwarding data from a source to a destination.

## Role
Writes the processed value to the destination topic in the `state_cache_manager`. 

### Logic
- Handles sub-path injection if a `dest_key` is present.
- Avoids redundant updates if the value has not changed.
- Includes metadata to identify `SPLINKER` as the source of the update, preventing feedback loops.
