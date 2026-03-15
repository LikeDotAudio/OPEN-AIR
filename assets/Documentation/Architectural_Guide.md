# 🏗️ OPEN-AIR Architectural Guide: How and Why It Works

## 📖 The Core Philosophy: Partitioned Intelligence

The OPEN-AIR project is built upon a **Partitioned Architecture**, a design choice born from the need to separate high-performance hardware orchestration from responsive, aesthetically rich user interfaces. 

In traditional monolithic systems, UI lag can delay critical hardware commands, and heavy hardware polling can freeze the UI. OPEN-AIR solves this by splitting the world into two distinct halves: **The Core** and **The UI**.

### 1. The Core (Hardware & State Orchestration)
The "Core" lives in `managers/System_Core/open_air_core.py`. It is the silent engine.
*   **How it works:** It manages the physical connections (VISA, SNMP, MQTT) and maintains the "Source of Truth" for the entire system state.
*   **Why it's needed:** By isolating hardware logic, we ensure that a slow instrument response never blocks the user's view. It allows for headless operation—the system can run and monitor hardware even if no screen is attached.

### 2. The UI (The Visual Reflex)
The "UI" lives in `managers/Display/open_air_ui.py`. It is the reactive skin.
*   **How it works:** It uses the **Widget Registry** system to dynamically build interfaces from JSON blueprints. It doesn't "know" about hardware; it only knows about MQTT topics and visual states.
*   **Why it's needed:** This decoupling allows UI designers to iterate on meters, knobs, and graphs without ever touching a line of hardware driver code.

---

## 📡 The Nervous System: MQTT Event Bus

Everything in OPEN-AIR communicates via **MQTT**. This is the glue that binds the Partitioned Architecture.

*   **How it works:** When you turn a knob on the screen, the UI publishes a message to a specific topic (e.g., `OPEN-AIR/Device/Command`). The Core, which is listening to that topic, receives the message and translates it into a physical hardware command (e.g., a SCPI string over VISA).
*   **Why it works:** MQTT is asynchronous and distributed. This means components can be on the same machine, or spread across a network of Raspberry Pis. It provides a built-in "State Mirror" where any component can see what any other component is doing just by subscribing.

---

## 🛠️ The Assembly Line: Dynamic Widget Registry

Instead of hard-coding every screen, OPEN-AIR uses a **Widget Registry** (`managers/Display/factory/widget_registry.py`).

*   **How it works:** 
    1.  A **Blueprint Loader** reads a JSON file defining a layout.
    2.  The **Widget Schema Normalizer** ensures the configuration is valid.
    3.  The **Registry** looks up the appropriate Python class (e.g., `MeterNeedle` or `WinkButton`).
    4.  The **Async Grid Renderer** places them on the screen without locking the main thread.
*   **Why it's needed:** Speed of development. You can create an entirely new control surface for a complex Oscilloscope just by writing a JSON file.

---

## 🏗️ Operational Flow: A Lifecycle Story

1.  **Ignition:** `OpenAir.py` (The Supervisor) starts. It launches the Core and the UI as separate processes or threads.
2.  **Discovery:** The Core's **Discovery Agents** (`workers/discovery_agents/`) scan the network and USB ports for instruments.
3.  **Mapping:** When an instrument is found, the **Visa Fleet Manager** identifies it and triggers the UI to load the corresponding **Yak JSON** command repertoire.
4.  **Interaction:** The user interacts with a "Next Gen" meter. The UI sends a pulse. The Core catches it. The hardware reacts. The Core publishes the new data. The UI meter moves.

This cycle of **Action -> Event -> Reaction** is the heartbeat of OPEN-AIR.
