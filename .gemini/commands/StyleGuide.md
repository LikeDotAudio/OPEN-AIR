# OPEN-AIR Code Style & Architectural Guide

## I. Project Architecture: The `oa*` Standard
The **OPEN-AIR** system is built on a modular, partitioned architecture. Every module must adhere to the following structural and organizational rules:

### 1. The 12-Subfolder Standard
Every `oa*` module (e.g., `oaComMQTT`, `oaGuiBuilder`) must contain these specific subdirectories:
- `Core`: Low-level logic, data models, and foundational services.
- `Workers`: Background processes, threaded tasks, and long-running services.
- `Managers`: High-level orchestrators and state management.
- `Methods`: Stateless utility functions and helper logic.
- `Constants`: Module-specific static values and configurations.
- `Tests`: Unit and integration tests (following F.I.R.S.T. principles).
- `Documentation`: Module-specific `.md` files and design specs.
- `Assets`: Icons, JSON blueprints, and static resources.
- `Interface`: UI components or public API definitions.
- `Hooks`: Event listeners and callback registries.
- `FileReaders`: Logic for ingesting data (CSV, JSON, etc.).
- `FileWriters`: Logic for exporting data.

### 2. The Root Rule & Gatekeeper
- **No files are permitted in the root of an `oa*` directory except for `Entry.py`.**
- `Entry.py` serves as the **Gatekeeper**: it is the sole public API for the module.
- All internal logic must be imported into `Entry.py` and exposed via the `__all__` list.

## II. Coding Standards & Implementation

### 1. Function & Variable Design
- **No Magic Numbers**: All raw numbers must be assigned to named constants before use.
- **Named Arguments**: All function calls must pass arguments by name (e.g., `connect(address="localhost", port=1883)`) for clarity.
- **Single Responsibility**: Functions must perform exactly one task and descend only one level of abstraction.
- **Resource Safety**: Always use context managers (`with`) or `finally` blocks for file, socket, or database operations.

### 2. Logic & Performance
- **Partitioned Architecture**: Maintain a strict separation between **Core (Logic)** and **UI (Display)**. UI layers must not directly import low-level infrastructure.
- **Anti-Loop Patterns**: Never execute database commits or network calls inside loops. Use $O(1)$ lookups (Sets/Dictionaries) for large datasets.
- **Memory Discipline**: Use generators for large data processing; avoid `.read()` on files of unknown size.

## III. Logging & Forensics
The system uses a "Directional Observability" model for debugging and tracing:

- **Ingress/Inbound**: Prefix with `📡📥📥 [CATEGORY]`.
- **Egress/Outbound**: Prefix with `📡📤📤 [CATEGORY]`.
- **Debug Gates**: All granular `trace()` and `debug()` calls must be wrapped in `if LOCAL_DEBUG:` or equivalent flags to minimize overhead.
- **Emoji Categories**: Use domain-specific emojis (🚀 `[DEPLOY]`, 📡 `[SENSOR]`, 🎨 `[RENDER]`).
- **No Message Boxes**: Communicate alerts via console logs or the UI's status bar; never use intrusive pop-up dialogs.

## IV. Documentation & Versioning

### 1. Mandatory File Header
Every Python file must start with a header in the following format:
```python
# FolderName/FileName.py
# Author: [Author Name]
# Version: [W.X.Y]
#
# Description: [Brief summary of purpose]
```

### 2. Versioning (W.X.Y)
- **W**: Date (YYYYMMDD).
- **X**: Time (HHMM, no leading zero).
- **Y**: Revision/Patch number.
Example: `20260322.1430.1`

### 3. Change Tracking
Every significant change must be documented in `oaDataLogs/ChangeLog/CHANGELOG.md` with a timestamped entry.

## V. Testing Protocol (F.I.R.S.T.)
- **Fast**: Tests must run quickly.
- **Independent**: Tests must not depend on each other.
- **Repeatable**: Results must be consistent across environments.
- **Self-Validating**: Tests must have a clear pass/fail output.
- **Timely**: Tests should be written alongside or before the code they verify.
- **Structure**: Use the **Build-Operate-Check** pattern for all test cases.
