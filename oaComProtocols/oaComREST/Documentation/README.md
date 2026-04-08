# 🌐 REST: Stateless Injection Module

The **REST** module provides a high-level, stateless entry point into the OPEN-AIR ecosystem. It allows external applications or simple web hooks to trigger internal system actions via standard HTTP protocols.

---

## 1. V3.1.0 Behavioral Matrix
| Feature | Implementation |
| :--- | :--- |
| **Stateless Injection** | Directly triggers the **Protocol Matrix** via HTTP POST. |
| **State Snapshots** | Returns JSON snapshots from the **State Cache** via HTTP GET. |
| **Non-Blocking** | The API server runs in a dedicated thread, ensuring high-speed command intake. |

---

## 2. Core Functional Role
*   **Decoupled Control:** The REST module does not maintain state. It simply converts incoming HTTP requests into internal **SPLICE** actions.
*   **System Visibility:** It provides endpoints for external monitors to query the current functional state of the `OPEN-AIR` network without needing an MQTT client.

---

## 3. Topic Mapping
*   **Primary Path:** `OPEN-AIR/REST/#`
*   **Usage:** External commands arriving here are treated as high-priority, pre-settled actions.
