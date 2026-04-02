# .gemini/TempScripts/bench_logging_gate.py
import time
import sys
import os

# Ensure the project root and module dirs are in sys.path
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, "oaLogging/Methods"))

from oaLogging.Methods.matrix_gate import is_debug_allowed, RUST_ENABLED

# Mock LoggingMatrixManager for Python side
class MockManager:
    @staticmethod
    def get_instance():
        return MockManager()
    def is_debug_allowed(self, s, e, f):
        return True

# Monkey patch for the benchmark if needed
import oaConfiguration.Managers.LoggingManager.manager as m
m.LoggingMatrixManager = MockManager

def run_bench(iterations=1_000_000):
    print(f"🚀 [BENCHMARK] Running {iterations} iterations of is_debug_allowed...")
    print(f"🦀 Rust Enabled: {RUST_ENABLED}")
    
    start = time.time()
    for _ in range(iterations):
        is_debug_allowed("core", "data", "test_func")
    end = time.time()
    
    total_time = end - start
    avg_time = (total_time / iterations) * 1_000_000
    print(f"⏱️ Total Time: {total_time:.4f}s")
    print(f"⏱️ Avg Time per call: {avg_time:.4f}μs")

if __name__ == "__main__":
    run_bench()
