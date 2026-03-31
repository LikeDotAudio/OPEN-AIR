OPEN-AIR Architecture Change Log: Project "Iron Oxide" (Phase 2)
Date: March 31, 2026
Subject: Mass Expansion of the Distributed Binary Strategy (30 Additional Modules)
Status: Architecture Proposal & Implementation Blueprint

Following the initial success metrics of the JIT-compiled Rust/PyO3 architecture, this document outlines the conversion of 30 additional modules. These modules have been selected based on their CPU-bound bottlenecks, heavy I/O requirements, or necessity for strict memory safety in concurrent environments.

All modules below will follow the Distributed Binary Strategy outlined in Phase 1: they will contain a Cargo.toml, a src/lib.rs for the PyO3 bindings, and a compiler_hook.py in their __init__.py to ensure local JIT compilation.

Category 1: Real-Time Protocol Translators & Networking
These modules handle intense byte-level parsing, serialization, and high-frequency socket communication where Python's GIL and object overhead cause latency.

1. oaComAES70 ➔ oaAES70Core-rs

What it is/does: Implements the Open Control Architecture (OCA) standard, parsing OCP.1 (TCP/IP) messages to communicate with professional amplifiers.

Why Rust: AES70 relies heavily on strict binary unmarshalling and endianness conversions. Rust's nom parser combinator framework is magnitudes faster and memory-safe compared to Python's struct.unpack.

How to Change & Integrate: Rewrite the byte-deserializer in Rust. Expose a Python class OcaParser. Python passes raw socket byte-arrays (bytes) to OcaParser.decode(), which returns a clean Python dictionary of the OCA payload.

2. oaComEmber ➔ oaEmberTree-rs

What it is/does: Parses Ember+ (a tree-structured control protocol used in broadcast).

Why Rust: Ember+ uses ASN.1 BER (Basic Encoding Rules). Parsing deeply nested BER trees dynamically in Python is highly recursive and CPU-intensive. Rust can traverse and decode these trees recursively with near-zero allocation.

How to Change & Integrate: Build a Rust BER decoder. In Python, replace the packet ingest logic: tree_state = rust_ember.parse_ber_payload(raw_bytes).

3. oaComMidi ➔ oaMidiEngine-rs

What it is/does: Handles real-time MIDI input/output, translating physical fader moves to internal values.

Why Rust: MIDI requires strict sub-millisecond timing. Python's garbage collection pauses can cause audible latency or missed MIDI clock ticks.

How to Change & Integrate: Use the Rust midir crate to handle the OS-level MIDI API completely outside Python. The Rust engine buffers events and pushes them to the Python oaComBroker in optimized, time-stamped batches via a PyO3 callback.

4. oaComREST ➔ oaFastAPI-rs

What it is/does: Serves the HTTP API for external web dashboards.

Why Rust: As telemetry data scales, serializing massive JSON objects for HTTP responses blocks Python. Rust frameworks (like axum or actix) combined with serde_json can saturate a 10Gbps link without breaking a sweat.

How to Change & Integrate: Replace the Python web server (e.g., Flask/Uvicorn) with a Rust binary thread. Python logic registers routes via PyO3: rest_server.add_route("/api/state", python_callback_func).

5. oaComSMPTE2138 ➔ oaST2138Codec-rs

What it is/does: Bridges internal MQTT actions to Protobuf-encoded SMPTE namespaces.

Why Rust: Protocol Buffers are natively typed. Python's dynamic Protobuf implementation is notoriously slow. Rust's prost crate compiles .proto files into blazing-fast native structs.

How to Change & Integrate: Compile the SMPTE .proto schemas in build.rs. Python calls st2138_codec.encode_state(topic, value), returning the raw bytes for the network socket.

6. oaComSNMP ➔ oaSNMPAgent-rs

What it is/does: Acts as an SNMP agent, translating OID requests into MQTT state queries.

Why Rust: SNMP MIB tree walking (GetNext, Walk) requires traversing thousands of text-based OIDs. Rust's BTreeMap handles this OID routing instantly.

How to Change & Integrate: Move the OID tree registry to Rust. Python updates the Rust tree asynchronously: snmp_tree.update("1.3.6.1.4.1...", new_value). Rust handles the actual UDP packet responses natively.

7. oaComVisa ➔ oaVisaFormat-rs

What it is/does: Generates SCPI string commands for lab instrument control.

Why Rust: String interpolation in Python for thousands of floating-point telemetry values is slow. Rust's formatting macros and static memory allocation eliminate this overhead.

How to Change & Integrate: Create a Rust SCPI formatter. Python calls visa.format_command("SET_VOLTAGE", 5.0134), and Rust returns the strictly terminated byte-string ready for the VISA socket.

8. oaPTP ➔ oaPTPClock-rs

What it is/does: Precision Time Protocol (IEEE 1588) listener for media network clock sync.

Why Rust: PTP requires nanosecond-level timestamping of network packets. Python cannot do this accurately. Rust can interface directly with OS-level hardware timestamping (SO_TIMESTAMPING).

How to Change & Integrate: Build a standalone Rust thread that listens on the PTP multicast address. It exposes a lock-free getter to Python: current_ptp_time = ptp_engine.get_nanos().

Category 2: Massive Data Parsing & File I/O
These modules read, parse, and write massive files where Python's single-threaded disk I/O and dynamic typing create long loading screens.

9. oaFileImportCSV ➔ oaCSVParser-rs

What it is/does: Ingests massive routing tables or equipment lists.

Why Rust: Rust's polars or csv crates can parse gigabytes of CSV data per second, automatically inferring types and handling malformed rows cleanly without Python's memory bloat.

How to Change & Integrate: Python passes a file path: dataframe = rust_csv.load_and_validate(filepath, expected_schema).

10. oaFileExportCSV ➔ oaCSVWriter-rs

What it is/does: Dumps audit logs and telemetry histories to disk.

Why Rust: Writing line-by-line in Python blocks the GUI. Rust can asynchronously stream data from memory to disk in a background thread.

How to Change & Integrate: Python passes an iterator or list of dictionaries to rust_csv.dump_async(data_list, filepath).

11. oaFileImportHTML ➔ oaHTMLScraper-rs

What it is/does: Extracts equipment tables from vendor-provided HTML reports.

Why Rust: Parsing messy DOM trees using Beautiful Soup in Python is very slow. Rust's scraper or html5ever (from Servo) parses DOMs at C-speeds.

How to Change & Integrate: Python passes raw HTML text. Rust queries it using CSS selectors and returns a clean Python list of dictionaries representing the tables.

12. oaFileImportShow ➔ oaShowfileUnpacker-rs

What it is/does: Unpacks proprietary .show binary archives.

Why Rust: Decompressing and decoding custom binary headers is safer in Rust, preventing buffer overflow attacks from corrupted showfiles.

How to Change & Integrate: Python passes the .show filepath. Rust decrypts, unzips to memory, parses the manifest, and returns a structured configuration object.

13. oaReports ➔ oaReportGen-rs

What it is/does: Generates PDF compliance and audit reports.

Why Rust: PDF generation in Python (e.g., ReportLab) is slow and difficult to multi-thread. Rust can render complex PDFs concurrently using crates like printpdf.

How to Change & Integrate: Python builds a JSON representation of the report schema. rust_report.build_pdf(json_schema, output_path) handles the layout and disk write.

14. oaConfiguration ➔ oaConfigEngine-rs

What it is/does: Parses INI, TOML, and JSON startup files.

Why Rust: Deep validation of configuration schemas is essential. Rust's serde can deserialize and strictly validate types, ranges, and missing fields instantly upon boot.

How to Change & Integrate: Replace the startup configparser. Python calls config = rust_config.load("settings.toml"), receiving a frozen, validated dictionary.

15. oaDocumentation ➔ oaMarkdownCompiler-rs

What it is/does: Dynamically compiles the application's internal help files from Markdown to HTML for the WYSIWYG editor.

Why Rust: Regex-heavy Markdown parsing is slow. Rust's pulldown-cmark crate is an industry-standard, ultra-fast Markdown compiler.

How to Change & Integrate: On boot, Python calls html_string = rust_md.render(markdown_string).

16. oaStand_Alone_Utilities (realign_logs) ➔ oaLogAligner-rs

What it is/does: A utility to ingest dozens of log files, sort them by microsecond timestamps, and merge them.

Why Rust: Sorting millions of text lines based on datetime string parsing is a massive CPU task. Rust can memory-map (mmap) the files, parse timestamps via SIMD, and sort out-of-core.

How to Change & Integrate: Python subprocess calls the Rust binary: subprocess.run(["oa_log_aligner", "--dir", "./logs"]).

Category 3: High-Frequency Data Management & Core State
These modules manage the internal plumbing, state diffing, and threading of the application.

17. oaDataAudits ➔ oaStateDiffer-rs

What it is/does: Compares the "Expected State" of the system vs. the "Actual State" queried from devices.

Why Rust: Diffing two complex JSON trees or dictionaries of 100,000 keys causes massive garbage collection pauses in Python. Rust can hash and diff struct trees in parallel.

How to Change & Integrate: Python passes two dictionaries to rust_differ.compare(expected, actual). Rust returns a list of delta topics (e.g., ["OPEN-AIR/fader/1: mismatch"]).

18. oaDataLogs ➔ oaAsyncLogger-rs

What it is/does: The central pipeline for writing system events to disk.

Why Rust: High-throughput logging can block the main thread. Rust provides lock-free ring buffers (like crossbeam::ArrayQueue) to instantly accept logs and write them to disk in a separate OS thread.

How to Change & Integrate: Replace loguru or standard logging handlers with a PyO3 bridge: rust_logger.info("System booted").

19. oaDataSNMP ➔ oaMIBCache-rs

What it is/does: Caches massive vendor MIB (Management Information Base) definitions.

Why Rust: Searching for an OID name inside a memory structure of 50,000 parsed MIB text files requires fast text search algorithms (like Aho-Corasick), which Rust implements perfectly.

How to Change & Integrate: Python initializes the cache: mib_db = rust_mib.load_directory("./mibs"). Queries: name = mib_db.resolve("1.3.6.1...").

20. oaDataSplinks ➔ oaSplinkGraph-rs

What it is/does: Stores the routing topology (which input affects which output).

Why Rust: Evaluating cyclic dependencies in a splink routing graph requires fast graph traversal. Rust's petgraph detects infinite loops in user-defined routing instantly.

How to Change & Integrate: Python registers links: graph.add_edge("fader_1", "mqtt_out_2"). Before applying, Python calls graph.is_valid().

21. oaDataCache ➔ oaDiskFlusher-rs

What it is/does: Periodically flushes the in-memory state to a local SQLite/JSON backup.

Why Rust: Serializing the entire state cache to JSON blocks the GIL. Rust can take a read-lock, clone the state natively, and handle the SQLite transaction without pausing the Python UI.

How to Change & Integrate: Python triggers the save: rust_cache.trigger_snapshot().

22. oaThreadManager ➔ oaThreadPool-rs

What it is/does: Manages worker threads for background tasks.

Why Rust: Python's ThreadPoolExecutor is still bound by the GIL for CPU tasks. Rust can spawn native OS threads (via rayon) that execute PyO3 functions completely parallel to the main Python thread.

How to Change & Integrate: Wrap Python math/logic tasks in a Rust scheduler: rust_pool.spawn(python_callback).

23. oaOchestration ➔ oaHeartbeatCore-rs

What it is/does: Monitors the health of all subsystems and handles graceful degradation.

Why Rust: The orchestrator must never crash. Rust's strict panic-handling and lack of null pointers guarantee that the watchdog itself remains immortal.

How to Change & Integrate: Python subsystems send UDP heartbeats to the Rust daemon. If a module hangs, Rust sends a SIGKILL/SIGTERM via OS APIs.

Category 4: GUI Math, Media & Layout Engines
These modules support the oaGuiElements by doing the heavy calculations required for rendering, rather than the rendering itself.

24. oaGuiTelemetry ➔ oaTimeSeriesDB-rs

What it is/does: Aggregates real-time data for GUI strip charts and histograms.

Why Rust: Constantly appending to Python lists and culling old data (e.g., maintaining a 60-fps rolling window of 1000 points) is highly inefficient. Rust's VecDeque handles this with zero reallocation overhead.

How to Change & Integrate: Python pushes data: telemetry.push(val). UI requests frame data: telemetry.get_window(), which returns a contiguous memory block (numpy array) to the UI framework.

25. oaGuiMediaElements ➔ oaImageScaler-rs

What it is/does: Resizes, caches, and compresses thumbnail images for the UI.

Why Rust: Image processing (downsampling, Lanczos filtering) is pure math. Rust's image crate performs these operations multi-threaded, outperforming Python's PIL/Pillow in batch operations.

How to Change & Integrate: Python passes a file list: rust_media.generate_thumbnails(["/img1.jpg", "/img2.jpg"], 128).

26. oaStyle ➔ oaCSSParser-rs

What it is/does: Parses OPEN-AIR's custom stylesheet formats to style the internal GUI.

Why Rust: Cascading style logic requires resolving hundreds of specific rules against UI element classes. A Rust parser can pre-calculate the final computed styles for all elements in milliseconds.

How to Change & Integrate: Python passes the style string. Rust returns a flattened dictionary mapping UI IDs to specific RGB/font values.

27. oaGuiBuildShell ➔ oaLayoutEngine-rs

What it is/does: Calculates absolute X/Y pixel coordinates from relative GUI definitions (like Flexbox).

Why Rust: Computing responsive layouts dynamically when the window resizes requires heavy tree-traversal math. Using a Rust engine like Taffy (used in modern UI frameworks) solves layout math instantly.

How to Change & Integrate: Python constructs the UI tree in Rust. On resize, Python calls layout.compute(), and Rust updates the X/Y properties of all Python widget objects.

28. oaGuiEditorWYSIWYG ➔ oaHitboxMath-rs

What it is/does: Handles mouse-picking, bounding-box collisions, and z-index sorting for the drag-and-drop UI editor.

Why Rust: Checking if a mouse coordinate intersects with 5,000 rotated and scaled widgets requires matrix transformations. Rust excels at linear algebra (using nalgebra).

How to Change & Integrate: Python passes mouse coordinates: rust_hitbox.get_element_at(x, y). Rust calculates matrix inversions and returns the UUID of the clicked element.

29. oaGuiFolderParser ➔ oaFastDir-rs

What it is/does: Scans the OS filesystem to build the media and project library trees.

Why Rust: Deep recursive directory traversal in Python (os.walk) is slow on network drives. Rust's ignore or walkdir crates execute directory walking natively and concurrently.

How to Change & Integrate: tree = rust_fs.scan_directory("/media/library", extensions=[".wav", ".png"]).

30. oaTranslator (Manifest Builder) ➔ oaManifestGen-rs

What it is/does: Compiles all internal UI layouts, routes, and splinks into a massive single JSON manifest for network broadcast.

Why Rust: Concatenating, validating, and escaping massive JSON payloads from disparate Python objects is slow. Rust can ingest the raw object data, serialize it natively using serde_json, and compress it (gzip) in one pass.

How to Change & Integrate: Python hands off the top-level state objects. rust_manifest.build_and_compress(gui_state, routing_state) returns the compressed byte payload ready for MQTT broadcast.