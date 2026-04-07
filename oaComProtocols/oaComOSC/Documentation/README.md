# 🅾️ oaComProtocols.oaComOSC: OSC Communication Module

## 📖 Overview
The `oaComProtocols.oaComOSC` package provides high-performance bridging between the OPEN-AIR system and external OSC (Open Sound Control) devices. It abstracts the complexities of UDP bundle handling and provides a unified, topic-aligned interface for remote control and telemetry.

---

## 🏗️ Core Components

### 1. The Gatekeeper (`Entry.py`)
The sole public API for the module. It manages the singleton instance of the `OSCManager` and provides high-level methods for sending messages and managing the bridge lifecycle.

### 2. OSC Orchestrator (`Managers/osc_manager.py`)
The central hub that coordinates all OSC sub-services. It handles the mapping between OSC addresses and system topics, manages loop prevention, and orchestrates the background server/client workers.

### 3. RX Server (`Workers/osc_rx_server.py`)
A background UDP listener that ingests incoming OSC bundles, decodes them, and injects the resulting data into the system via the `ProtocolRouter`.

### 4. TX Client (`Workers/osc_tx_client.py`)
A dedicated client responsible for dispatching system state changes back to external OSC surfaces.

---

## 🔬 Data Pipeline
1. **Remote Input**: An OSC bundle arrives at the `OscRxServer`.
2. **Decoding**: The bundle is unpacked and normalized into a system topic.
3. **Injection**: `OSCManager` injects the data into the `ProtocolRouter`.
4. **Mirroring**: System changes from other sources (e.g., MQTT) are automatically translated into OSC addresses and dispatched to the `OscTxClient` for remote surface updates.

---

## 🛠️ Usage
To start the OSC subsystem:
```python
from oaComProtocols.oaComOSC import Entry as osc_api
osc_api.start()
```

## 🛡️ Dependencies
* **python-osc**: For low-level OSC protocol handling.
* **oaComBroker**: For protocol routing.
