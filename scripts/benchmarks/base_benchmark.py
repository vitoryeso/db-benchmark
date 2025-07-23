import abc
import time
import json
import logging
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from pathlib import Path
import numpy as np
from tqdm import tqdm

logger = logging.getLogger(__name__)


class BenchmarkResult:
    """Class to store benchmark results"""
    def __init__(self):
        self.latencies = []
        self.errors = []
        self.metadata = {}
    
    def add_latency(self, latency: float):
        self.latencies.append(latency)
    
    def add_error(self, error: str):
        self.errors.append(error)
    
    def get_statistics(self) -> Dict[str, float]:
        """Calculate statistics from latencies"""
        if not self.latencies:
            return {}
        
        return {
            'count': len(self.latencies),
            'mean': np.mean(self.latencies),
            'median': np.median(self.latencies),
            'std': np.std(self.latencies),
            'min': np.min(self.latencies),
            'max': np.max(self.latencies),
            'p95': np.percentile(self.latencies, 95),
            'p99': np.percentile(self.latencies, 99),
            'error_count': len(self.errors)
        }


class BaseBenchmark(abc.ABC):
    """Abstract base class for database benchmarks"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_name = self.__class__.__name__.replace('Benchmark', '').lower()
        self.connection = None
        self.results = {}
        
    @abc.abstractmethod
    def connect(self):
        """Establish connection to the database"""
        pass
    
    @abc.abstractmethod
    def disconnect(self):
        """Close connection to the database"""
        pass
    
    @abc.abstractmethod
    def setup_schema(self):
        """Create tables/collections and indexes"""
        pass
    
    @abc.abstractmethod
    def teardown(self):
        """Clean up database resources"""
        pass
    
    @abc.abstractmethod
    def insert_batch(self, data: List[Dict[str, Any]]) -> float:
        """Insert a batch of records and return time taken"""
        pass
    
    @abc.abstractmethod
    def query_by_codigo(self, codigos: List[str]) -> Tuple[List[Dict], float]:
        """Query records by codigo field"""
        pass
    
    @abc.abstractmethod
    def query_by_cliente_substring(self, substring: str, limit: int = 100) -> Tuple[List[Dict], float]:
        """Query records by cliente substring"""
        pass
    
    @abc.abstractmethod
    def get_record_count(self) -> int:
        """Get total number of records in database"""
        pass
    
    def load_test_data(self, file_path: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load test data from JSON file"""
        logger.info(f"Loading test data from {file_path}")
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if limit:
            data = data[:limit]
        
        logger.info(f"Loaded {len(data)} records")
        return data
    
    def warmup(self, sample_data: List[Dict[str, Any]], iterations: int = 100):
        """Perform warmup queries to stabilize cache"""
        logger.info(f"Performing warmup with {iterations} iterations")
        
        # Get sample codigos for warmup
        sample_codigos = [record['codigo'] for record in sample_data[:50]]
        
        for _ in tqdm(range(iterations), desc="Warmup"):
            # Random queries to warm up the cache
            batch_size = np.random.randint(10, 30)
            selected_codigos = np.random.choice(sample_codigos, size=batch_size, replace=True).tolist()
            
            try:
                self.query_by_codigo(selected_codigos)
            except Exception as e:
                logger.warning(f"Warmup query failed: {e}")
    
    def run_scalability_test(self, data: List[Dict[str, Any]], batch_size: int = 1000) -> pd.DataFrame:
        """Run scalability test - measure performance as data grows"""
        logger.info(f"Running scalability test with {len(data)} total records")
        
        results = []
        total_batches = len(data) // batch_size
        
        for i in tqdm(range(total_batches), desc="Scalability Test"):
            # Insert batch
            batch_data = data[i * batch_size:(i + 1) * batch_size]
            insert_time = self.insert_batch(batch_data)
            
            # Current database size
            current_size = self.get_record_count()
            
            # Perform query test - 10 batches of 20 records each
            query_latencies = []
            for _ in range(10):
                # Select random codigos from inserted data so far
                all_inserted = data[:(i + 1) * batch_size]
                selected_records = np.random.choice(all_inserted, size=20, replace=False)
                selected_codigos = [r['codigo'] for r in selected_records]
                
                _, query_time = self.query_by_codigo(selected_codigos)
                query_latencies.append(query_time)
            
            # Record results
            results.append({
                'batch_number': i + 1,
                'records_in_db': current_size,
                'insert_time': insert_time,
                'query_mean_latency': np.mean(query_latencies),
                'query_median_latency': np.median(query_latencies),
                'query_p95_latency': np.percentile(query_latencies, 95),
                'query_p99_latency': np.percentile(query_latencies, 99),
                'timestamp': datetime.now().isoformat()
            })
        
        return pd.DataFrame(results)
    
    def run_load_test(self, num_iterations: int = 1000, batch_size: int = 20) -> pd.DataFrame:
        """Run load test - measure performance under sustained load"""
        logger.info(f"Running load test with {num_iterations} iterations")
        
        # Get total record count for sampling
        total_records = self.get_record_count()
        
        # Get all codigos for random sampling
        # Note: In real implementation, we'd need a way to get all codigos efficiently
        # For now, we'll assume we have access to the data
        
        result = BenchmarkResult()
        
        for i in tqdm(range(num_iterations), desc="Load Test"):
            # Run 50 queries in parallel (simulated as sequential for now)
            iteration_latencies = []
            
            for _ in range(50):
                # Generate random codigos
                # In real implementation, we'd select from existing codigos
                # For now, we'll use a placeholder
                try:
                    # This is a placeholder - actual implementation would select real codigos
                    _, query_time = self.query_by_codigo(['placeholder'] * batch_size)
                    iteration_latencies.append(query_time)
                    result.add_latency(query_time)
                except Exception as e:
                    result.add_error(str(e))
                    logger.error(f"Query failed in iteration {i}: {e}")
            
            # Add some variation in timing between iterations
            time.sleep(0.01)
        
        # Calculate statistics
        stats = result.get_statistics()
        
        # Convert to DataFrame for consistency
        df = pd.DataFrame([{
            'database': self.db_name,
            'test_type': 'load_test',
            'iterations': num_iterations,
            'queries_per_iteration': 50,
            'batch_size': batch_size,
            **stats,
            'timestamp': datetime.now().isoformat()
        }])
        
        return df
    
    def run_substring_search_test(self, substrings: List[str], iterations: int = 100) -> pd.DataFrame:
        """Run substring search test on cliente field"""
        logger.info(f"Running substring search test with {len(substrings)} patterns")
        
        results = []
        
        for substring in tqdm(substrings, desc="Substring Search Test"):
            latencies = []
            
            for _ in range(iterations):
                try:
                    _, query_time = self.query_by_cliente_substring(substring)
                    latencies.append(query_time)
                except Exception as e:
                    logger.error(f"Substring query failed for '{substring}': {e}")
            
            if latencies:
                results.append({
                    'substring': substring,
                    'mean_latency': np.mean(latencies),
                    'median_latency': np.median(latencies),
                    'p95_latency': np.percentile(latencies, 95),
                    'p99_latency': np.percentile(latencies, 99),
                    'iterations': len(latencies)
                })
        
        return pd.DataFrame(results)
    
    def save_results(self, results: pd.DataFrame, test_name: str):
        """Save results to CSV file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/{self.db_name}_{test_name}_{timestamp}.csv"
        
        Path("results").mkdir(exist_ok=True)
        results.to_csv(filename, index=False)
        logger.info(f"Results saved to {filename}")
        
        return filename 