import os
import shutil
from pathlib import Path

elements = [
    "Core/break_line",
    "Core/breakoff",
    "Core/input/checkbox",
    "Core/special/circular_motion_displacement_potentiometer",
    "Core/input/composite_horizontal_dial_value",
    "Core/special/composite_mdp",
    "Core/input/json_tree",
    "Core/Knobs/knob",
    "Core/Knobs/knob_rotary_selector",
    "Core/input/listbox",
    "Core/special/midi_keyboard",
    "Core/panels",
    "Core/panels/panel_screw",
    "Core/input/slider_value",
    "Core/special/status_light"
]

base_path = Path("/home/anthony/Documents/OPEN-AIR/oaGuiElements")

subfolders = ["Core", "Workers", "Managers", "Methods", "Constants", "Tests", "Documentation", "Assets", "Interface", "Hooks", "FileReaders", "FileWriters"]

for rel_path in elements:
    elem_root = base_path / rel_path
    if not elem_root.exists():
        print(f"Skipping {rel_path}, does not exist.")
        continue

    print(f"Processing {rel_path}...")

    # Create 12 subfolders
    for sub in subfolders:
        (elem_root / sub).mkdir(parents=True, exist_ok=True)

    # Check for redundant nested folder
    name = elem_root.name
    nested = elem_root / name
    if nested.exists() and nested.is_dir():
        print(f"  Found nested folder {name}, moving contents up...")
        for item in nested.iterdir():
            dest = elem_root / item.name
            if dest.exists():
                if dest.is_dir():
                    # Merge directories
                    for subitem in item.rglob('*'):
                        if subitem.is_file():
                            rel_subitem = subitem.relative_to(item)
                            final_dest = dest / rel_subitem
                            final_dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(subitem), str(final_dest))
                else:
                    # File exists, skip or overwrite? Let's skip if they are likely same
                    print(f"  File {item.name} already exists at root, skipping move from nested.")
            else:
                shutil.move(str(item), str(elem_root))
        shutil.rmtree(nested)

    # Move files from root to appropriate subfolders
    for item in elem_root.iterdir():
        if item.is_file():
            if item.name == "Entry.py":
                continue
            if item.name == "__init__.py":
                # item.unlink() # Keep or remove? Let's remove if we are using Entry.py
                os.remove(item)
                continue
            
            if item.suffix == ".py":
                shutil.move(str(item), str(elem_root / "Core" / item.name))
            elif item.suffix in [".json", ".png", ".jpg", ".svg"]:
                shutil.move(str(item), str(elem_root / "Assets" / item.name))
            elif item.suffix == ".md":
                shutil.move(str(item), str(elem_root / "Documentation" / item.name))

print("Cleanup complete.")
