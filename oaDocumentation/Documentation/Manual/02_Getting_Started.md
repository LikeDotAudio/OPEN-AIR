# OPEN-AIR User Manual

## 02. Getting Started

Getting up and running with OPEN-AIR is designed to be as straightforward as possible.

### Installation
For full installation details, including hardware dependencies like VISA, please refer to the `README.md` and the `Installation/` directory.

### Launching the Supervisor
The primary entry point is the **Supervisor**, which manages both the Core and UI partitions.

To start the full system, run:
```bash
python3 OpenAir.py
```

### Advanced Launch Options
For advanced users or debugging, the supervisor supports flags to run specific partitions independently:

- **Launch only the Core (Partition A):**
  ```bash
  python3 OpenAir.py --core
  ```
  *This is useful when you want to use the hardware driver layer without the UI.*

- **Launch only the UI (Partition B):**
  ```bash
  python3 OpenAir.py --ui
  ```
  *This allows you to work on the UI layout while connecting to a remote core or simulated environment.*

### First Launch Checklist
1.  **MQTT Broker:** OPEN-AIR requires an MQTT broker (like Mosquitto) running on the host machine (`localhost` by default).
2.  **Configuration:** Check `config.ini` in the root directory to set your preferred broker address and debug modes.
3.  **Hardware Connection:** Ensure your instruments are connected via USB, Ethernet (VXI-11), or Serial.

Once launched, the supervisor will initialize the MQTT bridge, start the state managers, and render the initial dashboard based on the `oaGui/Assets/` directory structure.
