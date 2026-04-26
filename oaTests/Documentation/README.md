# 🧪 oaTests: Test Suite & Maintenance Utilities

## 📖 Overview
`oaTests` is the central hub for system validation and environmental maintenance. It provides a terminal-based TUI (Textual) that orchestrates unit tests, architectural audits, and system cleanup tools.

---

## 🏗️ Core Components

### 1. The Dashboard (`Interface/TestsUI.py`)
A high-fidelity Textual application that serves as the UI layer for the test suite. It provides:
* **Test Execution**: Buttons to trigger unit tests, installation validation, and full system checks.
* **Audit Control**: Triggers structural audits across all `oa*` modules.
* **Maintenance Hub**: Direct access to cleanup scripts for logs, MQTT state, and flamegraphs.
* **Telemetry**: Real-time display of system resources and High Availability (HA) roles.

### 2. Test Runner (`Core/`)
A background service that executes F.I.R.S.T. principle tests and aggregates results into a unified summary.

### 3. Cleanup Utilities (`Workers/CleanupApps/`)
A collection of "Surgical Sweepers" designed to purge technical debt and temporary data without impacting system stability.

---

## 🔬 High Availability Monitoring
The TUI includes a dedicated MQTT listener that subscribes to:
* `OPEN-AIR/System/Failover/Status/#`

It dynamically updates the role label (PRIMARY/SHADOW) based on the heartbeat data received from the Communication Broker.

---

## 🛠️ Usage
To launch the test suite:
```bash
python3 openair.py --tests
```
(Or run the entry point directly if available in the module).

## 🛡️ Dependencies
* **textual**: TUI Framework.
* **oaComProtocols.oaComMQTT**: For real-time telemetry monitoring.
* **oaConfigurationManager**: For GUID and path resolution.
