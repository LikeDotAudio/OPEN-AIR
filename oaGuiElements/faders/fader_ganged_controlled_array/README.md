# GCA: Ganged Controlled Array

**Author:** Anthony P. Kuzub (Anthony@Kuzub.com)  
**License:** The Open Concept License (see below)

## Overview

The **Ganged Controlled Array (GCA)**, also known as the **Composite Fader**, is a high-density user interface widget designed to manage multiple related parameters (channels) through a single "Master" fader cap. It solves the problem of controlling groups of values (e.g., a 5.1 surround mix, a drum bus, or an RGB color mix) where maintaining relative offsets is critical, but screen real estate is limited.

## Core Concepts

### 1. Composite Control
*   **The Cap:** A single, large fader cap spans across all underlying channel tracks.
*   **Master Value:** The position of the cap represents the *average* value of all child channels.
*   **Gang Behavior:** Moving the cap adjusts all child channels simultaneously, preserving their relative offsets (e.g., if Channel 1 is +10dB relative to Channel 2, this difference is maintained as the master volume creates a fade-out).

### 2. Dual-View Modes
Users can toggle between two visualization modes by double-clicking (or double-tapping) the fader cap:

*   **Macro Mode (Default):**
    *   Displays a single bar representing the average value.
    *   Useful for quick, high-level adjustments (e.g., "Turn down the drums").
    *   Shows the numeric average value.

*   **Micro Mode:**
    *   The cap's "screen" splits into individual mini-meters for each channel.
    *   Provides a detailed view of the internal balance of the group.
    *   Allows **individual adjustments**: Users can click/drag specific mini-bars *inside* the cap to tweak a single channel's offset without moving the whole group.

### 3. Visual Feedback
*   **Tracks:** Each channel has its own vertical track line.
*   **Markers:** Small colored markers on the tracks indicate the actual value of each channel relative to the master cap position.
*   **Color Coding:** Values are color-coded (Green → Yellow → Red) to indicate intensity or signal level.
*   **Master Highlight:** An orange highlight line connects the bottom of the track to the master cap, visualizing the overall group level.

## Use Cases

*   **Audio Mixing:** Controlling a stereo pair, a 5.1/7.1 surround bed, or a 20-channel microphone array for an orchestra.
*   **Lighting Control:** Managing RGB (Red, Green, Blue) intensity for a fixture using a single fader while allowing individual color tweaking.
*   **Data Visualization:** adjusting threshold parameters for a sensor array.

## Implementations

### HTML5 Demo (`index.htm`)
A standalone web-based demonstration using HTML5 Canvas.
*   **Features:** Touch support, responsive layout, RGB mixer example.
*   **Theme:** Dark mode with Orange (`#f4902c`) accents.

### Python Prototype (`Composite_fader_multichannel.py`)
A `tkinter`-based widget for desktop applications.
*   **Integration:** Designed to work with an MQTT-based state mirror engine for real-time hardware control.
*   **Configuration:** Data-driven via config dictionaries (JSON/YAML compatible).

## The Open Concept License

This project is released under **The Open Concept License**.

*   **Freedom:** You are free to use, modify, and distribute this work.
*   **Attribution:** Explicit credit to **Anthony Kuzub** must be given in all derivative works.
*   **Nomenclature:** Implementations must strictly use the terms **GCA (Ganged Controlled Array)**, **LTP (Linear Travelling Potentiometer)**, and **CMDP (Circular Motion Displacement Potentiometer)** where applicable.
*   **Warranty:** Provided "As Is" without warranty.

*(See the full license text in the application footer or source code.)*