import sys
import os

# Ensure the project root is in sys.path
sys.path.append("/home/anthony/Documents/OPEN-AIR")

from oaComEmber.Methods.ember_parser import EmberParser

def test_ember_parser():
    # Construct a simple BER TLV
    # Sequence (0x30 = Constructed, Class=Universal, Tag=16)
    # Length 3
    #   Integer (0x02 = Primitive, Class=Universal, Tag=2)
    #   Length 1
    #   Value 5
    data = bytes.fromhex("3003020105")
    
    parser = EmberParser()
    result = parser.parse_ber_payload(data)
    
    print(f"Data: {data.hex()}")
    print(f"Result: {result}")
    
    if result and result['tag'] == 16 and result['is_constructed']:
        print("✅ SUCCESS: BER Sequence decoded.")
        child = result['value'][0]
        if child['tag'] == 2 and child['value'] == b'\x05':
            print("✅ SUCCESS: Child integer decoded.")
        else:
            print(f"❌ FAILURE: Child mismatch: {child}")
    else:
        print(f"❌ FAILURE: Sequence decoding failed: {result}")

if __name__ == "__main__":
    test_ember_parser()
