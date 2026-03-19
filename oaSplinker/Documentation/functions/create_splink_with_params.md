# create_splink_with_params

Creates a splink with a specific source and destination.

## Role
Programmatically creates a fully configured splink. By default, it includes a `scale` handler to map common ranges (e.g., 0-127 MIDI to 0-100 percentage).

### Parameters
- `source`: The source topic/path.
- `dest`: The destination topic/path.
