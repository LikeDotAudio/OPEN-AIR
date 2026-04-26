
import json
import os

target_dir = "/home/anthony/Documents/OPEN-AIR/oaGui/Assets/Assets/right_50/bottom_90/9_Zoo"
unique_strings = set()

def find_en_strings(data):
    if isinstance(data, dict):
        if "En" in data:
            unique_strings.add(data["En"])
        for key, value in data.items():
            find_en_strings(value)
    elif isinstance(data, list):
        for item in data:
            find_en_strings(item)

for root, dirs, files in os.walk(target_dir):
    for file in files:
        if file.endswith(".json"):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    find_en_strings(data)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

# Output unique strings sorted
sorted_strings = sorted(list(unique_strings))
for s in sorted_strings:
    print(s)
