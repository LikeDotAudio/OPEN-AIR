# Protocol Stateflow (Hub-and-Spoke Model)

## Hub-and-Spoke Architecture
The system operates as a centralized Hub (MQTT Storage) with spoke protocols (this module).

### Data Flow Diagram

```mermaid
graph TD
    subgraph Hardware_Spoke
        A[Input/Sensor] --> B[Spoke Manager]
        B --> C[Output/Actuator]
    end

    subgraph Hub_Infrastructure
        D{MQTT Hub}
    end

    B -- 1. Ingest: Spoke to Hub --> D
    D -- 2. Dispatch: Hub to Spoke --> B

    style D fill:#f9f,stroke:#333,stroke-width:4px
    style Hardware_Spoke fill:#e1f5fe,stroke:#01579b
    style Hub_Infrastructure fill:#fce4ec,stroke:#880e4f
```

## Flow Logic
1. **Ingest (Spoke -> Hub)**:
   - Data enters via the Spoke Manager (this protocol).
   - **Guard**: The Protocol Router checks `ingest_enabled` for this protocol.
   - **Hub**: Data is persisted into the MQTT Storage.

2. **Dispatch (Hub -> Spoke)**:
   - MQTT Hub broadcasts state changes.
   - **Guard**: The Protocol Router checks `egress_enabled` for this protocol.
   - **Output**: The Spoke Manager processes the message (e.g., OSC send, MIDI out).
