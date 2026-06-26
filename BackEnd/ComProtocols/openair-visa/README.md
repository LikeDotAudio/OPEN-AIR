# OpenAir VISA Backend (`openair-visa`)

`openair-visa` is a high-performance, natively compiled Rust backend wrapped for Python using PyO3. It is designed to act as the core communication and discovery protocol for laboratory instruments (Oscilloscopes, DMMs, Spectrum Analyzers, etc.) within the OPEN-AIR system.

By leveraging Rust, it provides lightning-fast network hunting, parallel device scanning, and robust native MQTT publishing, while still seamlessly exposing a simple API to Python scripts.

## Core Architecture

The project strictly follows a clean **"one module per folder"** architecture inside the `src/` directory:

- **`scan_for_devices/`**: The orchestration engine for device discovery.
- **`oa_visa_scanner/`**: Aggressively hunts for raw TCP/IP devices on subnets and scrapes web gateways for connected instruments.
- **`oa_visa_mdns_zeroconf/`**: Listens for mDNS/ZeroConf broadcasts to auto-detect LXI and AES70 devices on the local network.
- **`oa_visa_usb_enumerator/`**: Enumerates locally connected USB test and measurement devices.
- **`visa_connect/`**: Manages low-level, pure-Rust raw TCP socket connections to instruments.
- **`oa_visa_pyvisa_wrapper/`**: A private module that spins up PyVISA under the hood to bridge communication with older, strict VXI-11 gateways (such as the Agilent E5810A) that refuse standard raw TCP sockets.
- **`visa_get_idn/` & `known_devices/`**: Queries the `*IDN?` string of discovered instruments and intelligently maps them to known device categories (e.g., Oscilloscopes, Generators).
- **`oa_visa_reset/`, `oa_visa_status/`, `oa_visa_error_check/`**: Granular modules for sending `*RST`, reading the Status Byte (`*STB?`), and extracting system errors (`:SYST:ERR?`).
- **`oa_visa_mqtt/`**: A fully native Rust MQTT publisher that blasts instrument states, connection info, and health checks to the central OPEN-AIR broker.
- **`resource_manager/` & `visa_proxy/`**: The core struct engines exported to Python that hold the system state and dispatch commands.

## Installation

Because this is a Rust extension for Python, it uses `maturin` as its build system. 
To compile and install it globally into your active Python environment:

```bash
cd /home/anthony/Documents/OPEN-AIR/BackEnd/ComProtocols/openair-visa
maturin develop
```

This compiles the Rust codebase and makes the `openair_visa` library available to any Python script on the system.

## How the Tests Work

The test suite is driven by a powerful Python script located at `Test/visa_tester.py`. It imports the native `openair_visa` Rust library and orchestrates a full validation sequence.

### Running the Tester

You can execute the tester directly from your terminal:

```bash
python Test/visa_tester.py list
```

### What the Test Script Does:

1. **Backend Initialization**: It boots up the Rust `ResourceManager`.
2. **Network Hunt**: It triggers the Rust scanner, which heavily parallelizes scanning across subnets, probes port 5025/5555, checks USB ports, and listens for mDNS broadcasts.
3. **Identification**: For every resource found (e.g., `TCPIP::44.44.44.33::INSTR`), it sends a `*IDN?` query.
4. **Formatting**: It formats a beautiful CLI table displaying the Resource URI, the raw identification string, and the categorized Device Type.
5. **MQTT Integration**: It kicks off the native Rust MQTT publisher (`publish_devices_mqtt`), pushing device profiles (manufacturer, firmware, status, etc.) to the `OpenAir/System/Protocols/visa/Device/...` topic tree.
6. **Health Validation**: 
   - It sends a `*RST` command to every active device to reset them to a known state.
   - It waits 5 seconds for the hardware to settle.
   - It sends `*STB?` and `:SYST:ERR?` to capture any lingering errors on the hardware.
   - It natively publishes these health results (status bit and error message) back to the MQTT broker.

If a specific gateway or device refuses normal raw TCP sockets (like older VXI-11 hardware), the Rust backend will automatically route the command through the `oa_visa_pyvisa_wrapper` to ensure seamless communication without the Python layer ever knowing the difference!
