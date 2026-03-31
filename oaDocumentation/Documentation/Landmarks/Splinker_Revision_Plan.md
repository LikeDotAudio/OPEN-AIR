# Splinker Core v1.1.0 - Revision Plan & Strategy

## 1. Logic Analysis: "The Splinker" Architecture

The core problem "The Splinker" solves is the "Connection Gap" in decoupled hardware-software systems. When physical controls (motors, faders) are detached from the digital engine they manipulate, the latency between action, software processing, network routing, and physical feedback can cause chaotic oscillations ("Infinite Echo") and ghost touches.

**Bifurcated Routing:**
1. **Splicing Control (Fast Lane):** High-priority path for raw human input. This goes straight to the digital processing engine to preserve muscle memory and immediate acoustic/visual response.
2. **Linking Feedback (State Awareness):** Bidirectional meta-data layer that maintains state synchronization, drives UI displays (LCDs, LEDs), and controls physical hardware locks (motors).

**The JSON Immutability Pattern:**
Every hardware input acts as an immutable "shipping manifest." 
When hardware generates an event, it tags it with `origin_source`. When the Splinker processes the event and fires back a Consumer Update, it reflects this `origin_source` back to the hardware.

**Echo Cancellation & Ghost Touch Lock:**
When the hardware receives a Consumer Update from the network:
1. It checks the `origin_source`. If it matches its own ID, it knows it caused the event, thus ignoring the value update (Echo Cancellation).
2. It checks `is_settled`. If `false` (human is still moving the control), it engages the Ghost Touch Lock on its motors, allowing only the local human finger to drive the value. Displays (LCDs) continue to update via the Link path.
3. Once the physical interaction ceases, a debounce timer expires, and a final packet is sent with `is_settled: true`. The Splinker reflects this, and the hardware motor lock disengages, snapping the physical fader to the definitive software value.

## 2. Payload Format Check

The entire system (GUI, MQTT, OSC, SNMP, MIDI) must conform to this strict JSON schema.

```json
{
  "origin_source": "Fader_Bank_Left",
  "msg_guid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "timestamp": 1710500123.456,
  "target_parameter": "fader_channel_1",
  "value": 0.701,
  "is_locked": true,
  "is_settled": false
}
```

**Formatting Rules:**
*   **JSON Immutability:** Core attributes must not be mutated in transit. The router may only append metadata or reflect.
*   **Naming Conventions:** Hardware IDs use `UPPER_SNAKE_CASE` (e.g., `CTRL_SURFACE_A`). Variable keys use `snake_case` (e.g., `is_locked`).
*   **Type Enforcement:** 
    *   `value`: Always a `float`.
    *   `is_locked` / `is_settled`: Strict JSON booleans (`true`/`false`), not ints or strings.
    *   `timestamp`: Float representing epoch time.
*   **Parser Safety:** All ingest nodes must use strict `try/except` JSON parsing to drop malformed packets gracefully.

---

## 3. The 10-Point Strategy for Implementation

1. **Schema Standardization:** Update `StateCacheManager.handle_external_update` and `StateMirrorEngine.broadcast_gui_change_to_mqtt` to strictly output the new JSON schema (including `origin_source`, `target_parameter`, `is_locked`, `is_settled`, `msg_guid`).
2. **Global Payload Refactor:** Audit `OSCManager`, `SNMPManager`, and `MidiManager` translation layers. Force all ingress/egress to wrap their native data into this unified JSON dictionary before publishing to the `ProtocolRouter`.
3. **Ghost Touch Lock Implementation (GUI):** Update the `StateMirrorEngine.sync_incoming_mqtt_to_gui` method. If `is_settled == false` and the local widget is `is_locked == true` (currently being dragged), silently drop the incoming network payload to prevent fighting the user's mouse.
4. **Echo Cancellation Logic:** Enhance the loop-prevention check in `StateMirrorEngine` and `StateCacheManager`. Use `origin_source` and `target_parameter` matching against local IDs to break infinite feedback loops.
5. **Debounce & Settling Protocol:** Implement a debounce timer on all physical and UI control endpoints. On drag/move, broadcast `is_settled: false`. On release, wait 50ms, then fire a final absolute value broadcast with `is_settled: true`.
6. **Hardware Node Compliance:** Ensure any attached hardware (ESP32/Teensy) runs a compliant ArduinoJson parser that checks for `is_settled` before attempting to drive physical PWM motors.
7. **Splinker Engine Refactor:** Review the `workers/Splinker` directory (`_broker_splice.py`, `_broker_link.py`). Ensure the `Splinker` acts exclusively as a passive broker that links parameters, scaling values as needed, without destroying the `msg_guid` or `origin_source` of the manifest.
8. **DPI (Deep Packet Inspection) Hardening:** In `ProtocolRouter.ingest()`, wrap all JSON extraction in tight `try/except` blocks. Immediately drop, log, and quarantine any strings that fail strict JSON formatting.
9. **Visual Linking Enhancements:** If requested, build a "Link Setup" GUI that visualizes the Splinker connections (e.g., linking `fader_channel_1` to `osc_output_5`), defining scaling/inversion handlers.
10. **System-Wide Telemetry Validation:** Use the new `UPPER_SNAKE_CASE` origin sources to filter and visualize MQTT traffic cleanly in the debug logs (using the established Three Emoji standard).

---

## 4. Test Set Scenarios

### Test 1: The Echo Cancellation Test
*   **Action:** Simulate a `GUI` node sending a `value: 0.5` payload with `origin_source: "GUI_Main"`.
*   **Expected Result:** The `Splinker` links this to an external system, which acknowledges the change. The `GUI_Main` node receives the confirmation packet but drops it silently because `origin_source == "GUI_Main"`, preventing an infinite loop.

### Test 2: The Ghost Touch (Conflict) Test
*   **Action:** A user is actively dragging `fader_1` in the UI (`is_locked: true`). Concurrently, an incoming MQTT message arrives attempting to set `fader_1` to `0.9` with `is_settled: false`.
*   **Expected Result:** The `StateMirrorEngine` drops the incoming network packet to prevent the fader from jumping around while the user holds it.

### Test 3: The Settle & Snap Test
*   **Action:** The user releases `fader_1` in the UI. 
*   **Expected Result:** A final MQTT broadcast is fired containing the exact final float `value` and `is_settled: true`. The receiving hardware node unlocks its physical motor and drives it to the matching position.

### Test 4: The Poison Packet (Malformed JSON) Test
*   **Action:** Publish a raw string `{"origin_source": "BAD_JSON", value: 1}` (missing quotes around 'value') to the root MQTT topic.
*   **Expected Result:** The `StateCacheManager` ingest function catches the JSONDecodeError, drops the packet, logs a `🚫🛑 [ERROR] Malformed Payload` warning, and the system continues running without crashing.

---

## 5. Proposed Changelog Entry

```markdown
## [Upcoming] Splinker Core v1.1.0 Architecture Overhaul
**************************************
### Added
- **Unified JSON Manifest**: Implemented strict, immutable JSON payloads across all protocols (GUI, MQTT, OSC, SNMP, MIDI). Payloads now enforce `origin_source`, `msg_guid`, `timestamp`, `target_parameter`, `value`, `is_locked`, and `is_settled`.
- **Debounce & Settling Protocol**: Added the `is_settled` boolean flag to all control surfaces. Systems now distinguish between an "in-motion" continuous stream and a "finalized" value state.

### Changed
- **Echo Cancellation**: Hardened the `StateMirrorEngine` and `StateCacheManager` to strictly rely on `origin_source` reflection to identify and drop redundant feedback packets, neutralizing infinite loops.
- **Ghost Touch Lock**: Decoupled physical/visual displays from motor control logic. Incoming network updates dynamically yield to local human interaction if the `is_settled` flag indicates motion.

### Fixed
- **Payload Resiliency**: Wrapped all network ingest functions in strict JSON validation blocks. Malformed hardware packets are now cleanly dropped and logged rather than causing cascading parsing errors.
```
