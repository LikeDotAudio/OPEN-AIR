# 🎹 oaComMidi: MIDI Communication Module

## 📖 Overview
The `oaComMidi` package is responsible for bidirectional communication between the OPEN-AIR system and MIDI-enabled hardware. It abstracts the complexities of raw MIDI protocols and provides a unified, topic-based interface for the rest of the application.

---

## 🏗️ Core Components

### 1. The Gatekeeper (`Entry.py`)
Following the **Partitioned Architecture**, `Entry.py` is the sole public API for the module. it provides a singleton access to the `MidiManager` and high-level lifecycle methods.

### 2. MIDI Orchestrator (`Managers/midi_manager.py`)
The central hub that coordinates between virtual MIDI ports and the system's protocol router. It manages:
* **Lifecycle**: Starting and stopping the MIDI listener threads.
* **Status Broadcasting**: Informing the system of active MIDI inputs and outputs.
* **Bridging**: Normalizing incoming MIDI messages into the unified internal format.

### 3. Port Controller (`Core/midi_port_controller.py`)
Handles the low-level discovery and opening/closing of physical and virtual MIDI ports.

### 4. Hardware Lock (`Core/midi_hardware_lock.py`)
Prevents feedback loops by temporarily locking parameters while they are being physically manipulated on a MIDI controller.

---

## 🔬 Data Pipeline
1. **Physical Input**: A fader is moved on a MIDI device.
2. **Detection**: `MIDIPortController` detects the message in a high-priority loop.
3. **Normalization**: `MIDIProtocolMapper` translates the raw bytes into a logical topic and value.
4. **Injection**: `MidiManager` injects the normalized data into the `ProtocolRouter`.
5. **Feedback**: If the system state changes, the `MidiManager` receives the update and transmits the corresponding MIDI message back to the hardware.

---

## 🛠️ Usage
To start the MIDI subsystem:
```python
from oaComMidi import Entry as midi_api
midi_api.start()
```

## 🛡️ Dependencies
* **mido**: For MIDI port abstraction.
* **python-rtmidi**: Backend for real-time MIDI I/O.
* **oaComBroker**: For protocol routing.
