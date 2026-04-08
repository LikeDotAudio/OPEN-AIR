# 🏷️ Manager Visa

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Documentation](https://img.shields.io/badge/docs-GNU%2FLinux_Standard-brightgreen)

# 🏷️ Manager Visa: Bonjour & Proxy Module

The **VISA** module provides query/response control for SCPI-compatible laboratory and broadcast hardware. In V3.1.0, it is enhanced with **Bonjour** Zero-Conf discovery to automatically map IP-based instruments.

---

## 1. V3.1.0 Behavioral Matrix
| Feature | Implementation |
| :--- | :--- |
| **Bonjour Zero-Conf** | Periodically browses for mDNS services and populates the `Proxy/` path with available IP/Ports. |
| **Asynchronous Query** | All SCPI commands are non-blocking; responses are returned via a dedicated `LINK_FEEDBACK` thread. |
| **Timeout Protection** | Individual device timeouts prevent a single slow instrument from hanging the entire proxy bridge. |

---

## 2. Core Functional Role
*   **Proxy Discovery:** The VISA module acts as a bridge between the physical instrument and the MQTT backbone, ensuring that discovered hardware is instantly controllable via the `OPEN-AIR/Proxy/` namespace.
*   **Stateless Control:** It handles the translation of high-level MQTT "Intents" into low-level SCPI strings.

---

## 3. Topic Mapping
*   **Primary Path:** `OPEN-AIR/Proxy/#`
*   **Discovery Path:** `OPEN-AIR/Discovery/Bonjour/[DeviceID]`

---

## 📖 Description & Purpose
### File Level
managers/VisaScipi/manager_visa.py

Main orchestrator for VISA device interactions.

Author: Anthony Peter Kuzub


## ⚙️ Assumptions & Constraints
*(Document any specific platform requirements, ABI expectations, or required execution privileges here)*

## 📚 API Reference

### Classes
#### `class VisaManagerOrchestrator`
No class description provided.

##### `__init__(self, mqtt_connection_manager, subscriber_router)`
[TODO: Brief verb-first description. Start with action (e.g., 'Allocates...',
'Parses...').]

**Parameters:**
- `mqtt_connection_manager`: [TODO: Detail meaning, valid ranges, special cases]
- `subscriber_router`: [TODO: Detail meaning, valid ranges, special cases]

**Returns:**
- [TODO: Define success and error returns.]

**Side Effects & Thread-Safety:**
- [TODO: Note any locks, I/O, or global state.]

##### `get_managers(self)`
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
