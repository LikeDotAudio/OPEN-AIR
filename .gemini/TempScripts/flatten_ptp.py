import os
import shutil

base_dir = "/home/anthony/Documents/OPEN-AIR/oaComProtocols/oaPTP"
folders_to_delete = ["Assets", "Constants", "Core", "Documentation", "FileReaders", "FileWriters", "Hooks", "Interface", "Managers", "Methods", "Tests", "Workers", "__pycache__"]

for sub in folders_to_delete:
    sub_path = os.path.join(base_dir, sub)
    if os.path.exists(sub_path):
        if os.path.isdir(sub_path):
            shutil.rmtree(sub_path)
        else:
            os.remove(sub_path)
        print(f"Deleted {sub_path}")
