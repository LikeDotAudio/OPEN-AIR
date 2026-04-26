# .gemini/TempScripts/audit_folders.py
import os

STANDARD_FOLDERS = [
    "Core", "Workers", "Managers", "Methods", "Constants", "Tests",
    "Documentation", "Assets", "Interface", "Hooks", "FileReaders", "FileWriters"
]

VAULTS = [
    "oaGuiDefinitions", "oaDataRunningFiles", "oaDataLogs",
    "oaDataCache", "oaDataSplinks", "oaDataTests"
]

def audit_modules():
    modules = [d for d in os.listdir('.') if os.path.isdir(d) and d.startswith('oa') and d not in VAULTS]
    report = {}

    for mod in modules:
        mod_path = os.path.join(os.getcwd(), mod)
        contents = os.listdir(mod_path)

        missing_folders = [f for f in STANDARD_FOLDERS if f not in contents or not os.path.isdir(os.path.join(mod_path, f))]
        has_entry = "Entry.py" in contents
        root_files = [f for f in contents if os.path.isfile(os.path.join(mod_path, f)) and f != "Entry.py" and f != "__init__.py" and not f.startswith('.')]

        report[mod] = {
            "missing_folders": missing_folders,
            "has_entry": has_entry,
            "root_files": root_files
        }
    return report

if __name__ == "__main__":
    import json
    print(json.dumps(audit_modules(), indent=2))
