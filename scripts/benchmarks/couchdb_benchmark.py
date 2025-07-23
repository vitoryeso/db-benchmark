import couchdb
import time
import logging
import json
from typing import List, Dict, Any, Tuple
from .base_benchmark import BaseBenchmark

logger = logging.getLogger(__name__)


class CouchdbBenchmark(BaseBenchmark):
    """CouchDB benchmark implementation"""
    
    def connect(self):
        """Establish connection to CouchDB"""
        try:
            # Create CouchDB server connection
            server_url = f"http://{self.config.get('user', 'benchmark')}:{self.config.get('password', 'benchmark123')}@{self.config.get('host', 'localhost')}:{self.config.get('port', 5984)}/"
            
            self.server = couchdb.Server(server_url)
            
            # Create or get database
            db_name = self.config.get('database', 'benchmark_db')
            if db_name in self.server:
                self.db = self.server[db_name]
            else:
                self.db = self.server.create(db_name)
            
            logger.info("Connected to CouchDB")
        except Exception as e:
            logger.error(f"Failed to connect to CouchDB: {e}")
            raise
    
    def disconnect(self):
        """Close CouchDB connection"""
        # CouchDB doesn't require explicit disconnection
        logger.info("Disconnected from CouchDB")
    
    def setup_schema(self):
        """Create views for indexing"""
        # Create design document with views
        design_doc = {
            "_id": "_design/queries",
            "views": {
                "by_codigo": {
                    "map": """
                        function(doc) {
                            if (doc.codigo) {
                                emit(doc.codigo, doc);
                            }
                        }
                    """
                },
                "by_cliente": {
                    "map": """
                        function(doc) {
                            if (doc.cliente) {
                                emit(doc.cliente, doc);
                            }
                        }
                    """
                },
                "cliente_substring": {
                    "map": """
                        function(doc) {
                            if (doc.cliente) {
                                // Index all substrings for efficient search
                                var cliente = doc.cliente.toLowerCase();
                                for (var i = 0; i < cliente.length - 2; i++) {
                                    for (var j = i + 3; j <= cliente.length && j <= i + 20; j++) {
                                        emit(cliente.substring(i, j), doc);
                                    }
                                }
                            }
                        }
                    """
                }
            }
        }
        
        # Save or update design document
        try:
            existing = self.db.get("_design/queries")
            if existing:
                design_doc["_rev"] = existing["_rev"]
        except:
            pass
        
        self.db.save(design_doc)
        
        # Create mango indexes for better query performance using direct HTTP requests
        import requests
        import json as json_lib
        
        # Get database URL
        db_url = f"http://{self.config.get('user', 'benchmark')}:{self.config.get('password', 'benchmark123')}@{self.config.get('host', 'localhost')}:{self.config.get('port', 5984)}/{self.config.get('database', 'benchmark_db')}"
        
        # Create index for codigo
        codigo_index = {
            "index": {
                "fields": ["codigo"]
            },
            "name": "codigo-index",
            "type": "json"
        }
        
        try:
            response = requests.post(f"{db_url}/_index", 
                                   json=codigo_index,
                                   headers={"Content-Type": "application/json"})
            if response.status_code not in [200, 201]:
                logger.warning(f"Could not create codigo index: {response.text}")
        except Exception as e:
            logger.warning(f"Could not create codigo index: {e}")
        
        # Create index for cliente
        cliente_index = {
            "index": {
                "fields": ["cliente"]
            },
            "name": "cliente-index",
            "type": "json"
        }
        
        try:
            response = requests.post(f"{db_url}/_index", 
                                   json=cliente_index,
                                   headers={"Content-Type": "application/json"})
            if response.status_code not in [200, 201]:
                logger.warning(f"Could not create cliente index: {response.text}")
        except Exception as e:
            logger.warning(f"Could not create cliente index: {e}")
        
        logger.info("CouchDB views and indexes created")
    
    def teardown(self):
        """Delete database"""
        db_name = self.config.get('database', 'benchmark_db')
        if db_name in self.server:
            del self.server[db_name]
        logger.info("CouchDB database deleted")
    
    def insert_batch(self, data: List[Dict[str, Any]]) -> float:
        """Insert a batch of records"""
        start_time = time.time()
        
        # CouchDB requires documents to have unique _id
        documents = []
        for i, record in enumerate(data):
            doc = record.copy()
            # Use codigo as _id if unique, otherwise generate one
            doc['_id'] = f"{record.get('codigo', '')}_{start_time}_{i}"
            doc['created_at'] = start_time
            documents.append(doc)
        
        # Bulk insert
        self.db.update(documents)
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Inserted {len(data)} records in {elapsed_time:.3f}s")
        return elapsed_time
    
    def query_by_codigo(self, codigos: List[str]) -> Tuple[List[Dict], float]:
        """Query records by codigo using view or direct lookup"""
        start_time = time.time()
        
        results = []
        
        # Use the view to query by codigo
        for codigo in codigos:
            try:
                # Query the view
                for row in self.db.view('queries/by_codigo', key=codigo):
                    doc = row.value
                    # Remove CouchDB internal fields
                    doc.pop('_id', None)
                    doc.pop('_rev', None)
                    results.append(doc)
            except Exception as e:
                logger.debug(f"Error querying codigo {codigo}: {e}")
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Queried {len(codigos)} codigos in {elapsed_time:.3f}s, found {len(results)} records")
        
        return results, elapsed_time
    
    def query_by_cliente_substring(self, substring: str, limit: int = 100) -> Tuple[List[Dict], float]:
        """Query records by cliente substring"""
        start_time = time.time()
        
        results = []
        count = 0
        
        # Use all_docs and filter manually (not ideal but works)
        # In production, you'd use a full-text search index
        for doc_id in self.db:
            if count >= limit:
                break
            
            try:
                doc = self.db[doc_id]
                if 'cliente' in doc and substring.lower() in doc['cliente'].lower():
                    # Make a copy to avoid modifying the original
                    result_doc = doc.copy()
                    # Remove CouchDB internal fields
                    result_doc.pop('_id', None)
                    result_doc.pop('_rev', None)
                    results.append(result_doc)
                    count += 1
            except Exception as e:
                logger.debug(f"Error accessing document {doc_id}: {e}")
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Queried cliente substring '{substring}' in {elapsed_time:.3f}s, found {len(results)} records")
        
        return results, elapsed_time
    
    def get_record_count(self) -> int:
        """Get total number of records"""
        return len(self.db)
    
    def get_all_codigos(self) -> List[str]:
        """Get all codigo values for load testing"""
        codigos = []
        
        # Use the view to get all codigos
        for row in self.db.view('queries/by_codigo'):
            codigos.append(row.key)
        
        return codigos
    
    def optimize_for_load_test(self):
        """Trigger view building to optimize queries"""
        # Access views to ensure they are built
        _ = list(self.db.view('queries/by_codigo', limit=1))
        _ = list(self.db.view('queries/by_cliente', limit=1))
        
        # Compact database for better performance
        self.db.compact()
        
        logger.info("CouchDB optimizations applied") 