#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# FolderName/structural_audit.py
# Author: Gemini CLI
# Version: 20260412.1200.1
#
# Description: Structural Architect: Deep Audit of oa* modules into the 12-folder Encapsulated Module standard.

STANDARD_SUBFOLDERS = [
    "Core", "Workers", "Managers", "Methods", "Constants", 
    "Tests", "Documentation", "Assets", "Interface", 
    "Hooks", "FileReaders", "FileWriters"
]

MANDATORY_ROOT_FILES = ["Entry.py"]
FORBIDDEN_ROOT_FILES = ["__init__.py"] # Though some modules have it, the mandate says NO files except Entry.py

def audit_module(module_path: Path):
    errors = []
    
    # 1. Check for standard subfolders
    for subfolder in STANDARD_SUBFOLDERS:
        if not (module_path / subfolder).is_dir():
            errors.append(f"Missing standard subfolder: {subfolder}")
            
    # 2. Check for Entry.py
    if not (module_path / "Entry.py").is_file():
        errors.append("Missing Entry.py gatekeeper")
        
    # 3. Check for unauthorized files in root
    root_files = [f for f in module_path.iterdir() if f.is_file()]
    for f in root_files:
        if f.name not in MANDATORY_ROOT_FILES:
            # We allow .gitignore or other hidden files if they exist, but GEMINI.md is strict.
            if not f.name.startswith('.'):
                errors.append(f"Unauthorized file in module root: {f.name}")
                
    return errors

def main():
    project_root = Path(__file__).parent.parent.parent
    oa_modules = [d for d in project_root.iterdir() if d.is_dir() and d.name.startswith("oa")]
    
    # Exclude Vaults as per UltraFolder.toml (they are flat)
    VAULTS = ["oaGuiDefinitions", "oaDataRunningFiles", "oaDataLogs", "oaDataCache", "oaDataSplinks", "oaDataTests"]
    
    # Filter out vaults and nested modules (like oaComProtocols.oaComVisa - wait, those are subdirs)
    # The session context shows oaComProtocols contains sub-modules.
    
    all_errors = {}
    
    modules_to_check = []
    for mod in oa_modules:
        if mod.name in VAULTS:
            continue
        
        # Special handling for oaComProtocols which contains nested oa* modules
        if mod.name == "oaComProtocols":
            for submod in mod.iterdir():
                if submod.is_dir() and submod.name.startswith("oa"):
                    modules_to_check.append(submod)
        else:
            modules_to_check.append(mod)

    for module in modules_to_check:
        errors = audit_module(module)
        if errors:
            all_errors[str(module.relative_to(project_root))] = errors

    if all_errors:
        print("❌ [AUDIT FAILURE] Structural inconsistencies found:")
        for mod, errors in all_errors.items():
            print(f"\nModule: {mod}")
            for err in errors:
                print(f"  - {err}")
        sys.exit(1)
    else:
        print("✅ [AUDIT SUCCESS] All modules adhere to the 12-folder standard.")
        sys.exit(0)

if __name__ == "__main__":
    main()
