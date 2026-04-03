
import sys
import os
sys.path.append(os.getcwd())

from oaComBroker.Methods.oaCoreRouter_rs.compiler_hook import ensure_compiled
ensure_compiled()
from oacorerouter_rs import CoreRouter

def test_rust_router_none():
    print("Testing Rust CoreRouter with None value in dictionary...")
    router = CoreRouter()
    
    msg = {
        "topic": "test/topic",
        "val": None,
        "meta": {}
    }
    
    print(f"Pushing message: {msg}")
    try:
        router.push_inbound(msg)
        print("Push inbound success.")
        
        recv = router.pop_inbound()
        print(f"Pop inbound result: {recv}")
        
        assert recv == msg
        print("✅ SUCCESS: Rust router handled dictionary with None correctly.")
    except Exception as e:
        print(f"❌ FAILED: {e}")

if __name__ == "__main__":
    test_rust_router_none()
