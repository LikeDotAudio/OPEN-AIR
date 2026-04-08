# 🔗 SPLINKER: The Micro-Logic Event Lifecycle

The **Splinker** system is the core behavioral engine of OPEN-AIR. It manages the physical reality of control events, ensuring that asynchronous MQTT messages do not cause hardware jitter or conflicting states. It specifically handles the lifecycle of a "move" through three primary micro-logic gates: **SPLICE**, **LINK**, and **SPLINKER**.

---

## 1. The Micro-Logic Gates

### A. The SPLICE (Update Partner)
*   **Role:** The entry gate for a new event.
*   **Behavior:** It identifies the `origin_source` and pairs it with its intended `target_parameter`.
*   **Action:** It triggers the **Ghost Touch Unlock**. 
    *   *Logic:* If a user physically touches a motorized fader, the system "unlocks" software control to prevent the motor from fighting the human hand.

### B. The LINK (The Payload Generator)
*   **Role:** The data packager.
*   **Behavior:** It creates a unique `msg_guid` and attaches critical state flags to the event envelope.
*   **State Flags:**
    *   `is_locked`: Prevents low-priority sources from interrupting this specific stream.
    *   `is_settled`: Communicates whether the value is currently moving (False) or has reached its final destination (True).
*   **Output:** An **Event Stamp** with a high-resolution timestamp, published to the MQTT backbone.

### C. The SPLINKER (Consumer Update)
*   **Role:** The distribution engine.
*   **Behavior:** Receives the **Update Stamp** from MQTT and acts as the "Master Consumer."
*   **Action:** It splits the update into two distinct paths:
    1.  **Maker Update:** Informs the GUI and other status displays that the value has changed in real-time.
    2.  **Consumer Update:** Physically commands the hardware (e.g., moves a motorized fader) but only after passing through **Ghost Touch Lock** logic to ensure the fader is safe to move.

---

## 2. Narrative: The "Splinker" Flow in Action

1.  **Generation:** A user moves a MIDI Fader. The **MIDI Receiver** triggers a **SPLICE**.
2.  **Logic Gate:** **SPLICE** identifies the `origin_source` as a physical move and triggers **Ghost Touch Unlock**, signaling the motor driver to release hold.
3.  **Transit:** **LINK** generates a `msg_guid`, sets `is_settled: false`, and stamps the event for publication to **MQTT Storage**.
4.  **Distribution:** The **SPLINKER** picks up the message. Seeing `is_locked: true` and `is_settled: false`, it prioritizes this stream.
5.  **Feedback:** It sends a **Maker Update** to the **GUI**, allowing the screen fader to follow the physical hand in real-time.
6.  **Resolution:** Once the user releases the fader, a final message with `is_settled: true` is sent. The **SPLINKER** then triggers **Ghost Touch Lock**, returning the fader to automated control readiness.

---

## 3. Benefits of the Splinker Architecture
*   **Hardware Safety:** Ghost Touch logic prevents mechanical wear and motor fighting.
*   **Deterministic State:** `is_settled` and `is_locked` flags ensure that automated moves don't jitter during manual overrides.
*   **Decoupled Feedback:** Makers (GUIs) and Consumers (Hardware) are updated independently, ensuring the UI remains responsive even if hardware response is delayed.
