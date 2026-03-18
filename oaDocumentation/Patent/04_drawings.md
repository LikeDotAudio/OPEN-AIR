# Drawings

## Figure 1: Partitioned System Architecture

The following diagram illustrates the partitioned architecture of the OPEN-AIR platform.

```
+-----------------------------------------------------------------+
|                        Desktop Computer                         |
|                                                                 |
|  +-----------------------------------------------------------+  |
|  |                SUPERVISOR (OpenAir.py)                    |  |
|  +-----------------------------------------------------------+  |
|           |                                       |             |
|           v                                       v             |
|  +-----------------------+      +-----------------------------+ |
|  |  PARTITION B (UI)     |      |    PARTITION A (CORE)       | |
|  | photorealistic engine |      |  safety-critical drivers    | |
|  +-----------------------+      +-----------------------------+ |
|           ^                                       ^             |
|           |                                       |             |
|           v                                       v             |
|  +-----------------------------------------------------------+  |
|  |                     MQTT MESSAGE BUS                      |  |
|  +-----------------------------------------------------------+  |
|           ^                                       ^             |
|           |                                       |             |
|           v                                       v             |
|  +-----------------------+      +-----------------------------+ |
|  |      MANAGERS         |      |        WORKERS              | |
|  | (State Control & YAK) |<---->|  (Hardware Acquisition)     | |
|  +-----------------------+      +-----------------------------+ |
|                                                   |             |
|                                                   v             |
|                                     +-------------------------+ |
|                                     |  INSTRUMENT HARDWARE    | |
|                                     | (VISA/USB/SCPI/Yak Mon) | |
|                                     +-------------------------+ |
|                                                                 |
+-----------------------------------------------------------------+
```

**Description of Figure 1:**

Figure 1 is a block diagram of the partitioned software system. The system is managed by a **Supervisor (OpenAir.py)** which orchestrates two distinct execution environments.

**Partition B (UI Engine)** is responsible for the photorealistic, filesystem-driven graphical user interface. It utilizes the "Next Gen" rendering engine to create industrial dashboards and subscribes/publishes to the MQTT bus for state synchronization.

**Partition A (Core)** handles all safety-critical interactions with the **Instrument Hardware**. It contains the low-level drivers and the MQTT bridge that isolates hardware latency from the user interface.

The **MQTT Message Bus** serves as the asynchronous communication backbone, linking the UI, Managers, and Workers.

The **Managers** reside in the logic layer, processing state changes and implementing the YAK command abstraction protocol to translate abstract UI interactions into hardware-specific commands.

The **Workers** perform high-speed data acquisition from the physical instruments and publish processed results back to the message bus for visualization.