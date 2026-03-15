# 🏷️ Xxx-Worker Active Peak Publisher

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
active/XXX-worker_active_peak_publisher.py

A worker module that listens for marker frequency and amplitude outputs from the
YAK repository and republishes the data to a new, deeply hierarchical topic
structure based on the frequency (GHz down to 1s of kHz).

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

### Classes
#### `class ActivePeakPublisher`
An event-driven worker that transforms flat marker data into a hierarchical
topic structure based on frequency (GHz -> 100MHz -> 10MHz -> 1MHz -> 100kHz ->
10kHz -> 1kHz).

##### `__init__(self, mqtt_util)`
Initializes the publisher and sets up subscriptions.

**Parameters:**
- `mqtt_util`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_setup_subscriptions(self)`
Subscribes to the wildcards for all marker peak and frequency values.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_marker_message(self, topic, payload)`
Primary callback to receive data, buffer it, and check for completeness.

**Parameters:**
- `topic`: [TODO: Detail meaning, valid ranges, special cases]
- `payload`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_republish_to_hierarchical_topic(self, marker_id, freq_hz, peak_dbm)`
Converts frequency in Hz to the required hierarchical topic structure and
publishes.

**Parameters:**
- `marker_id`: [TODO: Detail meaning, valid ranges, special cases]
- `freq_hz`: [TODO: Detail meaning, valid ranges, special cases]
- `peak_dbm`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
