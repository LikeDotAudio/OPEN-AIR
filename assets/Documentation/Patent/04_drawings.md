# Drawings

## Figure 1: System Architecture

The following diagram illustrates the high-level architecture of the software system.

```
+-----------------------------------------------------------------+
|                        Desktop Computer                         |
|                                                                 |
| +-----------------------+      +------------------------------+ |
| |   Graphical User      |      |     Instrument Hardware      | |
| |      Interface        |<---->| (e.g., RF Spectrum Analyzer) | |
| |      (Display)        |      +------------------------------+ |
| +-----------------------+                      ^                |
|           ^                                    |                |
|           |                                    |                |
|           v                                    |                |
| +-------------------------------------------------------------+ |
| |                     MQTT Message Bus                        | |
| +-------------------------------------------------------------+ |
|           ^                                    ^                |
|           |                                    |                |
|           v                                    v                |
| +-----------------------+      +-----------------------+        |
| |      Managers         |      |        Workers        |        |
| | (e.g., FreqManager,   |<---->|  (e.g., PeakPublisher)|        |
| |  BWManager, YaketyYak)|      |                       |        |
| +-----------------------+      +-----------------------+        |
|                                                                 |
+-----------------------------------------------------------------+
```

**Description of Figure 1:**

Figure 1 is a block diagram of the software system. The system runs on a desktop computer and interacts with an external instrument, such as an RF spectrum analyzer.

The **Graphical User Interface (GUI)**, also referred to as the **Display**, is the primary interface for the user. It is dynamically generated based on the filesystem structure. The GUI sends user commands to the MQTT message bus and subscribes to data streams from the bus to display information to the user.

The **MQTT Message Bus** is the central communication hub of the system. It allows the different components to communicate with each other in a decoupled, asynchronous manner.

The **Managers** are a set of components that are responsible for managing the desired state of the instrument. They subscribe to command messages from the GUI and publish state change messages to the workers. The `YaketyYakManager` is a special manager that implements the YAK command abstraction protocol, translating abstract commands into instrument-specific commands.

The **Workers** are a set of components that are responsible for acquiring data from the instrument. They subscribe to state change messages from the managers and publish data messages to the GUI.

The **Instrument Hardware** is the physical test and measurement instrument that is being controlled and monitored by the software.