# ARCHITECTURE.md - The WYSIWYG Orchestration
#
# Author: Anthony Peter Kuzub
# Version 20260417.0100.1
#
# Description: Narrative architectural guide for the WYSIWYG Editor.

## 🎭 The Narrative
Imagine a professional broadcast studio where the engineers (Core) and the 
on-air talent (UI) are separated by a thick glass pane. They communicate 
via headsets (Event Bus) to ensure that no matter how chaotic things get on 
stage, the underlying broadcast remains stable.

This is the **Partitioned Architecture** of the OPEN-AIR WYSIWYG Editor.

## 🏗️ How it Works

### 1. The Pulse (Events)
Everything in the editor starts with a 🖱️ `[ACTION]`. A user grabs a 
fader or drags a new component from the Library. The UI doesn't 
directly change the data; it broadcasts a `FOCUS_REQUESTED` or 
`COMPONENT_DROPPED` event.

### 2. The Brain (Core State)
The `StateManager` listens to these events. It performs the heavy lifting:
*   Validating the JSON schema.
*   Moving elements between containers.
*   Updating property values.
Once the state is mutated, it yells back: 🧠📡📤 `[COMPUTE] STATE_UPDATED`.

### 3. The Stage (Dynamic Rendering)
The `InteractiveLayout` receives the update and triggers a ♻️ `[REBUILD]`.
It uses an `BatchLayoutEngine` to rebuild the UI in batches. To keep the 
experience fluid, it employs a "Skeleton-First" strategy:
1.  **Ghost Mode**: In high-speed drag operations, the editor renders 
    simple boxes and green insertion lines to indicate intent.
2.  **Surgical Refresh**: Only the affected branches of the UI are 
    re-rendered when possible.

## 🛠️ The Interaction Layers (Overlays)
Traditional Tkinter event handling is too slow for pixel-perfect design. 
We use a **Ghost Overlay**—a transparent canvas that sits above the 
rendered widgets.
*   **Green Line**: Indicates a valid drop insertion point.
*   **🎯 Handle**: Provides a universal selection and drag entry point.
*   **Alignment Guides**: Real-time snappers that calculate distances 
    between sibling widgets.

## 🔌 Integration with MQTT
The editor is "Live-Aware". Every change made in the WYSIWYG environment 
can be mirrored to a running device in real-time via the `oaComBroker`. 
This creates a true "What You See Is What You Get" loop where the design 
on your screen is the reality on the hardware.
