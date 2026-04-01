import sys
import os
import zipfile
import orjson

# Ensure the project root is in sys.path
sys.path.append("/home/anthony/Documents/OPEN-AIR")

from oaFileImportShow.Methods.showfile_unpacker import ShowfileUnpacker

def test_showfile_unpacker():
    # Create a dummy .show file (actually a zip)
    show_path = ".gemini/test_show.show"
    with zipfile.ZipFile(show_path, 'w') as z:
        z.writestr("manifest.json", orjson.dumps({"version": "1.0", "name": "Test Show"}))
        z.writestr("layout.json", orjson.dumps({"widgets": []}))
        z.writestr("notes.txt", "Plain text note")
    
    data = ShowfileUnpacker.unpack(show_path)
    print(f"Unpacked Data Keys: {list(data.keys())}")
    print(f"Manifest: {data.get('manifest.json')}")
    
    if data.get('manifest.json', {}).get('name') == "Test Show":
        print("✅ SUCCESS: .show file unpacked and JSON parsed.")
    else:
        print(f"❌ FAILURE: Data mismatch or extraction failed: {data}")

if __name__ == "__main__":
    test_showfile_unpacker()
