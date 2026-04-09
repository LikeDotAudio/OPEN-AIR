# Protocol Stateflow (Hub-and-Spoke Model)

## Hub-and-Spoke Architecture
The system operates as a centralized Hub (MQTT Storage) with spoke protocols (this module).

### Data Flow & Routing Diagram
```mermaid
graph TD
    subgraph Hardware_Interface
        A[External/Local Interface] -- 1. Start: Event Trigger --> B[Spoke Manager]
    end

    subgraph Hub_Infrastructure
        C{MQTT Hub}
    end

    subgraph Guards
        G1[Ingest Gate]
        G2[Dispatch Gate]
    end

    B -- 2. Ingest: Publish to Hub --> G1
    G1 -- Verified --> C
    C -- 3. Dispatch: Broadcast from Hub --> G2
    G2 -- Filtered/Validated --> B
    B -- 4. Output: Hardware/Interface --> A

    style C fill:#f9f,stroke:#333,stroke-width:4px
    style G1 fill:#fff9c4,stroke:#fbc02d
    style G2 fill:#fff9c4,stroke:#fbc02d
    style Hardware_Interface fill:#e1f5fe,stroke:#01579b
    style Hub_Infrastructure fill:#fce4ec,stroke:#880e4f
```

## Lifecycle & Logic
1. **Start**: The manager initializes as a Spoke, registering with the `ProtocolRouter` Hub.
2. **Ingest (Spoke -> Hub)**:
   - Event triggered (MIDI note, OSC addr, etc).
   - **Ingest Gate**: Router checks `ingest_enabled` for this Spoke.
   - **Hub**: Data is validated and committed to `MQTT Storage`.
3. **Dispatch (Hub -> Spoke)**:
   - MQTT Hub broadcasts state changes to all connected Spokes.
   - **Dispatch Gate**: Router checks `egress_enabled` for this protocol.
   - **Filter**: Echo removal (origin-source guard) ensures no self-reflection.
4. **Transmit**: Validated data is rendered to the local physical interface (MIDI Out, OSC Out, etc).

## System Tree Reporting (Heartbeats & Status)
All protocol managers are required to report their operational status to the central monitoring hierarchy. This ensures the Hub maintains an accurate, real-time view of system health and failover eligibility.

### Reporting Flow
```mermaid
graph TD
    subgraph Manager_Self_Health
        B[Spoke Manager]
    end

    subgraph Monitoring_Tree
        H{MQTT Hub}
        S[System Tree]
    end

    B -- 1. Heartbeat: Periodic Status --> H
    H -- 2. Register: Update Tree --> S
    S -- 3. Observe: Status Broadcast --> B

    style S fill:#e8f5e9,stroke:#2e7d32
    style H fill:#fce4ec,stroke:#880e4f
    style B fill:#e1f5fe,stroke:#01579b
```

### Reporting Lifecycle
1. **Heartbeat**: Every manager periodically publishes its status (e.g., ) to the Hub.
2. **System Tree Registration**: The Hub (MQTT) updates the global  tree.
3. **Observation**: Managers subscribe to their own status tree to maintain a synchronized, failover-aware state.

## System Tree Reporting (Heartbeats & Status)
All protocol managers report their operational status to the central monitoring hierarchy.

### Reporting Flow
```mermaid
graph TD
    subgraph Manager_Self_Health
        B[Spoke Manager]
    end

    subgraph Monitoring_Tree
        H{MQTT Hub}
        S[System Tree]
    end

    B -- "1. Heartbeat: Periodic Status" --> H
    H -- "2. Register: Update Tree" --> S
    S -- "3. Observe: Status Broadcast" --> B

    style S fill:#e8f5e9,stroke:#2e7d32
    style H fill:#fce4ec,stroke:#880e4f
    style B fill:#e1f5fe,stroke:#01579b
```

### Reporting Lifecycle
1. **Heartbeat**: Every manager periodically publishes its status (e.g., OPEN-AIR/System/Status/Protocol/Bridge) to the Hub.
2. **System Tree Registration**: The Hub (MQTT) updates the global System/Status tree.
3. **Observation**: Managers subscribe to their own status tree to maintain a synchronized, failover-aware state.
