# Ⓢ SNMP: Industrial Monitoring Module

The **SNMP** module provides legacy industrial monitoring for the OPEN-AIR ecosystem. It translates high-level system states into standardized OIDs (Object Identifiers) and manages asynchronous trap generation.

---

## 1. V3.1.0 Behavioral Matrix
| Feature | Implementation |
| :--- | :--- |
| **Industrial Monitoring** | Translates internal states into a static OID tree for IT software (e.g., PRTG, Nagios). |
| **Trap Triggers** | Generates SNMP TRAPs based on Matrix-defined critical alarm thresholds. |
| **Asynchronous Reader** | Monitored topics are processed in a low-priority thread to prevent logic stutter. |

---

## 2. Core Functional Role
*   **System Auditing:** The SNMP module acts as a passive auditor, reporting functional status without interfering with the low-latency control paths.
*   **Critical Alerts:** High-criticality events (like hardware disconnects) are instantly converted into SNMP Traps for external enterprise notification.

---

## 3. Topic Mapping
*   **Primary Path:** `OPEN-AIR/SNMP/#`
*   **Output Path:** `OPEN-AIR/SNMP/gui_out/[OID]`
*   **Trap Path:** `OPEN-AIR/SNMP/Trap/[AlertLevel]`
