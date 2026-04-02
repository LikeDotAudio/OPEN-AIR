# .gemini/TempScripts/bench_log_processor.py
import time
import sys
import os

# Ensure the project root is in sys.path
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, root)

from oaTests.FileWriters.ReportBuilder_RunLog import build_tab, RUST_ENABLED

def run_bench():
    print(f"🚀 [BENCHMARK] Running Log Processor comparison...")
    print(f"🦀 Rust Enabled: {RUST_ENABLED}")
    
    log_dir = os.path.join(root, "oaDataLogs", "ApplicationRunLog")
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a large dummy log file if it doesn't exist
    dummy_log = os.path.join(log_dir, "Application_BENCHMARK.log")
    if not os.path.exists(dummy_log):
        with open(dummy_log, "w") as f:
            for i in range(5000):
                f.write(f"2026-04-01 23:30:00.000 | INFO | CORE | SYSTEM | main | Dummy log message number {i}\n")
    
    start = time.time()
    html_output = build_tab(log_dir)
    end = time.time()
    
    print(f"⏱️ Total processing time: {end - start:.4f}s")
    print(f"📊 Output size: {len(html_output) / 1024:.2f} KB")

if __name__ == "__main__":
    run_bench()
