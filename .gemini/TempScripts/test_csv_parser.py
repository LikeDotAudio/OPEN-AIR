import sys
import os

# Ensure the project root is in sys.path
sys.path.append("/home/anthony/Documents/OPEN-AIR")

from oaFileImportCSV.Methods.csv_parser import CSVParser

def test_csv_parser():
    # Create a dummy CSV
    csv_content = "ZONE,GROUP,DEVICE,NAME,FREQ_MHZ,PEAK\nZone1,Group1,Dev1,Mic1,600 MHz, -10\n"
    csv_path = ".gemini/tmp_test.csv"
    with open(csv_path, "w") as f:
        f.write(csv_content)
    
    # Test convert_csv_unknown
    headers, data = CSVParser.convert_csv_unknown(csv_path)
    print(f"Headers: {headers}")
    print(f"Data: {data}")
    
    if len(data) > 0 and data[0]['FREQ_MHZ'] == 600.0:
        print("✅ SUCCESS: CSV parsed with frequency conversion.")
    else:
        print(f"❌ FAILURE: CSV parsing mismatch: {data}")

    # Test load_large_csv (Polars)
    data_large = CSVParser.load_large_csv(csv_path)
    print(f"Large Data (Polars): {data_large}")
    if len(data_large) > 0:
        print("✅ SUCCESS: Large CSV loaded via Polars.")
    else:
        print("❌ FAILURE: Large CSV loading failed.")

if __name__ == "__main__":
    test_csv_parser()
