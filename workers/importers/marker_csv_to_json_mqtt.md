# 🏷️ Worker Marker Csv To Json Mqtt

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
importers/worker_marker_csv_to_json_mqtt.py

This module contains the logic for converting marker data from a CSV file to a
device-centric JSON structure and publishing it to MQTT.

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
#### `_publish_recursive(mqtt_util, base_topic, data)`
A simple recursive function to publish all parts of a nested dictionary.

**Parameters:**
- `mqtt_util`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `base_topic`: [TODO: Detail the precise meaning, valid ranges, and special cases]
- `data`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

#### `csv_to_json_and_publish(mqtt_util)`
Reads MARKERS.csv, calculates summary data (total, min/max freq, span), converts
to a flat device-centric JSON structure, saves it, and publishes to MQTT.

MODIFIED: Uses the new nested structure with an 'IDENTITY' blob.

**Parameters:**
- `mqtt_util`: [TODO: Detail the precise meaning, valid ranges, and special cases]

**Returns:**
- [TODO: Explicitly define what constitutes success and specific meanings of returned error codes.]

**Side Effects & Thread-Safety:**
- [TODO: Note any global state changes, locks, I/O operations, or reentrancy limitations.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
