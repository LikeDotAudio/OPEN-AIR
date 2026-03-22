# LTP: Linear Travelling Potentiometer

**Author:** Anthony Kuzub (Anthony@Kuzub.com)  
**License:** The Open Concept License (see below)

## Overview

The **Linear Travelling Potentiometer (LTP)** is a hybrid user interface widget designed to save screen real estate while maximizing control density. It integrates a rotary knob directly onto the cap of a linear fader, allowing simultaneous control of two related parameters (e.g., Level and Pan, or Send Level and Send Pan) in a single compact footprint.

## Core Concepts

### 1. Hybrid Control
*   **Linear Fader (Y-Axis):** The vertical position of the cap controls the primary value (typically Volume, Level, or Depth).
*   **Rotary Knob (Rotation):** A knob embedded in the fader cap controls a secondary value (typically Pan, Param, or Intensity).
*   **Unified Interaction:** Both controls are accessible from the same visual element, reducing mouse travel and UI clutter.

### 2. Interaction Modes
The LTP supports distinct interaction modes to prevent accidental changes:

*   **Standard Mode:**
    *   **Drag Handle:** Adjusts Linear Value only.
    *   **Alt/Option + Drag:** Adjusts Rotary Value only (Linear position is locked).
    *   **Scroll:** Fine-tune Linear Value.
    *   **Alt/Option + Scroll:** Fine-tune Rotary Value.

*   **Freestyle Mode:**
    *   Dragging the handle adjusts **BOTH** Linear and Rotary values simultaneously based on 2D mouse movement. This allows for gestural control (e.g., "throwing" a sound into a corner).

*   **Pan Latch:**
    *   **Double-Click** the cap to engage "Pan Latch".
    *   In this state, horizontal mouse movement adjusts the Rotary value without needing to hold a modifier key.
    *   Click or drag again to disengage.

### 3. Visual Feedback
*   **Linear:** Position of the cap along the vertical track.
*   **Rotary:** Orientation of the indicator line on the cap.
*   **Active State:** The knob glows (default blue/orange) when Rotary control is active (via modifier, latch, or freestyle mode).
*   **Pointer:** When adjusting rotation, the indicator line extends (10x length) to provide precise visual feedback, then retracts on release.

## Use Cases

*   **Channel Strips:** Volume (Linear) + Pan (Rotary).
*   **Effect Sends:** Send Level (Linear) + Pre/Post Toggle or Send Pan (Rotary).
*   **Synthesizers:** Cutoff (Linear) + Resonance (Rotary).
*   **Spatial Audio:** Distance (Linear) + Azimuth (Rotary - mapped to circular motion).

## Implementations

### HTML5 Demo (`index.html`)
A standalone web-based demonstration using HTML5 Canvas.
*   **Features:** Multi-touch support (1 finger slide, 2 finger twist/pan), keyboard modifiers, responsive layout.
*   **Theme:** Dark mode with high-contrast UI.

## The Open Concept License

This project is released under **The Open Concept License**.

*   **Freedom:** You are free to use, modify, and distribute this work.
*   **Attribution:** Explicit credit to **Anthony Kuzub** must be given in all derivative works.
*   **Nomenclature:** Implementations must strictly use the terms **LTP (Linear Travelling Potentiometer)**, **GCA (Ganged Controlled Array)**, and **MDP (Multi-Dimensional Panner)** where applicable.
*   **Warranty:** Provided "As Is" without warranty.

*(See the full license text in the application footer or source code.)*
