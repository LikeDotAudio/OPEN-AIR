# 🌐 oaComProtocols.oaComSNMP: SNMP Communication Module

## 📖 Overview
The `oaComProtocols.oaComSNMP` package provides bidirectional synchronization between the OPEN-AIR system state and the SNMP protocol. It enables external network management systems (NMS) to monitor and control OPEN-AIR parameters using standard SNMP GET and SET operations.

---

## 🏗️ Core Components

### 1. The Gatekeeper (`Entry.py`)
The sole public API for the module. It manages the singleton instance of the `SNMPManager` and handles standalone service initialization.

### 2. SNMP Orchestrator (`Managers/snmp_manager.py`)
The central hub that coordinates all SNMP sub-services. It handles OID tree construction, state persistence, and command monitoring.

### 3. State Persister (`Core/snmp_state_persister.py`)
A high-priority background worker that serializes the internal state cache into a flat file format optimized for fast `awk`-based retrieval by the SNMP daemon bridge.

### 4. Log Monitor (`Core/snmp_log_monitor.py`)
A dedicated listener that watches the system SET log for commands issued by external SNMP managers and injects them back into the system via the `ProtocolRouter`.

### 5. OID Map Converter (`Core/oid_map_converter.py`)
The "Translation Engine" that transforms hierarchical MQTT topics into numerical OIDs based on the project's folder sorting conventions.

---

## 🔬 The "Pull" Bridge Architecture
Unlike event-driven protocols, SNMP in OPEN-AIR operates on a high-speed file-sync model:
1. **Persistence**: The system constantly writes its state to `oaDataLogs/SNMP/openair_snmp_objects.txt`.
2. **Master Bridge**: A generated bash script (`master_snmp_bridge.sh`) is registered with the system `snmpd` daemon using the `pass` command.
3. **Retrieval**: When an external manager performs a GET, `snmpd` executes the master script, which uses `awk` to instantly retrieve the value from the state file.
4. **Command**: For SET operations, the script writes the command to `oaDataLogs/SNMP/snmp_set.log`, which is then picked up by the `LogMonitor`.

---

## 🛠️ Installation & Setup
To deploy the SNMP infrastructure on a Linux host:
1. Open the **SNMP Bridge** status widget in the UI.
2. Click **Request Script** to generate the installer.
3. Copy the script and run it in a terminal with `sudo` privileges.

## 🛡️ Dependencies
* **snmpd**: System SNMP daemon.
* **awk**: For high-performance file parsing.
* **oaComBroker**: For system-wide command routing.
