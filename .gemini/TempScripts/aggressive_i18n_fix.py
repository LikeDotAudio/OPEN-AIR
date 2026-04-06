import os
import re
import pathlib

TARGET_KEYS = [
    "label", 
    "description", 
    "label_active", 
    "label_inactive", 
    "text", 
    "hover_text"
]

def process_file(filepath):
    if not os.path.exists(filepath):
        return

    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content

    # 1. Add import if translatable keys are accessed but import is missing
    has_keys = any(key in content for key in TARGET_KEYS)
    import_stmt = "from oaGuiFramework.Methods.i18n_utils import get_text"
    if has_keys and import_stmt not in content:
        # Insert after existing imports
        lines = content.splitlines()
        inserted = False
        for i, line in enumerate(lines):
            if line.startswith("from oaGui") or line.startswith("import "):
                continue
            elif i > 0:
                lines.insert(i, import_stmt)
                inserted = True
                break
        if not inserted:
            lines.insert(0, import_stmt)
        content = "\n".join(lines)

    # 2. Aggressive Regex Replacements
    for key in TARGET_KEYS:
        # config.get("key") -> get_text(config.get("key"))
        # (avoiding double wrapping)
        pattern = rf'(?<!get_text\()config(?:_data)?\.get\([\"\']{key}[\"\']\)'
        content = re.sub(pattern, rf'get_text(config.get("{key}"))', content)

        # config.get("key", "default") -> get_text(config.get("key"), "default")
        pattern = rf'(?<!get_text\()config(?:_data)?\.get\([\"\']{key}[\"\'],\s*([\"\'].*?[\"\']|[^)]+)\)'
        content = re.sub(pattern, rf'get_text(config.get("{key}"), \1)', content)

        # config["key"] -> get_text(config["key"])
        pattern = rf'(?<!get_text\()config(?:_data)?\[[\"\']{key}[\"\']\]'
        content = re.sub(pattern, rf'get_text(config["{key}"])', content)

    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Processed: {filepath}")

def main():
    search_dirs = ["oaGuiFramework/Core", "oaGuiFramework/Managers"]
    for root_dir in search_dirs:
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.endswith(".py"):
                    process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
