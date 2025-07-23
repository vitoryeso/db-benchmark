#!/usr/bin/env python3
"""
Benchmark Runner - Main orchestrator for database benchmarks
"""

import click
import logging
import sys
import json
import time
import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

# Add the parent directory to path to import benchmarks
sys.path.append(str(Path(__file__).parent.parent))

from scripts.benchmarks import (
    PostgresBenchmark,
    MongodbBenchmark,
    CouchdbBenchmark,
    CassandraBenchmark,
    ScylladbBenchmark
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/benchmark.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database configurations
DB_CONFIGS = {
    'postgres': {
        'class': PostgresBenchmark,
        'config': {
            'host': 'localhost',
            'port': 5432,
            'database': 'benchmark_db',
            'user': 'benchmark',
            'password': 'benchmark123'
        }
    },
    'mongodb': {
        'class': MongodbBenchmark,
        'config': {
            'host': 'localhost',
            'port': 27017,
            'database': 'benchmark_db',
            'user': 'benchmark',
            'password': 'benchmark123'
        }
    },
    'couchdb': {
        'class': CouchdbBenchmark,
        'config': {
            'host': 'localhost',
            'port': 5984,
            'database': 'benchmark_db',
            'user': 'benchmark',
            'password': 'benchmark123'
        }
    },
    'cassandra': {
        'class': CassandraBenchmark,
        'config': {
            'host': 'localhost',
            'port': 9042,
            'keyspace': 'benchmark_ks',
            'user': None,
            'password': None
        }
    },
    'scylladb': {
        'class': ScylladbBenchmark,
        'config': {
            'host': 'localhost',
            'port': 9043,
            'keyspace': 'benchmark_ks',
            'user': None,
            'password': None
        }
    }
}


class BenchmarkRunner:
    """Main benchmark orchestrator"""
    
    def __init__(self, db_name: str, data_file: str):
        if db_name not in DB_CONFIGS:
            raise ValueError(f"Unknown database: {db_name}")
        
        self.db_name = db_name
        self.data_file = data_file
        self.benchmark_class = DB_CONFIGS[db_name]['class']
        self.config = DB_CONFIGS[db_name]['config']
        self.benchmark = None
        
    def initialize(self):
        """Initialize benchmark instance and connect to database"""
        logger.info(f"Initializing {self.db_name} benchmark")
        self.benchmark = self.benchmark_class(self.config)
        self.benchmark.connect()
        
    def cleanup(self):
        """Clean up resources"""
        if self.benchmark:
            self.benchmark.disconnect()
    
    def run_scalability_test(self, max_records: Optional[int] = None, batch_size: int = 1000):
        """Run scalability test"""
        logger.info(f"Running scalability test for {self.db_name}")
        
        try:
            # Setup schema
            self.benchmark.setup_schema()
            
            # Load test data
            data = self.benchmark.load_test_data(self.data_file, limit=max_records)
            
            # Run scalability test
            results = self.benchmark.run_scalability_test(data, batch_size)
            
            # Save results
            filename = self.benchmark.save_results(results, 'scalability')
            logger.info(f"Scalability test completed. Results saved to {filename}")
            
            return results
            
        except Exception as e:
            logger.error(f"Scalability test failed: {e}")
            raise
    
    def run_load_test(self, num_iterations: int = 1000, batch_size: int = 20,
                     max_records: Optional[int] = None, warmup_iterations: int = 100):
        """Run load test with pre-populated database"""
        logger.info(f"Running load test for {self.db_name}")
        
        try:
            # Setup schema
            self.benchmark.setup_schema()
            
            # Load and insert all test data
            logger.info("Loading and inserting test data...")
            data = self.benchmark.load_test_data(self.data_file, limit=max_records)
            
            # Insert data in batches
            insert_batch_size = 1000
            for i in range(0, len(data), insert_batch_size):
                batch = data[i:i+insert_batch_size]
                self.benchmark.insert_batch(batch)
                if (i + insert_batch_size) % 10000 == 0:
                    logger.info(f"Inserted {i + insert_batch_size} records")
            
            logger.info(f"Total records in database: {self.benchmark.get_record_count()}")
            
            # Perform warmup
            if warmup_iterations > 0:
                logger.info(f"Performing warmup with {warmup_iterations} iterations")
                self.benchmark.warmup(data[:1000], iterations=warmup_iterations)
            
            # Get all codigos for random sampling during load test
            logger.info("Retrieving all codigos for load test...")
            all_codigos = [record['codigo'] for record in data]
            
            # Run the actual load test
            logger.info(f"Starting load test with {num_iterations} iterations")
            results = []
            
            for i in range(num_iterations):
                iteration_results = []
                
                # Run 50 queries in batches of 20-30
                for _ in range(50):
                    # Random batch size between 20-30
                    current_batch_size = random.randint(20, 30)
                    
                    # Select random codigos
                    selected_codigos = random.sample(all_codigos, current_batch_size)
                    
                    # Execute query and measure time
                    _, query_time = self.benchmark.query_by_codigo(selected_codigos)
                    iteration_results.append(query_time)
                
                # Log progress every 100 iterations
                if (i + 1) % 100 == 0:
                    logger.info(f"Completed {i + 1}/{num_iterations} iterations")
                
                # Store iteration statistics
                results.append({
                    'iteration': i + 1,
                    'mean_latency': np.mean(iteration_results),
                    'median_latency': np.median(iteration_results),
                    'p95_latency': np.percentile(iteration_results, 95),
                    'p99_latency': np.percentile(iteration_results, 99),
                    'min_latency': np.min(iteration_results),
                    'max_latency': np.max(iteration_results),
                    'queries_count': len(iteration_results)
                })
            
            # Convert to DataFrame and calculate overall statistics
            df_results = pd.DataFrame(results)
            
            # Add overall statistics
            overall_stats = pd.DataFrame([{
                'database': self.db_name,
                'test_type': 'load_test',
                'total_iterations': num_iterations,
                'queries_per_iteration': 50,
                'batch_size_min': 20,
                'batch_size_max': 30,
                'overall_mean': df_results['mean_latency'].mean(),
                'overall_median': df_results['median_latency'].median(),
                'overall_p95': df_results['p95_latency'].quantile(0.95),
                'overall_p99': df_results['p99_latency'].quantile(0.99),
                'timestamp': datetime.now().isoformat()
            }])
            
            # Save detailed results
            detailed_filename = self.benchmark.save_results(df_results, 'load_test_detailed')
            
            # Save summary results
            summary_filename = self.benchmark.save_results(overall_stats, 'load_test_summary')
            
            logger.info(f"Load test completed. Results saved to {detailed_filename} and {summary_filename}")
            
            return df_results, overall_stats
            
        except Exception as e:
            logger.error(f"Load test failed: {e}")
            raise
    
    def run_substring_test(self, test_strings: List[str], iterations: int = 100,
                          max_records: Optional[int] = None):
        """Run substring search test"""
        logger.info(f"Running substring search test for {self.db_name}")
        
        try:
            # Ensure database is populated
            if self.benchmark.get_record_count() == 0:
                logger.info("Database empty, populating with test data...")
                data = self.benchmark.load_test_data(self.data_file, limit=max_records)
                
                insert_batch_size = 1000
                for i in range(0, len(data), insert_batch_size):
                    batch = data[i:i+insert_batch_size]
                    self.benchmark.insert_batch(batch)
            
            # Run substring tests
            results = self.benchmark.run_substring_search_test(test_strings, iterations)
            
            # Save results
            filename = self.benchmark.save_results(results, 'substring_search')
            logger.info(f"Substring search test completed. Results saved to {filename}")
            
            return results
            
        except Exception as e:
            logger.error(f"Substring search test failed: {e}")
            raise


@click.command()
@click.option('--db', type=click.Choice(['postgres', 'mongodb', 'couchdb', 'cassandra', 'scylladb']),
              required=True, help='Database to benchmark')
@click.option('--test', type=click.Choice(['scalability', 'load', 'substring', 'all']),
              default='all', help='Type of test to run')
@click.option('--data-file', type=click.Path(exists=True), required=True,
              help='Path to JSON data file')
@click.option('--max-records', type=int, default=None,
              help='Maximum number of records to use (default: all)')
@click.option('--batch-size', type=int, default=1000,
              help='Batch size for scalability test')
@click.option('--iterations', type=int, default=1000,
              help='Number of iterations for load test')
@click.option('--warmup', type=int, default=100,
              help='Number of warmup iterations')
@click.option('--teardown/--no-teardown', default=True,
              help='Whether to teardown schema after test')
def main(db, test, data_file, max_records, batch_size, iterations, warmup, teardown):
    """Run database benchmarks"""
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    logger.info(f"Starting benchmark for {db} - Test type: {test}")
    
    runner = BenchmarkRunner(db, data_file)
    
    try:
        runner.initialize()
        
        # Define test substrings for substring search
        test_substrings = ['empresa', 'ltda', 'silva', 'santos', 'oliveira', 
                          'software', 'sistemas', 'consultoria', 'servicos', 'comercio']
        
        if test in ['scalability', 'all']:
            runner.run_scalability_test(max_records, batch_size)
        
        if test in ['load', 'all']:
            runner.run_load_test(iterations, 25, max_records, warmup)
        
        if test in ['substring', 'all']:
            runner.run_substring_test(test_substrings, 100, max_records)
        
        if teardown:
            logger.info("Tearing down schema...")
            runner.benchmark.teardown()
        
        logger.info("Benchmark completed successfully")
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise
    finally:
        runner.cleanup()


if __name__ == '__main__':
    main() 