# .gemini/TempScripts/bench_trie.py
import time
import sys
import os

# Ensure the project root is in sys.path
root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, root)

from oaStateCache.Core.cache_search_engine import CacheSearchEngine, RUST_ENABLED

def run_bench(num_topics=10_000, num_queries=100_000):
    print(f"🚀 [BENCHMARK] Running Trie vs Set comparison...")
    print(f"🦀 Rust Enabled: {RUST_ENABLED}")
    
    # 1. Generate dummy topics
    dummy_topics = {f"oa/System/Subsystem_{i}/Category_{j}/Parameter_{k}": i+j+k 
                    for i in range(10) for j in range(10) for k in range(100)}
    
    engine = CacheSearchEngine()
    
    # 2. Benchmark Rebuild
    start = time.time()
    engine.rebuild(dummy_topics)
    end = time.time()
    print(f"⏱️ Rebuild Time ({len(dummy_topics)} topics): {end - start:.4f}s")
    
    # 3. Benchmark Queries
    queries = [f"oa/System/Subsystem_{i}/" for i in range(10)] * (num_queries // 10)
    
    start = time.time()
    for q in queries:
        engine.exists(q)
    end = time.time()
    
    total_time = end - start
    avg_time = (total_time / num_queries) * 1_000_000
    print(f"⏱️ Query Time ({num_queries} queries): {total_time:.4f}s")
    print(f"⏱️ Avg Time per query: {avg_time:.4f}μs")

if __name__ == "__main__":
    run_bench()
