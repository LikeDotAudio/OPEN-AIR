# OPEN-AIR Module Audit Report: Entry.py Compliance

**Date:** 2026-03-24

This report details the audit of OPEN-AIR modules for adherence to the 'Entry.py' Based Design standard, focusing on the presence of `Entry.py`, the mandatory 12 subfolders, and the prohibition of logic in `__init__.py` files or unauthorized root files.

## **I. Green Modules (Fully Compliant):**
The following modules adhere to all aspects of the 'Entry.py' standard:
- `oaComBroker`
- `oaComMidi`
- `oaComMQTT`
- `oaComOSC`
- `oaComSNMP`
- `oaFileExportCSV`
- `oaFileImportCSV`
- `oaFileImportHTML`
- `oaFileImportPDF`
- `oaFileImportShow`
- `oaGuiBackground`
- `oaGuiBuilder`
- `oaGuiBuildShell`
- `oaGuiDefinitions`
- `oaGuiEditorWYSIWYG`
- `oaGuiElements`
- `oaGuiFolderParser`
- `oaGuiManager`
- `oaGuiMediaElements`
- `oaGuiShowtime`
- `oaGuiSplashScreen`
- `oaGuiTelemetry`
- `oaInstallation`
- `oaLogging`
- `oaOchestration`
- `oaPTP`
- `oaSplinker`
- `oaStand_Alone_Utilities`
- `oaStateCache`
- `oaStyle`
- `oaThreadManager`
- `oaTranslator`
- `oaWatchdog`

## **II. Structural Violations:**
Modules that deviate from the required directory structure or file presence.

### **A. Missing `Entry.py`:**
- `oaDataAudits`
- `oaDataCache`
- `oaDataLogs`
- `oaReports`

### **B. Missing 12 Standard Subfolders:**
- `oaDataAudits` (Missing all)
- `oaDataCache` (Missing most)
- `oaDataLogs` (Missing most)
- `oaReports` (Missing all)

### **C. Unauthorized Files in Root:**
- `oaComEmber`: `.gitignore`, `CMakeLists.txt`, `CMakePresets.json`, `config.ini`, `README.md`
- `oaConfiguration`: `installation_log.txt`
- `oaDataAudits`: All `.md` files (e.g., `Audit_Entry_Packages_20260324.md`)
- `oaDataCache`: `device_state_cache.json`, `layout_cache.json`
- `oaDataLogs`: (No direct files, but subfolders are non-standard)
- `oaDataSNMP`: `openair_snmp_objects.txt`
- `oaReports`: All `.html`, `.json` files (e.g., `UnifiedReport_20260324095207.html`)

### **D. Non-Standard or Redundant Subfolders:**
- `oaComEmber`: `include`, `logs`, `src`, `subprojects`. Also has a potentially redundant `tests` folder alongside the standard `Tests`.
- `oaComSNMP`: `MIB`, `pass_scripts`.
- `oaDocumentation`: `BugLog`, `ChangeLog`, `FlameTesting`, `Landmarks`, `Manual`, `Project_Map`.
- `oaDataLogs`: Subfolders `ApplicationRunLog`, `Errors`, `FlameGraph`, `JsonLines` are not standard top-level folders.

### **E. Missing Specific Standard Subfolders:**
- `oaComAES70`: Missing 'Tests'.
- `oaComVisa`: Missing 'FileReaders'.
- `oaDocumentation`: Missing 'Methods', 'Tests'.
- `oaTests`: Missing 'Tests' (ironic, given module name).

## **III. Logic Leaks (Root `__init__.py` Files):**
No `__init__.py` files were found to contain logic or imports. All scanned `__init__.py` files contained only metadata, adhering to the standard.

## **IV. Clean Entry Proposals:**
Recommendations for refactoring modules with structural violations to align with the 'Entry.py' standard.

### **A. Module: `oaComEmber`**
- **Action**: Move unauthorized root files (`.gitignore`, `CMakeLists.txt`, `CMakePresets.json`, `config.ini`, `README.md`) to an appropriate location (e.g., a `build/` or `config/` subfolder within the module, or the project root if global).
- **Action**: Reorganize or remove non-standard subfolders (`include`, `logs`, `src`, `subprojects`) and consolidate their contents into standard 12 subfolders.
- **Action**: Address the `tests` vs. `Tests` folder by consolidating into the standard `Tests` folder.

### **B. Module: `oaComAES70`**
- **Action**: Create a `Tests` subfolder.

### **C. Module: `oaComVisa`**
- **Action**: Create a `FileReaders` subfolder.

### **D. Module: `oaConfiguration`**
- **Action**: Move `installation_log.txt` to an appropriate subfolder (e.g., `Documentation/InstallationLogs`).

### **E. Module: `oaDataAudits`**
- **Action**: Create an `Entry.py` file.
- **Action**: Create all 12 standard subfolders (`Core`, `Workers`, `Managers`, `Methods`, `Constants`, `Tests`, `Documentation`, `Assets`, `Interface`, `Hooks`, `FileReaders`, `FileWriters`).
- **Action**: Move all `.md` files to the `Documentation` subfolder.

### **F. Module: `oaDataCache`**
- **Action**: Create an `Entry.py` file.
- **Action**: Ensure all 12 standard subfolders are present and populated correctly.
- **Action**: Move `device_state_cache.json` and `layout_cache.json` to the `Assets` subfolder.

### **G. Module: `oaDataLogs`**
- **Action**: Create an `Entry.py` file.
- **Action**: Create all 12 standard subfolders.
- **Action**: Refactor the contents of `ApplicationRunLog`, `Errors`, `FlameGraph`, `JsonLines` into appropriate standard subfolders like `Documentation` or `Assets`.

### **H. Module: `oaDataSNMP`**
- **Action**: Move `openair_snmp_objects.txt` to an appropriate subfolder (e.g., `Assets`).
- **Action**: Reorganize `MIB` and `pass_scripts` into standard subfolders if they contain core logic, methods, or assets.

### **I. Module: `oaDocumentation`**
- **Action**: Move non-standard subfolders (`BugLog`, `ChangeLog`, `FlameTesting`, `Landmarks`, `Manual`, `Project_Map`) into the `Documentation` folder or refactor their content into the standard `Documentation` structure.
- **Action**: Create a `Methods` subfolder.
- **Action**: Create a `Tests` subfolder.

### **J. Module: `oaReports`**
- **Action**: Create an `Entry.py` file.
- **Action**: Create all 12 standard subfolders.
- **Action**: Move all `.html` and `.json` files to the `Assets` subfolder.

### **K. Module: `oaTests`**
- **Action**: Create a `Tests` subfolder.
