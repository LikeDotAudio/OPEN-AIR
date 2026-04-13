# 🏷️ Meter To Display Units

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
data_graphing/Meter_to_display_units.py

A Tkinter widget that displays a numerical value with progress bars.
Now publishes standard 'value' envelopes to the widget's root topic.

Author: Anthony Peter Kuzub

specific
application can be negotiated. There is no charge to use, modify, or fork this
software.


Version 20250821.200641.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class HorizontalMeterWithText`
A Tkinter widget that displays a numerical value with progress bars.
Now publishes standard 'value' envelopes to the widget's root topic.

##### `__init__(self, parent, config, base_mqtt_topic_from_path, widget_id, **kwargs)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `parent`: [TODO: Detail meaning, valid ranges, special cases]
- `config`: [TODO: Detail meaning, valid ranges, special cases]
- `base_mqtt_topic_from_path`: [TODO: Detail meaning, valid ranges, special cases]
- `widget_id`: [TODO: Detail meaning, valid ranges, special cases]
- `**kwargs`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_meter_value_var_change(self, *args)`
Callback for when meter_value_var changes (from internal or MQTT).

**Parameters:**
- `*args`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

#### `class VerticalMeter`
A Tkinter widget to simulate a 4-channel vertical meter display.
Now publishes standard 'value' envelopes to the widget's root topic.

##### `__init__(self, parent, config, base_mqtt_topic_from_path, widget_id, **kwargs)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `parent`: [TODO: Detail meaning, valid ranges, special cases]
- `config`: [TODO: Detail meaning, valid ranges, special cases]
- `base_mqtt_topic_from_path`: [TODO: Detail meaning, valid ranges, special cases]
- `widget_id`: [TODO: Detail meaning, valid ranges, special cases]
- `**kwargs`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_meter_values_var_change(self, *args)`
Callback for when meter_values_var changes (from internal or MQTT).

**Parameters:**
- `*args`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
