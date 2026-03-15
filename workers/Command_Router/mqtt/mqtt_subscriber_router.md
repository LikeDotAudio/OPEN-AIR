# 🏷️ Mqtt Subscriber Router

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
mqtt/mqtt_subscriber_router.py

Manages MQTT subscriptions and dispatches incoming messages to registered
callbacks.
Optimized for high-throughput with wildcard-based routing and hash-map dispatch.
Updated for aiomqtt (asyncio) compatibility.

Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)
Version 20260218.AioMqtt.1

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class MqttSubscriberRouter`
Optimized MQTT routing engine.
Bridges the async aiomqtt client with synchronous application callbacks.

##### `__init__(self)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `set_client(self, client)`
Sets the MQTT client instance (aiomqtt Client).

**Parameters:**
- `client`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `subscribe_to_topic(self, topic_filter, callback_func)`
Registers a callback for a topic filter.

**Parameters:**
- `topic_filter`: [TODO: Detail meaning, valid ranges, special cases]
- `callback_func`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `unsubscribe_from_topic(self, topic_filter, callback_func)`
Removes a specific callback function from a topic filter.

**Parameters:**
- `topic_filter`: [TODO: Detail meaning, valid ranges, special cases]
- `callback_func`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_on_message(self, client, userdata, msg)`
Sync callback invoked by MqttConnectionManager's async receiver task.
Runs in the background MQTT thread.

**Parameters:**
- `client`: [TODO: Detail meaning, valid ranges, special cases]
- `userdata`: [TODO: Detail meaning, valid ranges, special cases]
- `msg`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `get_on_message_callback(self)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
