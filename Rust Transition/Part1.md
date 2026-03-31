OPEN-AIR Architecture Change Log: Project "Iron Oxide" (Python-to-Rust Migration)
Date: March 30, 2026
Subject: High-Performance Module Overhaul & Distributed Binary Strategy
Status: Architecture Proposal & Implementation Blueprint

1. Executive Summary: The Distributed Binary Strategy
As OPEN-AIR has scaled into a massive, multi-protocol orchestration framework, the Python Global Interpreter Lock (GIL) and dynamic typing overhead have become hard bottlenecks for high-frequency operations.

The Strategy: We will not rewrite OPEN-AIR in Rust. Instead, we will adopt a Distributed Binary Architecture via PyO3 and Cargo.

Compiler-in-Module: Each converted Python module will contain its own isolated Rust src/ directory and Cargo.toml.

Just-in-Time / Install-Time Compilation: The module's Python __init__.py or setup.py will act as a bootstrap. If the compiled binary (.so or .pyd) is missing or outdated, the Python wrapper will transparently invoke cargo build --release locally. This ensures the binary is compiled specifically for the host machine's architecture without requiring pre-compiled binaries in version control.

The Python Supervisor: openair.py remains the high-level orchestrator, but the "heavy lifting" is offloaded to native Rust extensions that look and act like standard Python libraries.

2. Detailed Module Conversion Blueprints
A. oaGuiElements.Core.metering ➔ oaMeteringEngine-rs
What it is: The subsystem responsible for calculating audio ballistics (peak, RMS, falloff, clipping) and rendering procedural visual meters.

Current Limitation: Exponential decay math and real-time UI updates in Python cause UI jitter and high CPU usage. Python's math library and loop execution are too slow for per-sample or high-framerate audio telemetry.

Why Rust is Better: Rust provides zero-cost abstractions and deterministic memory management. It can utilize SIMD (Single Instruction, Multiple Data) instructions to calculate falloff math for 128 audio channels simultaneously.

Implementation Plan:

Create oaMeteringEngine/Cargo.toml utilizing the ndarray and pyo3 crates.

Write a BallisticsEngine struct in Rust that holds state (current peak, hold time).

Expose a single Python function: process_batch(numpy_array_of_levels).

Rust processes the array in parallel using the rayon crate, returning a memory-view of the new meter heights directly to the GUI renderer.

B. oaComBroker (Protocol Router) ➔ oaCoreRouter-rs
What it is: The central nervous system routing thousands of MQTT, OSC, and internal state messages.

Current Limitation: The ProtocolRouter uses Python dictionaries and prefix-trees (Tries) for topic matching. String matching in Python is relatively fast, but doing it 10,000 times a second blocks the main thread.

Why Rust is Better: Rust excels at ultra-fast string parsing and lock-free concurrency. Using crates like regex and crossbeam channels, the router can operate entirely outside the Python GIL.

Implementation Plan:

Build as a standalone background binary (Daemon) managed by the oaThreadManager.

Python passes the socket file descriptor or uses ZeroMQ (ZMQ) to pass raw bytes to the Rust daemon.

Rust handles the Trie-based topic matching and subscription logic.

Rust only wakes up the Python interpreter when a message specifically requires a Python-level GUI update.

C. oaSplinker (Logic Pipeline) ➔ oaSplinkCore-rs
What it is: The inline data modifier (Scale, Invert, Deadband, Debounce).

Current Limitation: Python's function-call overhead. If a fader moves, 100 messages are generated, each passing through 4 Python functions.

Why Rust is Better: Rust functions can be inlined by the LLVM compiler. What takes 4 function calls in Python becomes a single, highly optimized block of machine code.

Implementation Plan:

Use PyO3 to create a PipelineBuilder class.

Python defines the logic at startup: pipeline = SplinkPipeline().add_scale(0, 100).add_deadband(2).

Rust compiles this configuration into an internal struct.

During runtime, Python simply calls pipeline.process(value). Rust executes the math in microseconds and returns the result.

D. oaStateCache ➔ oaStateRegistry-rs
What it is: The global in-memory mirror of the MQTT broker state.

Current Limitation: Thread safety. Multiple GUI elements and backend agents are constantly reading/writing to the global dictionary, requiring heavy threading.Lock() usage, causing contention and UI freezes.

Why Rust is Better: Rust's DashMap (a concurrent hash map) allows lock-free read access and highly granular write locks.

Implementation Plan:

Implement the state cache as a Rust shared library.

Expose thread-safe getters and setters to Python.

Implement a Rust-based "Search Engine" that can execute wild-card topic searches (e.g., OPEN-AIR/devices/*/fader) instantly.

3. How to Execute the Change (Best Practices)
Step 1: The Bootstrapper (compiler_hook.py)
To achieve the "compiler as a part of each module" requirement, create a standard compiler_hook.py that is placed in every converted module.

Python
# oaSplinker/compiler_hook.py
import os, subprocess, sys

def ensure_compiled():
    module_dir = os.path.dirname(__file__)
    binary_name = "oa_splink_core.so" # or .pyd on Windows
    
    if not os.path.exists(os.path.join(module_dir, binary_name)):
        print(f"[{module_dir}] Native binary not found. Compiling via Cargo...")
        try:
            # Requires Maturin: pip install maturin
            subprocess.run(["maturin", "develop", "--release"], cwd=module_dir, check=True)
            print("Compilation successful.")
        except subprocess.CalledProcessError:
            print("CRITICAL: Failed to compile Rust extension. Ensure Rust/Cargo is installed.")
            sys.exit(1)
Step 2: The Module Structure
Reorganize the target modules to contain both Python wrappers and Rust source:

Plaintext
└── oaSplinker/
    ├── __init__.py          # Calls compiler_hook.py, then imports the Rust binary
    ├── compiler_hook.py     # The JIT compilation script
    ├── Cargo.toml           # Rust package definition
    ├── pyproject.toml       # Instructs Python how to build the module
    ├── src/
    │   └── lib.rs           # The Rust PyO3 implementation
    └── Tests/               # Python-based unit tests to verify the Rust binary
Step 3: Integration into Main (openair.py)
Because the Python __init__.py files act as transparent wrappers, openair.py does not need to change its import syntax.

openair.py executes import oaSplinker.

oaSplinker/__init__.py runs the compiler_hook.py.

The hook checks for the compiled .so/.pyd. If missing, it runs cargo build.

The hook imports the highly optimized Rust functions into the Python namespace.

openair.py uses the Rust-backed classes exactly as if they were native Python classes.

Summary of Benefits
By adopting this distributed binary/PyO3 architecture, OPEN-AIR gains C-level performance for its heaviest operations, thread safety without GIL contention, while maintaining the rapid UI development speed of Python for the overarching framework. Furthermore, embedding the compiler ensures cross-platform compatibility without complex CI/CD binary distribution pipelines.