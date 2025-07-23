import couchdb
import time
import logging
import json
import requests
from typing import List, Dict, Any, Tuple
from .couchdb_benchmark import CouchdbBenchmark

logger = logging.getLogger(__name__)


class CouchdbBenchmarkOptimized(CouchdbBenchmark):
    """Optimized CouchDB benchmark implementation with batch queries"""
    
    def query_by_codigo(self, codigos: List[str]) -> Tuple[List[Dict], float]:
        """Query records by codigo using batch POST to view"""
        start_time = time.time()
        
        try:
            # Build the view URL
            db_url = f"http://{self.config.get('user', 'benchmark')}:{self.config.get('password', 'benchmark123')}@{self.config.get('host', 'localhost')}:{self.config.get('port', 5984)}/{self.config.get('database', 'benchmark_db')}"
            view_url = f"{db_url}/_design/queries/_view/by_codigo"
            
            # POST request with multiple keys at once
            headers = {"Content-Type": "application/json"}
            data = {"keys": codigos}
            
            response = requests.post(view_url, json=data, headers=headers)
            response.raise_for_status()
            
            results = []
            result_data = response.json()
            
            for row in result_data.get('rows', []):
                if 'value' in row and row['value'] is not None:
                    doc = row['value'].copy()
                    doc.pop('_id', None)
                    doc.pop('_rev', None)
                    results.append(doc)
            
            elapsed_time = time.time() - start_time
            logger.debug(f"Batch queried {len(codigos)} codigos in {elapsed_time:.3f}s, found {len(results)} records")
            
            return results, elapsed_time
            
        except Exception as e:
            logger.error(f"Batch query failed: {e}")
            # Fallback to original implementation
            return super().query_by_codigo(codigos)
    
    def setup_schema(self):
        """Create optimized views and Mango indexes"""
        # First create standard views
        super().setup_schema()
        
        # Try to create Mango index for better performance
        try:
            db_url = f"http://{self.config.get('user', 'benchmark')}:{self.config.get('password', 'benchmark123')}@{self.config.get('host', 'localhost')}:{self.config.get('port', 5984)}/{self.config.get('database', 'benchmark_db')}"
            
            # Create text index for substring search
            text_index = {
                "index": {
                    "fields": [{"cliente": "text"}]
                },
                "name": "cliente-text-index",
                "type": "text"
            }
            
            response = requests.post(
                f"{db_url}/_index", 
                json=text_index,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                logger.info("Created text index for cliente field")
            
        except Exception as e:
            logger.warning(f"Could not create text index: {e}")
    
    def query_by_cliente_substring(self, substring: str, limit: int = 100) -> Tuple[List[Dict], float]:
        """Query using Mango if available, otherwise fallback"""
        start_time = time.time()
        
        try:
            # Try Mango query first
            db_url = f"http://{self.config.get('user', 'benchmark')}:{self.config.get('password', 'benchmark123')}@{self.config.get('host', 'localhost')}:{self.config.get('port', 5984)}/{self.config.get('database', 'benchmark_db')}"
            
            # Mango query for text search
            query = {
                "selector": {
                    "$text": {
                        "$search": substring
                    }
                },
                "limit": limit
            }
            
            response = requests.post(
                f"{db_url}/_find",
                json=query,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                results = []
                data = response.json()
                
                for doc in data.get('docs', []):
                    result_doc = doc.copy()
                    result_doc.pop('_id', None)
                    result_doc.pop('_rev', None)
                    results.append(result_doc)
                
                elapsed_time = time.time() - start_time
                logger.debug(f"Mango queried cliente substring '{substring}' in {elapsed_time:.3f}s, found {len(results)} records")
                return results, elapsed_time
                
        except Exception as e:
            logger.debug(f"Mango query failed, falling back: {e}")
        
        # Fallback to original implementation
        return super().query_by_cliente_substring(substring, limit)
    
    def optimize_for_load_test(self):
        """Additional optimizations for CouchDB before load test"""
        super().optimize_for_load_test()
        
        # Ensure views are warmed up with parallel requests
        import concurrent.futures
        
        try:
            # Warm up views in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                
                # Warm up by_codigo view
                for i in range(4):
                    future = executor.submit(
                        lambda: list(self.db.view('queries/by_codigo', limit=100, skip=i*100))
                    )
                    futures.append(future)
                
                # Wait for all warmup queries to complete
                concurrent.futures.wait(futures)
                
            logger.info("CouchDB views warmed up in parallel")
            
        except Exception as e:
            logger.warning(f"Could not warm up views in parallel: {e}") 