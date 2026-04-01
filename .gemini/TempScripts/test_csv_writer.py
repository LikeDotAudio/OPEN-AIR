import sys
import os
import time

# Ensure the project root is in sys.path
sys.path.append("/home/anthony/Documents/OPEN-AIR")

from oaFileExportCSV.Methods.csv_writer import CSVWriter

def test_csv_writer():
    data = [
        {"timestamp": time.time(), "event": "System Boot", "level": "INFO"},
        {"timestamp": time.time(), "event": "Module Load", "level": "DEBUG"},
        {"timestamp": time.time(), "event": "Error Detected", "level": "ERROR"},
    ]
    
    csv_path = ".gemini/tmp_test_export.csv"
    if os.path.exists(csv_path): os.remove(csv_path)
    
    CSVWriter.dump_async(data, csv_path)
    print("Requested async CSV dump.")
    
    # Wait a bit for the async write
    time.sleep(0.5)
    
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            content = f.read()
            print(f"File content:\n{content}")
        print("✅ SUCCESS: CSV exported asynchronously.")
    else:
        print("❌ FAILURE: CSV file not created.")

if __name__ == "__main__":
    test_csv_writer()
