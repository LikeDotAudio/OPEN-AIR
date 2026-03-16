# MDP: Multi-Dimensional Panner

**Author:** Anthony Kuzub (Anthony@Kuzub.com)  
**License:** The Open Concept License (see below)

## Overview

The **Multi-Dimensional Panner (MDP)** is an advanced user interface concept designed for spatial audio mixing, object-based panning (e.g., Dolby Atmos), and complex parameter control. It extends the traditional "Linear Travelling Potentiometer" (LTP) by placing it within a free-floating, rotatable widget on a 2D plane.

This design allows a single touch point to control three distinct dimensions simultaneously:
1.  **Depth/Distance (Linear):** Sliding the fader cap along its track.
2.  **Intensity/Gain (Rotary):** Rotating the knob on the fader cap (without moving the fader).
3.  **Azimuth/Position (Spatial):** Moving and rotating the entire fader widget within the soundstage.

## Features

*   **Hybrid Control:** Combines the precision of a linear fader with the utility of a rotary knob in a single unit.
*   **Absolute Orientation:** The rotary knob's indicator and intensity sweep maintain an absolute orientation relative to the screen (bottom-left to bottom-right sweep), regardless of the widget's rotation. This prevents user disorientation when the fader is upside down or sideways.
*   **Spatial Manipulation:** The entire fader unit can be moved and rotated, allowing it to represent a sound source's physical position and orientation in a virtual room.
*   **Multi-Touch Interface:** Designed for touch screens with specific gestures for different modes of operation.

## Controls (Demo)

The HTML5 prototype supports both Touch and Mouse interactions:

| Action | Mouse | Touch | Function |
| :--- | :--- | :--- | :--- |
| **Linear Slide** | **Left-Drag** Cap | **1-Finger Drag** Cap | Adjusts the "Linear" value (e.g., Distance/Depth). Drag along the track axis. |
| **Rotary Turn** | **Right-Drag** Cap (Horizontal) | **Hold Cap + 2nd Finger Drag** | Adjusts the "Rotary" value (e.g., Intensity/Volume). Visualized by the orange sweep. |
| **Move Widget** | **Track Hold (1s)** -> Drag | **Track Hold (1s)** -> Drag | Moves the entire widget on the canvas. Glow indicates selection. |
| **Rotate Widget** | (N/A in simple mouse) | **Track Hold (1s)** -> **2-Finger Twist** | Rotates the widget's orientation. |
| **Quick Rotate** | **Alt/Ctrl + Scroll** | N/A | Quickly rotates the widget under the cursor. |
| **Quick Rotary** | **Scroll** | N/A | Quickly adjusts the rotary value. |

## Technical Implementation

*   **Platform:** HTML5 Canvas + JavaScript (ES6).
*   **Rendering:** Custom 2D context rendering with matrix transformations for widget rotation and absolute counter-rotation for the knob indicators.
*   **Hit Testing:** Vector-based hit detection using local coordinate transformations to accurately select the cap or body regardless of rotation.
*   **Theme:** High-contrast Dark Mode with Orange (`#f4902c`) accents for active elements and feedback.

## The Open Concept License

This project is released under **The Open Concept License**.

*   **Freedom:** You are free to use, modify, and distribute this work.
*   **Attribution:** Explicit credit to **Anthony Kuzub** must be given in all derivative works.
*   **Nomenclature:** Implementations must strictly use the terms **MDP (Multi-Dimensional Panner)**, **LTP (Linear Travelling Potentiometer)**, and **CMDP (Circular Motion Displacement Potentiometer)** where applicable.
*   **Warranty:** Provided "As Is" without warranty.

*(See the full license text in the application footer or source code.)*