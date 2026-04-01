import struct
import sys
import os

# Ensure the project root is in sys.path
sys.path.append("/home/anthony/Documents/OPEN-AIR")

from oaComAES70.Methods.aes70_parser import OcaParser

def test_aes70_parser():
    # Construct a valid OCP.1 PDU
    # Header: Version=1, PDU Size=24, Msg Count=1
    header = struct.pack(">H I H", 1, 24, 1)
    # Message: Size=16, Handle=10, Target ONo=1, Method ID=5 (No params)
    msg = struct.pack(">I I I I", 16, 10, 1, 5)
    
    pdu = header + msg
    
    parser = OcaParser()
    result = parser.decode(pdu)
    
    print(f"PDU: {pdu.hex()}")
    print(f"Result: {result}")
    
    if result and result['version'] == 1 and result['message_count'] == 1:
        print("✅ SUCCESS: OCP.1 PDU correctly decoded.")
        msg0 = result['messages'][0]
        if msg0['handle'] == 10 and msg0['target_ono'] == 1 and msg0['method_id'] == 5:
            print("✅ SUCCESS: Message contents match.")
        else:
            print("❌ FAILURE: Message contents mismatch.")
    else:
        print("❌ FAILURE: PDU decoding failed.")

    # Test with parameters
    # Header: Version=1, PDU Size=32, Msg Count=1
    header = struct.pack(">H I H", 1, 32, 1)
    # Message: Size=24, Handle=11, Target ONo=2, Method ID=6, Params=0xDEADBEEFCAFEBABE
    params = bytes.fromhex("DEADBEEFCAFEBABE")
    msg = struct.pack(">I I I I", 24, 11, 2, 6) + params
    
    pdu = header + msg
    result = parser.decode(pdu)
    print(f"PDU with params: {pdu.hex()}")
    print(f"Result: {result}")
    
    if result and result['messages'][0]['parameters'] == params:
        print("✅ SUCCESS: Parameters correctly extracted.")
    else:
        print("❌ FAILURE: Parameters mismatch.")

if __name__ == "__main__":
    test_aes70_parser()
