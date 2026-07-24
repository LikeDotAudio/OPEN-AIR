# YAK Protocol: Backend Architecture & GUI Integration Proposal

## 1. Executive Summary
This proposal outlines the architectural strategy for the YAK Protocol Resolvers. The goal is to establish the Backend as the definitive "Single Source of Truth" for all hardware communication definitions, while seamlessly serving these definitions to the Frontend to fulfill their original intent: auto-generating dynamic "Soft Front Panels" for rapid GUI testing.

## 2. The Architectural Challenge
The YAK JSON files are currently a hybrid entity. They contain:
1. **Frontend Concerns:** UI styling, layout columns, labels, and i18n translations.
2. **Backend/Hardware Concerns:** Low-level SCPI strings, parameters, and query structures.

Placing them exclusively in the Frontend orphans the Backend, making it impossible to perform automated forensic logging or generate digital twins. Placing them in the Backend raises the question of how the Frontend can use them for GUI testing. 

## 3. Proposed Solution: The "Hardware Gatekeeper" Model
The YAK files will remain in their current location: `/BackEnd/ComProtocols/openair-yak/`. 

The Backend will act as the gatekeeper for all hardware. The Frontend will remain completely ignorant of SCPI commands, baud rates, or instrument-specific string formatting. Instead, the Backend will serve the YAK JSON files to the Frontend via an API, allowing the Frontend to dynamically render the GUI.

### 3.1 Workflow: Discovery & GUI Instantiation
1. **The Discovery Window (Input):** A user navigates to the "Discovery" window in the Frontend UI and types in an instrument's IP address, VISA resource string (e.g., `TCPIP0::192.168.1.100::inst0::INSTR`), or serial port. 
2. **Identification (The Handshake):** The Frontend passes this address to the Backend. The Backend opens a temporary connection to the physical hardware and sends the universal IEEE-488.2 Identification Query (`*IDN?`).
3. **Model Resolution (The YAK Lookup):** The physical instrument responds with its identification string (e.g., `Agilent Technologies, N9340B, MY1234567, 1.02`). The Backend parses this string, extracts the model number (`N9340B`), and searches the `/10_Yak/` directory tree for a matching model folder.
4. **GUI Instantiation (Schema Delivery):** 
   - If a matching YAK folder is found, the Backend establishes a persistent session tying that physical IP to the logical YAK model.
   - The Backend streams the relevant YAK JSON schemas (e.g., `yak_frequency.json`) to the Frontend via a REST or WebSocket endpoint.
5. **Dynamic Rendering:** The Frontend automatically pops open a new "Soft Front Panel" tab or window. It parses the `_GuiActuator` and `_GuiValue` blocks to dynamically draw the buttons, layout, and input fields, making the instrument instantly available for manual GUI testing.

### 3.2 Workflow: Executing a Command
1. **User Action:** The engineer types "1000" into the Center Frequency input and clicks the "Set Center Frequency" actuator button on the generated GUI.
2. **Logical Payload:** The Frontend **does not** construct a SCPI string. Instead, it sends a semantic JSON payload back to the Backend:
   ```json
   {
     "instrument": "N9340B",
     "action": "Execute Command",
     "block": "freq_start_stop",
     "parameters": {
       "hz_value": 1000
     }
   }
   ```
3. **Backend Resolution:** The Backend receives this payload, looks up the corresponding YAK JSON file in its `/ComProtocols/` directory, maps the `hz_value` to the placeholder, and constructs the final hardware string: `:FREQuency:STARt 1000`.
4. **Execution:** The Backend transmits the string to the physical instrument over TCP/GPIB/USB.

### 3.3 Cross-GUI Communication (Unrelated Windows)
A major advantage of this architecture is how it handles unrelated UI elements (e.g., an automated Test Sequence Builder, a Data-Logging Chart, or a Macro Recorder).
*   **The YAK is just a schema:** Unrelated windows do **not** need to read or understand the YAK JSON files to communicate with hardware. 
*   **The Universal API:** Instead of talking to the YAK files directly, other GUI elements simply talk to the Backend's Execution API (as seen in Section 3.2). 
*   **Example:** A "Run Sequence" window can dispatch an array of logical payloads: `[{action: "Set Center Frequency"}, {action: "Set Span"}]`. The Backend acts as the universal router—it receives the generic semantic commands from the sequence window, uses the YAK schema in the background to translate them into SCPI, and executes them. The GUI elements remain completely decoupled from the hardware layer abstractions.

### 3.4 The YAK Engine API: An MQTT Pub/Sub Strategy
Given that the GUI communicates via MQTT, the YAK Engine should run as a standalone microservice (or internal daemon) that acts as an MQTT Client. This transforms the YAK Engine into a real-time, event-driven Hardware Command Server.

**1. Topic Structure Strategy:**
The API is defined by an organized hierarchy of MQTT topics:
*   **Command Topics (`openair/yak/cmd/<instrument_id>/<block>/<action>`):** 
    Any client (GUI, script, or other backend service) can publish a logical JSON payload to this topic. The YAK Engine subscribes to `openair/yak/cmd/#`. When a message arrives, the YAK Engine resolves it via the JSON schemas, translates it to SCPI, and dispatches it to the physical hardware.
*   **State/Telemetry Topics (`openair/yak/state/<instrument_id>/<block>/<variable>`):**
    When the hardware responds to a query (or when the YAK Engine polls the hardware for state updates), the YAK Engine publishes the parsed value to this topic.

**2. How the GUI Connects:**
*   **Decoupled Real-Time Updates:** The "Soft Front Panel" generated in the UI subscribes to the relevant `state/#` topics for its specific instrument. If an automated script changes the frequency, the YAK Engine publishes the new frequency to the state topic, and the GUI's text fields/gauges update instantly. 
*   **Execution:** When a user clicks a button in the GUI, the frontend simply publishes the parameter payload to the corresponding `cmd` topic. 

**3. Why MQTT is the Perfect Fit:**
*   **Many-to-Many Architecture:** Multiple GUIs or scripts can monitor the same spectrum analyzer simultaneously without polling the hardware multiple times. 
*   **Asynchronous Flow:** Hardware communication can be slow. MQTT prevents the GUI from freezing while waiting for an HTTP REST response. The GUI publishes a command and independently waits for the state topic to update.

### 3.5 YAK Schema Data Structure (I/O Mapping Strategy)
The internal structure of the YAK files utilizes `Input` and `Outputs` blocks to map generic variables to SCPI commands. Does this structure make sense?

**1. The `Input` Structure (Sending Commands): Highly Effective**
*   **How it works:** The `message` string acts as a template (e.g., `:FREQuency:STARt <start_freq>`), and the `Input` block defines the variables.
*   **Verdict:** This is standard, robust string-templating. The Backend can safely and efficiently inject values from the MQTT payload into the SCPI string before sending. 

**2. The `Outputs` Structure (Parsing Responses): Fragile (Requires Refactoring)**
*   **How it works:** A query (e.g., `:FREQuency:STARt?;:FREQuency:STOP?`) returns a comma-separated string from the hardware (e.g., `"1000.0, 2000.0"`). The current `Outputs` block simply lists `start_freq` and `stop_freq` sequentially. 
*   **Verdict:** Relying strictly on the implicit top-to-bottom order of JSON keys to map an array of return values is dangerous. If a developer accidentally alphabetizes the `Outputs` keys in the JSON, `start_freq` will start silently receiving `stop_freq` data.
*   **Proposed Fix:** Add explicit parsing metadata to the `Outputs` fields. For example, add an `index` property, a `delimiter`, or a `regex` matcher so the Backend YAK Engine knows exactly how to extract the correct value from the raw hardware response string:
    ```json
    "Outputs": {
      "delimiter": ",",
      "fields": {
        "start_freq": { "index": 0, "type": "float" },
        "stop_freq": { "index": 1, "type": "float" }
      }
    }
    ```

## 4. Key Benefits of This Architecture

*   **Security & Abstraction:** The Frontend remains lightweight and isolated. It never needs to know the complex syntax of SCPI hardware control.
*   **Zero-Friction GUI Testing:** You retain the original vision. The moment a new YAK file is dropped into the Backend directory, the Frontend can instantly render a functional testing GUI for that instrument without writing a single line of new HTML/JS.
*   **Enables Forensic Auditing:** Because the Backend handles the translation, it can intercept the flow to log the forensic timeline (e.g., "User clicked 'Set Center Frequency' -> Translated to ':FREQ:CENT 1000'").
*   **Enables Digital Twins:** The Backend can easily route the SCPI string to a mock hardware simulator instead of a real instrument for software-in-the-loop testing.

## 5. Next Steps
1. **API Implementation:** Create a simple endpoint in the Backend framework to serve the JSON files from the `/10_Yak` directory.
2. **Frontend Parser:** Build a generic "YAK Renderer" component in the Frontend that iterates through `OcaBlock` structures to construct a generic testing form.
3. **Execution Endpoint:** Create the Backend endpoint that accepts the logical payload from the Frontend, resolves it using the YAK files, and dispatches the command.
