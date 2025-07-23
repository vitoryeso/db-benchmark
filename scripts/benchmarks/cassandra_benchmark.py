from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import DCAwareRoundRobinPolicy
import time
import logging
from typing import List, Dict, Any, Tuple
from .base_benchmark import BaseBenchmark

logger = logging.getLogger(__name__)


class CassandraBenchmark(BaseBenchmark):
    """Cassandra benchmark implementation"""
    
    def connect(self):
        """Establish connection to Cassandra"""
        try:
            # Cassandra connection setup
            contact_points = [self.config.get('host', 'localhost')]
            port = self.config.get('port', 9042)
            
            # Authentication if needed
            auth_provider = None
            if self.config.get('user') and self.config.get('password'):
                auth_provider = PlainTextAuthProvider(
                    username=self.config.get('user'),
                    password=self.config.get('password')
                )
            
            self.cluster = Cluster(
                contact_points=contact_points,
                port=port,
                auth_provider=auth_provider,
                load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1')
            )
            
            self.session = self.cluster.connect()
            
            # Create keyspace
            keyspace = self.config.get('keyspace', 'benchmark_ks')
            self.session.execute(f"""
                CREATE KEYSPACE IF NOT EXISTS {keyspace}
                WITH replication = {{
                    'class': 'SimpleStrategy',
                    'replication_factor': 1
                }}
            """)
            
            self.session.set_keyspace(keyspace)
            logger.info("Connected to Cassandra")
        except Exception as e:
            logger.error(f"Failed to connect to Cassandra: {e}")
            raise
    
    def disconnect(self):
        """Close Cassandra connection"""
        if hasattr(self, 'cluster'):
            self.cluster.shutdown()
            logger.info("Disconnected from Cassandra")
    
    def setup_schema(self):
        """Create table with appropriate partition key"""
        # Create table with codigo as partition key for efficient lookups
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS atendimentos (
                codigo text PRIMARY KEY,
                titulo text,
                data_inicio text,
                data_fim text,
                origem text,
                contato text,
                email text,
                descricao text,
                atendente text,
                atendente_equipe text,
                atendente_unidade text,
                cliente text,
                produto text,
                situacao text,
                classificacao text,
                sub_classificacao text,
                tipo text,
                prioridade text,
                created_at timestamp
            )
        """)
        
        # Create secondary index on cliente for substring searches
        self.session.execute("""
            CREATE INDEX IF NOT EXISTS idx_cliente ON atendimentos (cliente)
        """)
        
        # Create custom index for SASI (if available) for better text search
        try:
            self.session.execute("""
                CREATE CUSTOM INDEX IF NOT EXISTS idx_cliente_sasi ON atendimentos (cliente)
                USING 'org.apache.cassandra.index.sasi.SASIIndex'
                WITH OPTIONS = {
                    'mode': 'CONTAINS',
                    'analyzer_class': 'org.apache.cassandra.index.sasi.analyzer.StandardAnalyzer',
                    'case_sensitive': 'false'
                }
            """)
            logger.info("SASI index created for text search")
        except Exception as e:
            logger.warning(f"Could not create SASI index: {e}")
        
        logger.info("Cassandra schema created")
    
    def teardown(self):
        """Drop table"""
        self.session.execute("DROP TABLE IF EXISTS atendimentos")
        logger.info("Cassandra table dropped")
    
    def insert_batch(self, data: List[Dict[str, Any]]) -> float:
        """Insert a batch of records"""
        start_time = time.time()
        
        # Prepare insert statement
        insert_stmt = self.session.prepare("""
            INSERT INTO atendimentos (
                codigo, titulo, data_inicio, data_fim, origem, contato, email,
                descricao, atendente, atendente_equipe, atendente_unidade,
                cliente, produto, situacao, classificacao, sub_classificacao,
                tipo, prioridade, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, toTimestamp(now()))
        """)
        
        # Execute batch insert
        from cassandra import ConsistencyLevel
        from cassandra.query import BatchStatement
        
        batch_size = 50  # Cassandra has limits on batch size
        for i in range(0, len(data), batch_size):
            batch = BatchStatement(consistency_level=ConsistencyLevel.LOCAL_ONE)
            
            for record in data[i:i+batch_size]:
                batch.add(insert_stmt, (
                    record.get('codigo', ''),
                    record.get('titulo', ''),
                    record.get('data_inicio', ''),
                    record.get('data_fim', ''),
                    record.get('origem', ''),
                    record.get('contato', ''),
                    record.get('email', ''),
                    record.get('descricao', ''),
                    record.get('atendente', ''),
                    record.get('atendente_equipe', ''),
                    record.get('atendente_unidade', ''),
                    record.get('cliente', ''),
                    record.get('produto', ''),
                    record.get('situacao', ''),
                    record.get('classificacao', ''),
                    record.get('sub_classificacao', ''),
                    record.get('tipo', ''),
                    record.get('prioridade', '')
                ))
            
            self.session.execute(batch)
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Inserted {len(data)} records in {elapsed_time:.3f}s")
        return elapsed_time
    
    def query_by_codigo(self, codigos: List[str]) -> Tuple[List[Dict], float]:
        """Query records by codigo (primary key)"""
        start_time = time.time()
        
        # Prepare select statement
        select_stmt = self.session.prepare("""
            SELECT * FROM atendimentos WHERE codigo = ?
        """)
        
        results = []
        # Execute individual queries for each codigo (Cassandra doesn't support IN on partition key efficiently)
        for codigo in codigos:
            rows = self.session.execute(select_stmt, (codigo,))
            for row in rows:
                results.append(dict(row._asdict()))
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Queried {len(codigos)} codigos in {elapsed_time:.3f}s, found {len(results)} records")
        
        return results, elapsed_time
    
    def query_by_cliente_substring(self, substring: str, limit: int = 100) -> Tuple[List[Dict], float]:
        """Query records by cliente substring"""
        start_time = time.time()
        
        # Try SASI index first if available
        try:
            query = f"""
                SELECT * FROM atendimentos 
                WHERE cliente LIKE '%{substring}%' 
                LIMIT {limit}
                ALLOW FILTERING
            """
            rows = self.session.execute(query)
        except:
            # Fallback to basic query with filtering
            query = f"""
                SELECT * FROM atendimentos 
                LIMIT {limit * 10}
                ALLOW FILTERING
            """
            rows = self.session.execute(query)
        
        results = []
        for row in rows:
            row_dict = dict(row._asdict())
            # Manual filtering if SASI not available
            if substring.lower() in row_dict.get('cliente', '').lower():
                results.append(row_dict)
                if len(results) >= limit:
                    break
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Queried cliente substring '{substring}' in {elapsed_time:.3f}s, found {len(results)} records")
        
        return results, elapsed_time
    
    def get_record_count(self) -> int:
        """Get total number of records"""
        # Note: COUNT in Cassandra can be slow for large tables
        result = self.session.execute("SELECT COUNT(*) FROM atendimentos")
        return result.one()[0]
    
    def get_all_codigos(self) -> List[str]:
        """Get all codigo values for load testing"""
        # Warning: This can be expensive in Cassandra
        rows = self.session.execute("SELECT codigo FROM atendimentos")
        return [row.codigo for row in rows]
    
    def optimize_for_load_test(self):
        """Cassandra-specific optimizations"""
        # Increase read timeout for large queries
        self.cluster.read_timeout = 30.0
        
        # Pre-compile frequently used statements
        self.select_by_codigo_stmt = self.session.prepare("""
            SELECT * FROM atendimentos WHERE codigo = ?
        """)
        
        logger.info("Cassandra optimizations applied") 