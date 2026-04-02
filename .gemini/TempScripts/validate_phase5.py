# .gemini/TempScripts/validate_phase5.py
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def test_osc_core():
    print("Testing oaosccore_rs...")
    try:
        from oaosccore_rs import OscServer
        server = OscServer()
        print(f"✅ oaosccore_rs imported. Server instance created.")
        print(f"✅ is_running: {server.is_running()}")
    except Exception as e:
        print(f"❌ oaosccore_rs failed: {e}")

def test_visa_scanner():
    print("\nTesting oavisascanner_rs...")
    try:
        from oavisascanner_rs import VisaScanner
        scanner = VisaScanner()
        print(f"✅ oavisascanner_rs imported. Scanner instance created.")
        # Localhost test (might fail if nothing listening, but should return reachable=False)
        res = scanner.check_reachability([("127.0.0.1", 80)], 100)
        print(f"✅ check_reachability call successful. Results count: {len(res)}")
    except Exception as e:
        print(f"❌ oavisascanner_rs failed: {e}")

if __name__ == "__main__":
    test_osc_core()
    test_visa_scanner()
