# oaGui/Documentation/loader_service_composer.md
# Author: Anthony Peter Kuzub
# Version 20260502.120000.1
#
# Description: Documentation for the UI Service Composition Root.

## 🚀 Overview
The `LoaderServiceComposer` acts as the **Composition Root** for the UI Partition. It is responsible for instantiating concrete service implementations and performing dependency injection across the UI-level service graph.

## 🏗️ Partitioned Architecture
- **Layer**: Managers (UI Partition)
- **Role**: Dependency Injector & Orchestrator 🏗️🧠

## 🔧 Core Functions
### `build_services()`
- **Purpose**: Instantiates and maps all UI-level services.
- **Layers**:
    1. **Base Communication**: MQTT Connection and Subscriber Router. 📡
    2. **State & Mirroring**: State Registry and Mirroring Engine. 🪞
    3. **Protocol Routing**: Protocol Router and Control Broker (Splinker). 🔄
    4. **Specialized Managers**: OSC, SNMP, MIDI, and REST managers (conditional based on config). 🔌
- **Outputs**: Returns a dictionary of shared service instances.
- **Side Effects**: Registers services with the global `ProtocolRouter`.

### `get_bootstrap_dependencies()`
- **Purpose**: Returns the composed service dictionary for use by the `LoaderBootstrapEngine`.
