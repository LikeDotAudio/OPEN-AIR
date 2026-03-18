# Bad File/Folder Naming & Improper Containerization Audit

**Date**: 2026-03-18  
**Architect**: Gemini Systems Architect  
**Status**: 🔴 POOR ORGANIZATIONAL HEALTH  

## Executive Summary
The project is currently suffering from a "Transition Gap." While the 12-subfolder hierarchy has been established, the actual contents are not properly containerized. 95% of modules violate the **Root Rule** by keeping logic files in the module root. Furthermore, naming conventions are inconsistent, relying heavily on "noise words" and type-encoding rather than intention-revealing names.

---

## 1. Top Offenders: Bad Naming

| File/Folder | Violation | Suggested Refactor |
| :--- | :--- | :--- |
| `oaComsBroker` | **Inconsistency**: The "s" in "Coms" differs from `oaComVisa`, `oaComMidi`. | `oaComBroker` |
| `oaDependancies` | **Misspelling**: Common spelling error. | `oaDependencies` |
| `oaIntstallation` | **Misspelling**: Common spelling error. | `oaInstallation` |
| `*_utils.py`, `*_util.py` | **Noise Word**: "Util" is a meaningless distinction. | Rename based on specific function (e.g., `topic_calculator.py`). |
| `*_mixin.py` | **Encoding**: Encoding the implementation pattern (Mixin) in the name. | Focus on the capability (e.g., `InteractionHandler.py`). |
| `*_logic.py` | **Noise Word**: Everything is "logic." | Identify the specific domain (e.g., `visa_handshake.py`). |
| `oaUnitTests` | **Dead Reference**: Folder was deleted but references might remain. | Verify and remove all import references. |

---

## 2. Improper Containerization (Artificial Coupling & Scatters)

### The "Root File" Plague
Almost every `oa*` module has its primary logic files sitting in the root instead of the standardized subfolders. This breaks the **Encapsulated Module** standard.
- **Offender**: `oaComMQTT` has 12+ files at its root (e.g., `mqtt_connection.py`, `mqtt_message.py`).
- **Offender**: `oaTranslator` has 10+ `yak_*` files at its root.
- **Offender**: `oaConfiguration` has all its core logic (`config_reader.py`, etc.) at the root.

### Abstraction Level Mixing
- **oaGuiManager**: Contains `open_air_ui.py` at the root, mixing high-level UI policy with low-level telemetry in subdirectories.
- **oaOchestration**: Mixes path initialization (`project_paths.py`) with complex application bootstrapping at the root level.

### "Alike" File Scatters
- **GUI Definitions**: `oaGuiDefinitions` contains a massive flat list of `yak_*.json` and `Connection_*.json` files. These should be sub-grouped by device type or function.

---

## 3. Specific Refactoring Recommendations

1.  **Enforce the Root Rule**: Move all `.py` files in the root of `oa*` modules into `Core/`, `Managers/`, or `Workers/` as per the `UltraFolder` execution strategy.
2.  **Rename Noise Modules**:
    - `oaComMQTT/mqtt_topic_utils.py` ➡️ `oaComMQTT/Methods/topic_formatter.py`
    - `oaComSNMP/snmp_utils.py` ➡️ `oaComSNMP/Methods/snmp_helpers.py`
3.  **Group GUI Definitions**: Create subdirectories in `oaGuiDefinitions` for `Yak/`, `Agilent/`, `Connection_Dialogs/`, etc.
4.  **Fix Core Spelling**: Rename `oaDependancies` and `oaIntstallation` immediately to prevent import confusion.
5.  **Bootstrap Entry.py**: Every module needs an `Entry.py` to hide its internal folder structure from the supervisor.

## Conclusion
The current naming and containerization are creating high cognitive load for developers. Navigating the `oa*` modules is difficult because the root is cluttered and names do not reveal intention. Priority should be given to cleaning the module roots and fixing the misspelled foundational modules.
