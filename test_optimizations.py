#!/usr/bin/env python3
"""
Test optimized vs non-optimized benchmarks
"""

import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from scripts.benchmarks import CouchdbBenchmark
from scripts.benchmarks.couchdb_benchmark_optimized import CouchdbBenchmarkOptimized

# Test data
TEST_CODIGOS = [str(i) for i in range(374000, 374050)]  # 50 códigos

def test_couchdb_comparison():
    """Compare original vs optimized CouchDB"""
    config = {
        'host': 'localhost',
        'port': 5984,
        'database': 'benchmark_test_opt',
        'user': 'benchmark',
        'password': 'benchmark123'
    }
    
    print("=== CouchDB Optimization Test ===")
    
    # Test original
    print("\n1. Testing ORIGINAL CouchDB implementation...")
    original = CouchdbBenchmark(config)
    original.connect()
    
    # Insert some test data
    test_data = [
        {
            'codigo': code,
            'titulo': f'Test {code}',
            'cliente': f'Cliente Test {code}',
            'descricao': 'Test description' * 10
        }
        for code in TEST_CODIGOS
    ]
    
    original.setup_schema()
    original.insert_batch(test_data)
    
    # Test query performance
    start = time.time()
    results, query_time = original.query_by_codigo(TEST_CODIGOS[:20])
    original_time = time.time() - start
    print(f"   Original query time: {original_time:.3f}s for 20 queries")
    
    original.teardown()
    original.disconnect()
    
    # Test optimized
    print("\n2. Testing OPTIMIZED CouchDB implementation...")
    optimized = CouchdbBenchmarkOptimized(config)
    optimized.connect()
    optimized.setup_schema()
    optimized.insert_batch(test_data)
    
    # Test query performance
    start = time.time()
    results, query_time = optimized.query_by_codigo(TEST_CODIGOS[:20])
    optimized_time = time.time() - start
    print(f"   Optimized query time: {optimized_time:.3f}s for 20 queries")
    
    # Calculate improvement
    improvement = original_time / optimized_time
    print(f"\n✨ Performance improvement: {improvement:.1f}x faster!")
    
    optimized.teardown()
    optimized.disconnect()


def quick_optimizations_summary():
    """Print quick optimization tips"""
    print("\n" + "="*60)
    print("🚀 QUICK OPTIMIZATION TIPS")
    print("="*60)
    
    tips = {
        "CouchDB": [
            "1. Use batch queries with POST to views",
            "2. Enable Mango queries instead of MapReduce",
            "3. Increase cache: COUCHDB_CACHE_SIZE=2GB",
            "4. Use the optimized implementation"
        ],
        "PostgreSQL": [
            "1. Already fast! But can add connection pooling",
            "2. Run ANALYZE after bulk inserts",
            "3. Increase shared_buffers to 512MB"
        ],
        "MongoDB": [
            "1. Use projections to exclude large fields",
            "2. Increase WiredTiger cache to 2GB",
            "3. Use aggregation pipelines for complex queries"
        ],
        "Cassandra": [
            "1. Use execute_concurrent for parallel queries",
            "2. Prepare statements once and reuse",
            "3. Increase batch size to 50-100 for ScyllaDB"
        ],
        "ScyllaDB": [
            "1. Same as Cassandra but can handle larger batches",
            "2. Use shard-aware drivers",
            "3. Increase SMP threads: --smp 4"
        ]
    }
    
    for db, optimizations in tips.items():
        print(f"\n{db}:")
        for opt in optimizations:
            print(f"  {opt}")


if __name__ == "__main__":
    print("Testing optimizations...\n")
    
    try:
        test_couchdb_comparison()
    except Exception as e:
        print(f"CouchDB test failed: {e}")
    
    quick_optimizations_summary()
    
    print("\n💡 To use optimized versions in benchmarks:")
    print("   1. Update benchmark_runner.py to import optimized classes")
    print("   2. Or apply the optimizations directly to the original files")
    print("   3. Update docker-compose.yml with performance settings") 