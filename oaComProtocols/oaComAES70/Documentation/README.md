# 70 AES70: Object-Oriented Control Module

The **AES70 (OCA)** module maps high-level, object-oriented device parameters from the Open Control Architecture into the normalized OPEN-AIR MQTT space. It provides professional-grade control for networked audio hardware.

---

## 1. V3.1.0 Behavioral Matrix
| Feature | Implementation |
| :--- | :--- |
| **Object-Oriented Map** | OCA device objects (Gains, Mutes, Switches) are mapped directly to internal MQTT topics. |
| **Heartbeat Synced** | Maintains a synchronized heartbeat with the device to prevent "ghost" control points. |
| **State Awareness** | Mirrors the device's functional tree in the global state cache. |

---

## 2. Core Functional Role
*   **Bidirectional Control:** Actions on an AES70 device (like a hardware button press) are ingested as **SPLICE** actions.
*   **Loop Protection:** Utilizes the global `src` ID to ensure commands from the system don't cause feedback loops at the device level.

---

## 3. Topic Mapping
*   **Primary Path:** `OPEN-AIR/AES70/#`
*   **Format:** `OPEN-AIR/AES70/[DeviceGUID]/[ObjectOID]/Value`
