# 🏷️ Mqtt Connection Manager

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
mqtt/mqtt_connection_manager.py

Manages the singleton MQTT client connection using aiomqtt (asyncio wrapper for
paho).
Bridges the async MQTT loop with the synchronous Tkinter application using a
background thread.

Author: Anthony Peter Kuzub
Blog: www.Like.audio (Contributor to this project)
Version 20260218.AioMqtt.2

## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class MqttConnectionManager`
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

##### `is_connected(self)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `get_client_instance(self)`
Returns self as a proxy for publishing and subscribing.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `publish(self, topic, payload, qos, retain)`
Thread-safe publish proxy.

**Parameters:**
- `topic`: [TODO: Detail meaning, valid ranges, special cases]
- `payload`: [TODO: Detail meaning, valid ranges, special cases]
- `qos`: [TODO: Detail meaning, valid ranges, special cases]
- `retain`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `subscribe(self, topic, qos)`
Thread-safe subscribe proxy. Queues the request for the async loop.

**Parameters:**
- `topic`: [TODO: Detail meaning, valid ranges, special cases]
- `qos`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `connect_to_broker(self, address, port, on_message_callback, subscriber_router)`
Starts the async MQTT loop in a background thread.

**Parameters:**
- `address`: [TODO: Detail meaning, valid ranges, special cases]
- `port`: [TODO: Detail meaning, valid ranges, special cases]
- `on_message_callback`: [TODO: Detail meaning, valid ranges, special cases]
- `subscriber_router`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `_run_async_loop(self)`
Entry point for the background thread.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `disconnect(self)`
Triggers graceful shutdown of the async loop.

**Parameters:**
- None

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

## 📝 Focus on Intent (Inline Comments)
> *Reminder: Ensure inline comments focus on the 'why'—non-obvious logic, workarounds, or hardware quirks rather than the mechanics of the code itself.*
