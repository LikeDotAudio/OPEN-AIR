# 🏷️ Active Marker Tune And Collect

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
active/active_marker_tune_and_collect.py

This worker listens for a start command and then continuously loops through all
markers from the repository, gets their peak values from the instrument, and
updates the repository with the new peak data.

Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)

Professional services for customizing and tailoring this software to your
specific
application can be negotiated. There is no charge to use, modify, or fork this
software.

Build Log: https://like.audio/category/software/spectrum-scanner/
Source Code: https://github.com/APKaudio/
Feature Requests can be emailed to i @ like . audio

Version 20250821.200641.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Global Functions
#### `Push_Marker_to_Center_Freq(mqtt_controller, marker_data)`
Publishes MQTT messages to set the instrument's center frequency and span
based on a selected marker, and then triggers the SCPI command.

**Parameters:**
- `mqtt_controller`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `marker_data`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

#### `Push_Marker_to_Start_Stop_Freq(mqtt_controller, marker_data, buffer)`
Calculates start and stop frequencies based on a marker frequency and a buffer,
then publishes the values and triggers the SCPI command.

**Parameters:**
- `mqtt_controller`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `marker_data`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `buffer`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

### Classes
#### `class MarkerGoGetterWorker`
A worker that, when started, continuously fetches peak values for all markers.

##### `__init__(self, mqtt_util)`
Initializes the worker, sets up state variables, and subscribes to topics.

**Parameters:**
- `mqtt_util`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_setup_subscriptions(self)`
Subscribes to all topics required for operation.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_peak_update_for_event_set(self, topic, payload)`
A placeholder method to satisfy the subscription. In a non-mock setup,
this would signal a threading event to continue the main processing loop.

**Parameters:**
- `topic`: [TODO: Detail meaning, valid ranges, special cases]
- `payload`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_marker_data_update(self, topic, payload)`
Callback to update internal state from the markers repository.

**Parameters:**
- `topic`: [TODO: Detail meaning, valid ranges, special cases]
- `payload`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_handle_start_stop(self, topic, payload)`
Starts or stops the main processing loop in a separate thread.

**Parameters:**
- `topic`: [TODO: Detail meaning, valid ranges, special cases]
- `payload`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_place_markers_for_batch(self, batch_ids)`
MODULAR FUNCTION: Sets the frequency of up to 6 markers and triggers the
placement command.

**Parameters:**
- `batch_ids`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_query_markers_for_batch(self, batch_ids)`
NEW FUNCTION: Triggers the NAB query to read the marker peak values.

**Parameters:**
- `batch_ids`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_set_instrument_frequency_span(self)`
Sets the instrument to the full frequency span of all markers,
but only if the min/max frequency has changed or if it's the first run.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_processing_loop(self)`
The main logic loop that runs in a thread.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
