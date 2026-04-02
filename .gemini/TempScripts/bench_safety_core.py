# .gemini/TempScripts/bench_safety_core.py
import time
import sys
import os

# Ensure the project root is in sys.path
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, root)

from oaOchestration.Methods.json_validator import validate_and_sanitize_json, RUST_ENABLED

def run_bench(iterations=100_000):
    print(f"🚀 [BENCHMARK] Running JSON Validator comparison...")
    print(f"🦀 Rust Enabled: {RUST_ENABLED}")
    
    # Complex nested data structure
    data = {
        "system": "CORE",
        "timestamp": time.time(),
        "metrics": {
            "cpu": [1.2, 3.4, 5.6],
            "memory": {"used": 1024, "free": 2048},
            "active": True
        },
        "tags": ["prod", "master", "v1.0"]
    }
    
    start = time.time()
    for _ in range(iterations):
        validate_and_sanitize_json(data)
    end = time.time()
    
    total_time = end - start
    avg_time = (total_time / iterations) * 1_000_000
    print(f"⏱️ Total Time: {total_time:.4f}s")
    print(f"⏱️ Avg Time per validation: {avg_time:.4f}μs")

if __name__ == "__main__":
    run_bench()
