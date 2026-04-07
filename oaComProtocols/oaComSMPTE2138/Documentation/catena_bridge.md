# 🏷️ SMPTE2138 Bridge (ST 2138)

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

## 📖 Description & Purpose
### File Level
oaComProtocols.oaComSMPTE2138/Managers/smpte2138_manager.py

This module implements a decoupled, standalone communication bridge that 
interfaces the internal OPEN-AIR MQTT action namespace with the external 
SMPTE ST 2138 (SMPTE2138) ecosystem.

Author: Anthony Peter Kuzub
Version 20260330.1400.1

### Partitioned Architecture
The `oaComProtocols.oaComSMPTE2138` module operates as a **Destination** partition. It 
consumes internal "intent-based" actions and transforms them into 
standardized, binary-encoded state updates for professional media clients.

## ⚙️ Assumptions & Constraints
- **MQTT Dependency**: Requires an active connection to the internal broker.
- **Protobuf 3.0**: Outbound messages are binary-encoded using ST 2138 
  normative schemata.
- **Namespace Isolation**: External traffic is strictly contained within 
   the `st2138/` root to prevent interference with internal human-readable 
   telemetry.

## 📚 API Reference

### Classes
#### `class SMPTE2138Manager`
Manages the translation and distribution of SMPTE2138-compliant messages.

##### `__init__(self, mqtt_connection, subscriber_router)`
Initializes the bridge and registers internal action subscriptions.

**Parameters:**
- `mqtt_connection`: Active MQTT connection manager.
- `subscriber_router`: Router for managing topic subscriptions.

**Returns:**
- None.

**Side Effects & Thread-Safety:**
- Registers callbacks for `oa/action/#`.
- Thread-safe for multi-publisher environments.

##### `_on_internal_action(self, msg)`
Processes incoming internal actions and triggers translation.

**Parameters:**
- `msg`: The `MqttMessage` containing the internal action payload.

**Returns:**
- None.

##### `_publish_parameter(self, oid, value)`
Encodes and publishes a FLOAT32 parameter update.

**Parameters:**
- `oid`: The SMPTE2138 Object Identifier.
- `value`: The numeric value to publish.

**Returns:**
- None.

## 📝 Focus on Intent (Inline Comments)
The bridge utilizes a static OID mapping to bridge the flexible internal 
topic structure with the rigid SMPTE2138 requirement for numeric or semantic 
identifiers. This allows the internal platform to evolve without breaking 
compliance with external media standards.
