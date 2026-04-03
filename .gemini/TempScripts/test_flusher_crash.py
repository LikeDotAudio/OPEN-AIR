
import sys
import os
import time
sys.path.append(os.getcwd())
# The DiskFlusher is in oaStateCache/Core/oaDiskFlusher_rs
sys.path.append(os.path.join(os.getcwd(), "oaStateCache/Core/oaDiskFlusher_rs"))

from oaStateCache.Core.oaDiskFlusher_rs.compiler_hook import ensure_compiled
try:
    # We might need to build it first
    import oadiskflusher_rs
    from oadiskflusher_rs import DiskFlusher
except ImportError:
    print("DiskFlusher not found, trying to build...")
    # This is a bit complex to do here, but let's assume it's there or we can find it.
    pass

def test_disk_flusher_crash():
    print("Testing DiskFlusher with self-referencing dictionary...")
    try:
        flusher = DiskFlusher()
        
        d = {"a": 1}
        d["self"] = d
        
        print("Calling flush_async with recursive dict...")
        # This SHOULD crash with Code -11 if my theory is right
        flusher.flush_async(d, "test_cache.json")
        print("Success? (Didn't crash)")
    except NameError:
        print("DiskFlusher not available for test.")
    except Exception as e:
        print(f"Caught exception: {e}")

if __name__ == "__main__":
    test_disk_flusher_crash()
