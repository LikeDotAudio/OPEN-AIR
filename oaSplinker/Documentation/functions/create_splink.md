# create_splink

Creates a new, empty splink configuration.

## Role
Generates a unique ID for a new splink, initializes it with default values (active, "New Splink" label), saves it, and automatically enters "Learn" mode for the new splink.

### Details
- Generates IDs using the `SPLINK_` prefix and current timestamp.
- Ingests a "CREATED" event into the Protocol Router for system visibility.
