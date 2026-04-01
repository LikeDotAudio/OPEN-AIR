import sys
import os
import time

# Ensure the project root is in sys.path
sys.path.append("/home/anthony/Documents/OPEN-AIR")

from oaPTP.Methods.ptp_clock import PtpClock

def test_ptp_clock():
    clock = PtpClock()
    
    time.sleep(0.1)
    t1 = clock.get_nanos()
    time.sleep(0.1)
    t2 = clock.get_nanos()
    
    print(f"T1: {t1} ns")
    print(f"T2: {t2} ns")
    print(f"Diff: {t2 - t1} ns")
    
    if t2 > t1:
        print("✅ SUCCESS: PTP Clock is advancing.")
    else:
        print(f"❌ FAILURE: PTP Clock mismatch: {t1}, {t2}")
    
    clock.stop()

if __name__ == "__main__":
    test_ptp_clock()
