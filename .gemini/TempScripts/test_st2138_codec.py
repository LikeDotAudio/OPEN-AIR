import sys
import os

# Ensure the project root is in sys.path
sys.path.append("/home/anthony/Documents/OPEN-AIR")

from oaComSMPTE2138.Methods.st2138_codec import St2138Codec

def test_st2138_codec():
    codec = St2138Codec()
    
    name = "Gain"
    val = 1.0
    
    # Encode
    encoded = codec.encode_param(name, val)
    print(f"Encoded bytes: {encoded.hex()}")
    
    # Decode
    decoded = codec.decode_param(encoded)
    print(f"Decoded dict: {decoded}")
    
    if decoded and decoded['name'] == name:
        print("✅ SUCCESS: ST2138 Param encoded and decoded correctly.")
    else:
        print(f"❌ FAILURE: Decoded data mismatch: {decoded}")

if __name__ == "__main__":
    test_st2138_codec()
