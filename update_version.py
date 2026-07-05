import os

# Read the list of files
with open("js_files_clean.txt", "r") as f:
    files = [line.strip() for line in f if line.strip()]

count = 0
for file_path in files:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if "Version: 1.0.0" in content:
            new_content = content.replace("Version: 1.0.0", "Version: 26.07.05.1")
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            count += 1
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

print(f"Updated version in {count} files.")
