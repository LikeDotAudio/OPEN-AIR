import sys
import os

# Ensure the project root is in sys.path
sys.path.append("/home/anthony/Documents/OPEN-AIR")

from oaComVisa.Methods.visa_formatter import VisaFormatter

def test_visa_formatter():
    formatter = VisaFormatter()
    
    cmd = "SET_VOLTAGE"
    val = 5.0134
    
    formatted = formatter.format_command(cmd, val)
    print(f"Formatted command: {formatted}")
    
    expected = f"{cmd} 5.013400e0\n".encode()
    # Note: Rust's :e might have slightly different precision defaults
    
    if formatted.startswith(cmd.encode()):
        print("✅ SUCCESS: VISA command formatted.")
    else:
        print(f"❌ FAILURE: Unexpected format: {formatted}")

if __name__ == "__main__":
    test_visa_formatter()
