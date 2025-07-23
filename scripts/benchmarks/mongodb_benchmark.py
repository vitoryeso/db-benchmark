import pymongo
import time
import logging
from typing import List, Dict, Any, Tuple
from .base_benchmark import BaseBenchmark

logger = logging.getLogger(__name__)


class MongodbBenchmark(BaseBenchmark):
    """MongoDB benchmark implementation"""
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            # MongoDB connection string
            connection_string = f"mongodb://{self.config.get('user', 'benchmark')}:{self.config.get('password', 'benchmark123')}@{self.config.get('host', 'localhost')}:{self.config.get('port', 27017)}/"
            
            self.client = pymongo.MongoClient(connection_string)
            self.db = self.client[self.config.get('database', 'benchmark_db')]
            self.collection = self.db['atendimentos']
            
            # Test connection
            self.client.server_info()
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def disconnect(self):
        """Close MongoDB connection"""
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    def setup_schema(self):
        """Create collection and indexes"""
        # MongoDB creates collections automatically, but we'll ensure indexes exist
        
        # Create indexes
        self.collection.create_index("codigo", unique=False)
        self.collection.create_index("cliente")
        
        # Create text index for substring search
        self.collection.create_index([("cliente", pymongo.TEXT)])
        
        logger.info("MongoDB indexes created")
    
    def teardown(self):
        """Drop collection"""
        self.collection.drop()
        logger.info("MongoDB collection dropped")
    
    def insert_batch(self, data: List[Dict[str, Any]]) -> float:
        """Insert a batch of records"""
        start_time = time.time()
        
        # MongoDB expects documents, so we can insert directly
        # Add timestamp for consistency with other DBs
        documents = []
        for record in data:
            doc = record.copy()
            doc['created_at'] = start_time
            documents.append(doc)
        
        # Insert many documents
        self.collection.insert_many(documents)
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Inserted {len(data)} records in {elapsed_time:.3f}s")
        return elapsed_time
    
    def query_by_codigo(self, codigos: List[str]) -> Tuple[List[Dict], float]:
        """Query records by codigo"""
        start_time = time.time()
        
        # Use $in operator for multiple values
        results = list(self.collection.find({"codigo": {"$in": codigos}}))
        
        # Remove MongoDB's _id field for consistency
        for result in results:
            result.pop('_id', None)
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Queried {len(codigos)} codigos in {elapsed_time:.3f}s, found {len(results)} records")
        
        return results, elapsed_time
    
    def query_by_cliente_substring(self, substring: str, limit: int = 100) -> Tuple[List[Dict], float]:
        """Query records by cliente substring"""
        start_time = time.time()
        
        # Use regex for substring search (case-insensitive)
        results = list(self.collection.find(
            {"cliente": {"$regex": substring, "$options": "i"}},
            limit=limit
        ))
        
        # Remove MongoDB's _id field for consistency
        for result in results:
            result.pop('_id', None)
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Queried cliente substring '{substring}' in {elapsed_time:.3f}s, found {len(results)} records")
        
        return results, elapsed_time
    
    def get_record_count(self) -> int:
        """Get total number of records"""
        return self.collection.count_documents({})
    
    def get_all_codigos(self) -> List[str]:
        """Get all codigo values for load testing"""
        # Use aggregation for better performance
        pipeline = [
            {"$group": {"_id": None, "codigos": {"$push": "$codigo"}}},
            {"$project": {"_id": 0, "codigos": 1}}
        ]
        
        result = list(self.collection.aggregate(pipeline))
        if result:
            return result[0]['codigos']
        return []
    
    def optimize_for_load_test(self):
        """Additional optimizations for MongoDB before load test"""
        # Ensure all indexes are built
        self.collection.reindex()
        
        # Pre-load index into memory (warming)
        self.db.command("planCacheSetFilter", "atendimentos", {
            "codigo": {"$exists": True}
        })
        
        logger.info("MongoDB optimizations applied") 