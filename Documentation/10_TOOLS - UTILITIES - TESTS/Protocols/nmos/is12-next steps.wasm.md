# NMOS IS-12 WebAssembly (WASM) Implementation Audit

This audit outlines what it would take to build a fully compliant, registerable NMOS IS-12 Control Protocol device utilizing WebAssembly (WASM), using the `nmos-cpp` mock device as an architectural reference.

## 1. Feasibility & Environment Constraints
**Yes, it is entirely feasible.** The `nmos-cpp` mock device provides a perfect structural blueprint of how the device model, JSON schemas, and state machines should behave. However, WASM introduces strict networking constraints depending on the runtime environment:

* **Browser-based WASM:** Browsers **cannot** host HTTP or WebSocket servers, nor can they perform raw UDP mDNS discovery. A browser-based WASM node would require a lightweight backend "Proxy" (e.g., a simple Node.js or Python server) that handles the actual HTTP/WebSocket listening and forwards the payloads into the WASM module for processing.
* **Server-side WASM (WASI / Node.js / WasmEdge):** If running WASM on a backend runtime, modern WASI (WebAssembly System Interface) extensions or Node.js bindings allow you to bind directly to HTTP/WebSocket ports and run the device entirely autonomously.

## 2. Requirements for a Registered IS-12 Device
To exist on an NMOS network and pass the AMWA test suites, your WASM implementation must fulfill three distinct roles:

### A. IS-04 Registration (The Client)
To be discovered, your device must proactively push its existence to the Registry.
* **Initial POSTs:** Send JSON representations of your `Node`, `Device`, `Source`, `Flow`, `Sender`, and `Receiver` resources to the Registry's `/x-nmos/registration/v1.3/resource` endpoint.
* **Heartbeat:** Maintain a persistent loop that POSTs to `/x-nmos/registration/v1.3/health/nodes/{nodeId}` every 5 seconds to prevent the Registry from garbage-collecting your device.
* **WASM Impact:** Requires outgoing HTTP capabilities (`fetch` API in JS bridging, or WASI HTTP).

### B. IS-04 Node API (The HTTP Server)
Even after registration, peer controllers (and the AMWA testing tool) will attempt to query your node directly.
* **Endpoints:** You must host a basic HTTP server responding to `/x-nmos/node/v1.3/...` returning your self-capabilities.
* **Advertisement:** In your `Device` JSON payload, you must include the `controls` array advertising your IS-12 endpoint (e.g., `urn:x-nmos:control:ncp/v1.0` pointing to your WebSocket URL).

### C. IS-12 Control Protocol (The WebSocket Server)
This is the core of the implementation.
* **WebSocket Hosting:** You must listen on a WebSocket route (e.g., `/x-nmos/ncp/v1.0`).
* **NCP Command Processor:** The WASM module must ingest incoming IS-12 JSON RPC commands, route them to the correct internal Object IDs (OIDs), and return synchronous JSON responses.
* **Subscription Engine:** The WASM module must maintain a list of active WebSocket clients and push asynchronous property-change notifications when internal values (like gain or mute) change.

## 3. The WASM Core: The MS-05 Device Model
The heaviest lifting—and the part most suited for WASM—is maintaining the **MS-05 Device Model**. This is an object-oriented tree of your device's capabilities. 

Looking at how `nmos-cpp` does it, your WASM core needs to implement:
1. **The Root Block (OID 1):** The top-level container holding everything else.
2. **Managers:** 
   * `ClassManager`: Reports what features your device supports.
   * `DeviceManager`: Reports system status.
3. **Workers/Touchpoints:** The actual audio/video parameters (e.g., a Stereo Gain `NcWorker` object with a `gain` property and `constraints` limiting it from -100dB to +20dB).
4. **JSON Schema Validator:** The AMWA tests require strict adherence to the NCP JSON Schema. The WASM module will need a fast JSON parser/validator to reject malformed commands with a `400 Bad Request` before attempting to process them.

## 4. Recommended Tech Stack
Given the need for strict memory safety, rich structs, and fast JSON processing, **Rust** is the ideal language for compiling this NMOS core to WASM.

* **Language:** Rust
* **WASM Target:** `wasm32-unknown-unknown` (for browser) or `wasm32-wasi` (for server).
* **State Machine:** Implement the MS-05 device tree purely in Rust. It takes JSON strings as input, mutates its internal struct tree, and returns JSON strings as output.
* **Networking Boundary:** Use Javascript (or a host backend language) to handle the actual WebSocket/HTTP server bindings, feeding the raw string payloads into the Rust WASM module's exposed memory.

## 5. Next Steps
1. **Define the Device Model:** Map out the exact tree of MS-05 objects your specific device needs (e.g., do you just need simple gain controls, or full IS-08 channel mapping?).
2. **Extract JSON Schemas:** Pull the official IS-12 JSON schemas (available in the AMWA spec or inside the `nmos-cpp` source) to use for command validation.
3. **Build the WASM State Machine:** Write a decoupled, pure-logic module that can ingest an IS-12 `Get` or `Set` JSON command and successfully update a mock memory property.
4. **Wrap in a Host:** Wrap the WASM module in a basic Node.js Express/ws server to handle the IS-04 HTTP endpoints and IS-12 WebSocket traffic.
