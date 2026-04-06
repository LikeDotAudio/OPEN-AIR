import os
import json
import pathlib

# Keys that strictly require language nesting
TARGET_KEYS = {
    "label", 
    "description", 
    "label_active", 
    "label_inactive", 
    "text", 
    "hover_text"
}

def migrate_to_language_support(data):
    """
    Recursively updates dictionary keys to support multi-language objects.
    Targets labels, descriptions, and button text specifically.
    Adds 'En' and 'Fr' (placeholder) keys.
    """
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            if key in TARGET_KEYS and isinstance(value, str):
                # Wrap string values in {"En": value, "Fr": ""} structure
                new_dict[key] = {"En": value, "Fr": ""}
            else:
                # Recurse deeper into the structure for nested dicts/lists
                new_dict[key] = migrate_to_language_support(value)
        return new_dict
    
    elif isinstance(data, list):
        # If it's a list, apply migration to each item
        return [migrate_to_language_support(item) for item in data]
    
    else:
        # Return primitive values (integers, booleans, hardware paths, etc.) as-is
        return data

def process_file(file_path):
    """Reads a JSON file, migrates its content, and writes it back."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {file_path}: {e}")
                return False
        
        updated_data = migrate_to_language_support(data)
        
        # Only write back if changes were made (or if the structure inherently changes)
        # Simple check: if the top level is a dict and it was modified.
        if isinstance(data, dict) and isinstance(updated_data, dict) and data != updated_data:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(updated_data, f, indent=2)
            print(f"Migrated: {file_path}")
            return True
        else:
            # print(f"Skipped (no change detected or not a dict): {file_path}")
            return False
            
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return False

def main():
    """
    Main function to find and migrate all JSON files in oaGuiDefinitions.
    """
    # Corrected project_root calculation: path to OPEN-AIR directory
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent # OPEN-AIR is 3 levels up from .gemini/TempScripts
    gui_definitions_path = project_root / "oaGuiDefinitions"
    
    if not gui_definitions_path.is_dir():
        print(f"Error: GUI definitions path not found: {gui_definitions_path}")
        return

    migrated_count = 0
    # Recursively find all .json files
    for file_path in gui_definitions_path.rglob("*.json"):
        if process_file(file_path):
            migrated_count += 1
            
    print("--- Migration Complete ---")
    print(f"Total files processed: {migrated_count}")
    print(f"Files migrated: {migrated_count}")

if __name__ == "__main__":
    main()
