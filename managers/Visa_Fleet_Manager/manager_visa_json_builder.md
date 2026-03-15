# 🏷️ Manager Visa Json Builder

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
managers/STATE_VISA_FLEET_Manager/manager_visa_json_builder.py

Manages the construction and augmentation of JSON data for VISA devices.

Author: Gemini Agent

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class VisaJsonBuilder`
No class description provided.

##### `__init__(self)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `augment_device_details(self, device_entry)`
Looks up the Model Number in KNOWN_DEVICES and adds Type/Notes to the entry.

**Parameters:**
- `device_entry`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `save_inventory_to_json(self, inventory_data)`
Saves the current fleet inventory to a JSON file in an atomic way to prevent
corruption.
It writes to a temporary file first and then renames it.

**Parameters:**
- `inventory_data`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `load_inventory_from_json(self)`
Loads fleet inventory from a JSON file if it exists, is not empty, and flattens
it.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `load_grouped_inventory_from_json(self)`
Loads fleet inventory from a JSON file if it exists and returns the raw,
hierarchical (grouped) dictionary without flattening.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `save_query_response_to_json(self, serial, response, command, corr_id)`
Saves a query response to a JSON file in the DATA directory.
Filename format: DATA/{serial}_query_{timestamp}.json

**Parameters:**
- `serial`: [TODO: Detail meaning, valid ranges, special cases]
- `response`: [TODO: Detail meaning, valid ranges, special cases]
- `command`: [TODO: Detail meaning, valid ranges, special cases]
- `corr_id`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_group_devices_by_type_and_model(self, inventory_data)`
Groups a flat list of device dictionaries first by 'device_type',
then a constant 'YAK' topic, then 'model' (forced uppercase), then a constant
'Connection' topic,
and finally by 'gpib_address'.
The innermost level will contain the device's full details.

**Parameters:**
- `inventory_data`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_flatten_grouped_inventory(self, grouped_data)`
Flattens the hierarchical grouped inventory data back into a list of individual
device dictionaries.
Expected structure: device_type -> "YAK" -> model -> "Connection" -> "Table" ->
gpib_address -> device_dict

**Parameters:**
- `grouped_data`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
