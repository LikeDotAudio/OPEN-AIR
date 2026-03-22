# Audit Result: AuditFileFolderNames
**Timestamp:** 2026-03-22 07:37:59
**Model:** gemini-2.5-flash-lite

## File: AuditFileFolderNames.toml (FAILED)

**Exit Code:** 1

**Error Details:**

```text
[ERROR] [ImportProcessor] Failed to import register_widget: ENOENT: no such file or directory, access '/home/anthony/.gemini/register_widget'
Loaded cached credentials.
[ERROR] [ImportProcessor] Failed to import register_widget: ENOENT: no such file or directory, access '/home/anthony/.gemini/register_widget'
Attempt 1 failed: You have exhausted your capacity on this model. Your quota will reset after 0s.. Retrying after 5285ms...
Attempt 1 failed: You have exhausted your capacity on this model. Your quota will reset after 0s.. Retrying after 5259ms...
Attempt 1 failed: You have exhausted your capacity on this model. Your quota will reset after 0s.. Retrying after 5461ms...
Attempt 1 failed: You have exhausted your capacity on this model. Your quota will reset after 0s.. Retrying after 5656ms...
Attempt 1 failed: You have exhausted your capacity on this model. Your quota will reset after 0s.. Retrying after 5773ms...
AbortError: The user aborted a request.
    at abort (/home/anthony/.nvm/versions/node/v24.11.1/lib/node_modules/@google/gemini-cli/node_modules/node-fetch/lib/index.js:1458:16)
    at AbortSignal.abortAndFinalize (/home/anthony/.nvm/versions/node/v24.11.1/lib/node_modules/@google/gemini-cli/node_modules/node-fetch/lib/index.js:1473:4)
    at [nodejs.internal.kHybridDispatch] (node:internal/event_target:845:20)
    at AbortSignal.dispatchEvent (node:internal/event_target:778:26)
    at runAbort (node:internal/abort_controller:488:10)
    at abortSignal (node:internal/abort_controller:465:5)
    at AbortController.abort (node:internal/abort_controller:507:5)
    at GeminiClient._recoverFromLoop (file:///home/anthony/.nvm/versions/node/v24.11.1/lib/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/client.js:796:28)
    at GeminiClient.processTurn (file:///home/anthony/.nvm/versions/node/v24.11.1/lib/node_modules/@google/gemini-cli/node_modules/@google/gemini-cli-core/dist/src/core/client.js:517:32)
    at process.processTicksAndRejections (node:internal/process/task_queues:103:5)
```

**Partial Output:**

The audit of the `oa*` modules has been completed. Several modules show significant structural debt, with many missing standard subfolders, while others exhibit critical violations such as incorrect module types or root file issues.

Here is the `Structural_Audit.md` report:

# OPEN-AIR Structural Audit Report

## Executive Summary

The OPEN-AIR project exhibits a varied adherence to the "Encapsulated Module" standard. While several modules successfully implement the 12-subfolder hierarchy and `Entry.py` orchestrator, a significant number of modules are missing a substantial portion of these standard subfolders, indicating a high level of "Structural Debt." Critical violations include non-standard module types (e.g., `oaComEmber`), root file violations, and modules entirely lacking the expected subfolder structure.

## Critical Violations

These modules present the most severe deviations from the expected structure and may require significant refactoring.

*   **Non-Standard Module Structure & Root Violations:**
    *   **`oaComEmber`**: This module deviates significantly from the Python `oa*` module standard. It contains C++ or similar compiled language artifacts (CMakeLists.txt, `src` directory) and has missing `Entry.py` at the root. It also has root file violations (`.gitignore`, `CMakeLists.txt`, `CMakePresets.json`, `config.ini`, `README.md`).
        *   *Finding:* Non-Python module structure, missing `Entry.py`, root file violations.
*   **Root Violations (Files other than `Entry.py` or `__init__.py` in module root):**
    *   **`oaDataSNMP`**: Contains `openair_snmp_objects.txt` in the root directory.
        *   *Finding:* `openair_snmp_objects.txt` found in root.
    *   **`oaDocumentation`**: Contains `CodeOfConduct.md` in the root directory.
        *   *Finding:* `CodeOfConduct.md` found in root.
*   **Missing Orchestrator:**
    *   **`oaComEmber`**: Lacks an

---

