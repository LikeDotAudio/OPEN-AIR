# YAK Protocol Resolvers Audit & Strategy

## 1. Architectural Audit

### Overview
The `openair-yak/10_Yak` directory contains a structured repository of JSON-based definitions that map UI elements (blocks, inputs, actuators) directly to instrument control commands (SCPI/text). The structure is logically organized by:
`Equipment Class (e.g., Spectrum_YAK) -> Model (e.g., N9340B) -> Functional Category (e.g., Frequency, Bandwidth)`

### Strengths (What works well)
*   **Declarative GUI-to-Command Mapping:** The JSON cleanly links a user action (a `_GuiActuator` button) to a specific hardware command (e.g., `:FREQuency:STARt <hz_value>`).
*   **Parameterized Execution:** Variables in the command strings (`<start_freq>`, `<hz_value>`) map directly to `_GuiValue` input fields, making dynamic command generation straightforward.
*   **Send & Receive Placeholders (I/O Mapping):** The structure elegantly handles both sending commands and receiving query responses. 
    *   **Send:** A block uses an `"Input"` object with named fields (e.g., `hz_value`) that map directly to the placeholders in the actuator's message string (e.g., `:FREQuency:STARt <hz_value>`).
    *   **Receive:** For queries, an `"Outputs"` object acts as the receive placeholder. When a query command (e.g., `:FREQuency:STARt?;:FREQuency:STOP?`) is executed, the `"Outputs"` block defines the destination variables (e.g., `start_freq`, `stop_freq`) sequentially mapped to capture the instrument's return values.
*   **Internationalization (i18n) Baked In:** Support for multiple languages (`En`, `Fr`, `De`, `Es`) is built directly into the component labels.
*   **Hierarchical Organization:** Grouping commands into functional blocks (`freq_start_stop`, `Span_Frequency`) provides a ready-made layout structure for rendering.
*   **Optimal Directory Taxonomy (Class -> Model):** The current folder structure (`1_Spectrum_YAK -> 1_N9340B`) is perfectly designed for enterprise scalability. By sorting by Equipment Class first rather than Model Number:
    *   **Hardware Abstraction:** It forces a focus on abstract capabilities ("I need a Spectrum Analyzer") rather than specific hardware, making it easier to build a Hardware Abstraction Layer (HAL).
    *   **Discoverability:** It prevents the top-level directory from becoming a confusing, flat list of cryptic alphanumeric model numbers (e.g., `3235`, `E4411A`), instantly providing context to new developers.
    *   **Clean API Routing:** It allows backend APIs to easily serve up "all available models for a given class" to a frontend UI simply by querying a specific class folder.

### Weaknesses & Limitations
*   **Tight Coupling of UI and Protocol:** The protocol definitions contain highly specific UI styling data (`text_color`, `bg_color`, `border_thickness`, `glow_intensity`, `layout_columns`). This bloats the protocol layer and requires scripts (like `update_yak_router.py`) just to change a button's height.
*   **State & Validation:** The JSON is static. It does not natively handle complex instrument state dependencies (e.g., disabling the 'Span' input if the analyzer is in 'Zero Span' mode).

---

## 2. Strategic Vision: How Best to Use YAK Translators

Your original thought—using these as GUI elements for fast, quick testing—is exactly the sweet spot for this architecture, but it can be expanded into a much more powerful system. Here is a strategy for maximizing their utility:

### Phase 1: The "Soft Front Panel" Engine (Your original idea)
These JSON files are essentially blueprints for auto-generating **Soft Front Panels (SFPs)**. 
*   **Actionable Step:** Build a lightweight rendering engine (e.g., a React/Vue web app or a Python/PyQt desktop app) that ingests a YAK JSON file and dynamically generates the form. 
*   **Value:** When an engineer connects a new piece of equipment in the lab, they don't need to read the manual or write a script to test it. They just load the YAK JSON into the renderer and get an instant, interactive GUI to fire commands at the instrument. This is invaluable for rapid prototyping and debug.

### Phase 2: Decoupling and the "Driver Generator"
To make the system maintainable, the "look and feel" should be stripped out of the protocol JSON.
*   **Actionable Step:** Separate the YAK files into two layers: 
    1.  **Protocol Map (The Logic):** Maps semantic actions ("SetCenterFreq") to SCPI strings (`:FREQuency:CENTer <val>`).
    2.  **UI Theme (The View):** A separate stylesheet or JSON that defines how actuators and values should look (`glow_intensity`, colors).
*   **Value:** Once the protocol map is clean, you can use these JSON files to **auto-generate code**. A simple script could read `yak_frequency.json` and automatically output a Python API driver class for the N9340B, saving hours of manual driver writing.

### Phase 3: Hardware Abstraction Layer (HAL)
By standardizing the `OcaBlock` and field names across different models of the same equipment class, YAK becomes a universal translator.
*   **Actionable Step:** Ensure that every Spectrum Analyzer YAK file uses the exact same variable name for Center Frequency (e.g., `center_freq`). 
*   **Value:** Your automated tests can run against an abstract "Spectrum Analyzer" object. The YAK layer acts as the HAL, translating the generic "Set Center Frequency" request into the specific SCPI syntax required for the Agilent N9340B vs. a Rohde & Schwarz analyzer.

### Phase 4: "Reverse YAK" for Digital Twins
Because you have a mapping of commands to variables (e.g., `:FREQuency:STARt <start_freq>`), you can run the YAK resolver in reverse.
*   **Actionable Step:** Feed these JSON files into a mock server.
*   **Value:** When the mock server receives `:FREQuency:STARt 1000`, it uses the YAK definition to parse the command and update its internal `start_freq` state to 1000. You now have instant, auto-generated digital twins for your hardware, allowing software teams to write and test automation scripts without needing the physical instruments.

### Phase 5: Forensic Computer Science & System Auditing
The structured `Input` and `Outputs` mappings provide a unique opportunity for digital forensics in automated test environments. 
*   **Actionable Step:** Insert a logging middleware layer between your test runner and the physical instrument that uses the YAK JSON to translate raw SCPI bytes back into human-readable, semantic state changes.
*   **Value:** Instead of just logging cryptic raw commands (e.g. `Tx: :FREQ:CENT 1000`), the system can log the *intent* and the *result* (e.g. `System changed [Center Frequency] to [1000 Hz]`). If a piece of hardware fails or a test suite yields corrupted data, a forensic analysis can perfectly reconstruct the exact timeline of states the machine was placed in. Because the YAK resolvers strictly define what is being sent and received, they act as the "Rosetta Stone" for analyzing and reverse-engineering hardware communication logs.

## Conclusion
The YAK architecture is highly valuable. Your intuition to use them for quick GUI testing is correct and should be the primary use case. To scale it to enterprise level, the focus should be on separating the UI styling from the command mapping, which will unlock the ability to use these files for auto-generating code, standardizing drivers, and creating hardware simulators.
