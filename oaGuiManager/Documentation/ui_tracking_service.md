# 🏷️ Ui Tracking Service

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
managers/Display/telemetry/ui_tracking_service.py

Centralized Telemetry Service for UI Visibility and Geometry.
Replaces HiddenVisibilityManagerMixin and HiddenGeometryManagerMixin.

Author: Anthony Peter Kuzub
Blog: www.Like.audio
Version 20260222.Telemetry.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class UITrackingService`
Centralized service to track widget visibility and geometry.
Handles debouncing and MQTT publishing.

##### `__init__(self)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `track(self, widget, tab_name, state_mirror_engine, base_mqtt_topic_from_path)`
Starts tracking a widget (usually a root frame/builder).

**Parameters:**
- `widget`: [TODO: Detail meaning, valid ranges, special cases]
- `tab_name`: [TODO: Detail meaning, valid ranges, special cases]
- `state_mirror_engine`: [TODO: Detail meaning, valid ranges, special cases]
- `base_mqtt_topic_from_path`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_visible(self, widget, event)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `widget`: [TODO: Detail meaning, valid ranges, special cases]
- `event`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_hidden(self, widget, event)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `widget`: [TODO: Detail meaning, valid ranges, special cases]
- `event`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_destroy(self, widget, event)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `widget`: [TODO: Detail meaning, valid ranges, special cases]
- `event`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_geometry_change(self, widget, event)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `widget`: [TODO: Detail meaning, valid ranges, special cases]
- `event`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_perform_geometry_publish(self, widget)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `widget`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_publish_visibility(self, meta, is_visible)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `meta`: [TODO: Detail meaning, valid ranges, special cases]
- `is_visible`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
