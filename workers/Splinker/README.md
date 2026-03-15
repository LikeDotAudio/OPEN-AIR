# 🔗 SPLINKER: The Bidirectional Command Broker

The Splinker system is a decoupled brokerage engine designed to create dynamic, bidirectional communication links between any two points (topics) in the OPEN-AIR ecosystem. It allows for hardware-to-hardware, GUI-to-hardware, or logic-to-logic "splices" with real-time value transformation.

## Core Concepts

### 1. The Splink
A **Splink** is a persistent configuration object that defines a relationship between a **Source** and a **Destination**.
- **Source**: The topic that triggers an action.
- **Destination**: The topic that receives the brokered value.
- **Sub-paths**: Splinker supports granular linking using the `Topic:Key` syntax, allowing you to link specific values within a JSON dictionary.

### 2. Modes of Operation
- **SPLICE**: One-way flow. Source updates the Destination.
- **LINK**: One-way flow. Destination updates the Source (Feedback loop).
- **BOTH**: Bidirectional flow. Both topics stay in sync.

### 3. Processing Pipeline
Every Splink can have a chain of **Handlers** that modify the value as it passes through the broker.
- **Scaling**: Map a 0-127 MIDI value to a 0-100% GUI fader.
- **Deadband**: Filter out jitter or small changes.
- **Debounce**: Prevent rapid-fire messaging (Rate limiting).
- **Inversion**: Flip a toggle or invert a range.

## Architecture

- **SplinkerManager**: The central singleton that manages the lifecycle of all Splinks, handles persistence (saving to `DATA/splink/`), and routes events from the `ProtocolRouter`.
- **SplinkPipeline**: A transient object created for each event to execute the chain of handlers.
- **Handlers**: Modular logic blocks that implement specific value transformations.

## Direct Creation
Splinks can be created on-the-fly via the Command Router's "Direct Splink" feature, which publishes to `OPEN-AIR/System/Control/Splinker/DirectCreate`.

## Persistence
All Splinks are stored as individual JSON files in `DATA/splink/`, allowing them to persist across system restarts.
