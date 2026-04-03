
import sys
import os
import time
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "oaSplinker/Core/oaSplinkRegistry_rs"))

from oaSplinker.Core.oaSplinkRegistry_rs.compiler_hook import ensure_compiled
ensure_compiled()
import oasplinkregistry_rs
from oasplinkregistry_rs import SplinkRegistry

def test_splink_registry_float_ts():
    print("Testing SplinkRegistry.mark_event_processed with float timestamp...")
    registry = SplinkRegistry()
    
    # msg["ts"] is time.time() which is a float
    ts = time.time()
    topic = "test/topic"
    splink_id = "test_id"
    
    print(f"Calling mark_event_processed with ts={ts} (type={type(ts)})")
    try:
        result = registry.mark_event_processed(ts, topic, splink_id)
        print(f"Result: {result}")
        print("✅ SUCCESS: Handled float.")
    except TypeError as e:
        print(f"Caught expected TypeError: {e}")
    except Exception as e:
        print(f"❌ FAILED with unexpected exception: {e}")

if __name__ == "__main__":
    test_splink_registry_float_ts()
