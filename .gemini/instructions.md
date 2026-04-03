### **OPEN-AIR SYSTEM OPERATING PARAMETERS: 202603-F (LINUX OPTIMIZED)**

oaDATA**** folders are repositories for data logging - exclude them from any functional analysis.

---
## **I. EFFICIENCY & CONTEXT OPTIMIZATION**
1.  **Inventory Protocol**: Execute `ls -R` or use `glob` to map project structure before file ingestion.
2.  **Targeted Retrieval**: Utilize `grep_search` to isolate specific logic blocks; do not read unrelated utility files.
3.  **Dependency Mapping**: Identify linked modules via imports or `package.json` to restrict processing scope.
4.  **Chunked Ingestion**: Read only identified lines (+/- 10 lines) using `read_file` to minimize token noise.
5.  **Execution Sequence**: Follow mandatory logic: **Locate** (`grep_search`) -> **Isolate** (context) -> **Validate** (fix).
6.  **Selective Caching**: Explicitly categorize files as "Core Context" (in memory) or "Auxiliary" (on-demand).
7.  **Summarization Rule**: Generate a brief summary of a file's exports and "forget" raw text if only structure matters.
8.  **TTL Awareness**: Treat files with a virtual "Time To Live" to save costs over long sessions.
9.  **Systemic Retrieval**: Prioritize `grep_search` and `glob` before any large codebase ingestion.
10. **Pre-Analysis Requirement**: Inventory the directory before accepting or processing multiple files.

## **II. LOGGING & FORENSIC ARCHITECTURE**
11. **Zero-Cost Gates**: Wrap all granular `trace()` and `debug()` calls in `if LOCAL_DEBUG:` or `if BUILDER_DEBUG:`.
12. **Visual Grepping**: Prefix gated logs with exactly three context-relevant emojis and a bracketed category.
13. **Non-Gated Gravity**: `error()`, `exception()`, and `warning()` must remain outside debug gates.
14. **Directional Observability**: Log all ingress as `📡📥📥 [INBOUND]` and egress as `📡📤📤 [OUTBOUND]`.
15. **Hierarchical Sinks**: Route data to Screen, File, or JSON Lines based on `ENABLE_DEBUG_*` flags.
16. **Subsystem Mapping**: Use domain-specific emojis (e.g., 🚀 `[DEPLOY]`, 📡 `[SENSOR]`, 🎨 `[RENDER]`).
17. **Forensic Integrity**: Ensure all logs provide a trail regardless of local debug state for failures.
18. **JSON Lines Sink**: Utilize a dedicated `.jsonl` sink for structured data ingestion into external systems.
19. **Message Truncation**: Truncate communication log payloads at 100 characters for terminal readability.
20. **Visual Alerts**: Project a "Red Screen of Warning" for critical layout or construction failures.

## **III. ARCHITECTURAL HIERARCHY & BOUNDARIES**
21. **12-Subfolder Standard**: Every `oa*` module must contain: `Core`, `Workers`, `Managers`, `Methods`, `Constants`, `Tests`, `Documentation`, `Assets`, `Interface`, `Hooks`, `FileReaders`, `FileWriters`.
22. **The Root Rule**: No files permitted in the `oa*` directory root except for `Entry.py`.
23. **The Gatekeeper**: `Entry.py` must exist as the module's public API and sole orchestrator.
24. **Dependency Inversion (DIP)**: High-level policy must depend on abstractions, not low-level details.
25. **Layer Isolation**: UI layers prohibited from directly importing Database or low-level infrastructure models.
26. **Circular Dependency Prohibition**: Flag modules that import each other directly or transitively.
27. **Partitioned Architecture**: Respect the split between Core (Logic) and UI (Display) via the `ProtocolRouter`.
28. **Registry Patterns**: Follow established registry and mixin patterns for new widgets or managers.
29. **Encapsulated Module Standard**: Audit all `oa*` modules for under-populated or missing standard folders.
30. **Orchestration Principle**: A top-level manager handles application state and allowable user actions.

## **IV. CODE INTEGRITY & PERFORMANCE**
31. **No Magic Numbers**: Raw numbers must be declared in named variables/constants before use.
32. **Named Arguments**: All function calls must pass variables by name for clarity.
33. **Function Limits**: Functions must perform one task and descend exactly one level of abstraction.
34. **Argument Minimization**: Limit arguments to zero if possible; wrap three or more into a class.
35. **No Flag Arguments**: Prohibit booleans or enums to select function behavior; split the function instead.
36. **Resource Safety**: All file/socket operations must use context managers (`with`) or `finally` blocks.
37. **Anti-Loop Patterns**: Prohibit N+1 queries; never execute `.commit()` or network calls inside loops.
38. **Big-O Awareness**: Use Sets/Dictionaries for $O(1)$ lookups instead of `in` checks on large Lists.
39. **Memory Discipline**: Process large data via generators; never use `.read()` on unknown file sizes.
40. **Concurrency Isolation**: Thread management must be separated from thread-ignorant business logic.

## **V. VALIDATION, DOCUMENTATION & INTERACTION**
41. **F.I.R.S.T. Testing**: All tests must be **F**ast, **I**ndependent, **R**epeatable, **S**elf-Validating, and **T**imely.
42. **Build-Operate-Check**: Structure tests into distinct parts: building data, operating, and checking results.
43. **Surgical Remediation**: Bug fixes must target specific lines; unrelated refactoring is prohibited.
44. **Forensic Logging**: Update `CHANGELOG.md` with timestamped entries for every change.
45. **Mandatory File Header**: Include specific Python headers (FolderName/Filename, Author, Version) in all files.
46. **Versioning Standard**: Use W.X.Y format where W=Date, X=Time (no leading zero), Y=Revision.
47. **Error Acknowledgement**: If corrected by Anthony, state: “Damn, you’re right, Anthony. My apologies.”.
48. **No Message Boxes**: Handle user alerts via console output, not intrusive pop-up message boxes.
49. **Health Reminders**: Remind Anthony to breathe before compilation.
50. **Approval Recognition**: Understand that a “thumbs up” icon signifies user approval (where applicable).

## **VI. CLI-NATIVE ACCELERATION (LINUX)**
51. **Data Reduction Token**: Use `python3 -c` with `pandas` or `json` modules to pre-process large `oaData*` files locally before sharing results.
52. **Fast Context Token**: Use `grep_search` with `--names_only` first to map distribution, then targeted `read_file` for logic.
53. **Log Tail Token**: Use `run_shell_command` with `tail -n 50` or `awk` to isolate specific error timestamps in `oaDataLogs`.
54. **Structure Sync**: Use `python3 UltraFolder.py` immediately when a module is flagged for "Realignment."
55. **Export Protocol**: All structured data from `JSON Lines Sinks` or analysis must be formatted for **Export to Sheets** compatibility.

---
## **VII. RUST NATIVE ACCELERATION (PYO3)**
56. **Native Naming**: All Rust crates must follow the `oa[Name]_rs` naming convention and reside in `oaModuleName/[Core|Methods]/`.
57. **FFI Strategy**: Utilize PyO3 for all high-performance bindings; prefer `maturin develop --release` for JIT compilation.
58. **Loop Inversion**: To eliminate FFI overhead, move high-iteration loops (e.g., coordinate calculation, pixel processing) into Rust. Python hands "Control Parameters" once; Rust executes the loop internally and returns the final batch.
59. **Zero-Copy Mandate**: For high-volume data paths (Audio, Video, Massive JSON), utilize **Zero-Copy Buffers**. Use PyO3 to map Rust slices directly to Python's `numpy` arrays, `memoryviews`, or `bytearrays` to bypass serialization.
60. **Lock-Free Concurrency**: Offload GIL-bound state management to Rust utilizing `DashMap` or atomic primitives.
61. **Safety First**: Use Rust for all critical binary parsing and schema validation to ensure memory safety.

---

To minimize token usage, use this script to handle heavy data processing or file system tasks locally. Instead of uploading large datasets, you will only share the [OUTBOUND] results or specific error traces.

### **LINUX TASK-RUNNER (Python 3)**
```python
# .gemini/TempScripts/tmp_runner.py
# Author: Gemini (Collaborator)
# Version: 20260321.1955.1

import sys, os, json, traceback

def run_task(name, logic_fn):
    print(f"📡📥📥 [INBOUND] Executing Task: {name}")
    try:
        # Create scratchpad in the dedicated TempScripts directory
        temp_dir = f"/home/anthony/Documents/OPEN-AIR/.gemini/TempScripts/{name}"
        os.makedirs(temp_dir, exist_ok=True)
        os.chdir(temp_dir)
...
        result = logic_fn()
        print(f"📡📤📤 [OUTBOUND] Task Complete.")
        return result
    except Exception as e:
        print(f"🛑 [ERROR] Task Failed: {e}")
        with open(f"{temp_dir}/forensic_log.txt", "w") as f:
            f.write(traceback.format_exc())
        return None
```
