from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import DCAwareRoundRobinPolicy
from cassandra.concurrent import execute_concurrent, execute_concurrent_with_args
import time
import logging
from typing import List, Dict, Any, Tuple
from .cassandra_benchmark import CassandraBenchmark

logger = logging.getLogger(__name__)


class CassandraBenchmarkOptimized(CassandraBenchmark):
    """Optimized Cassandra benchmark with parallel queries and prepared statements"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.prepared_statements = {}
    
    def connect(self):
        """Establish connection with optimized settings"""
        try:
            contact_points = [self.config.get('host', 'localhost')]
            port = self.config.get('port', 9042)
            
            auth_provider = None
            if self.config.get('user') and self.config.get('password'):
                auth_provider = PlainTextAuthProvider(
                    username=self.config.get('user'),
                    password=self.config.get('password')
                )
            
            # Optimized cluster configuration
            self.cluster = Cluster(
                contact_points=contact_points,
                port=port,
                auth_provider=auth_provider,
                load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1'),
                protocol_version=4,  # Fixed protocol version
                executor_threads=8,  # More executor threads
                connection_class=None,  # Use default
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
            
            # Prepare common statements
            self._prepare_statements()
            
            logger.info("Connected to Cassandra with optimized settings")
        except Exception as e:
            logger.error(f"Failed to connect to Cassandra: {e}")
            raise
    
    def _prepare_statements(self):
        """Prepare all commonly used statements"""
        # Prepare select by codigo
        self.prepared_statements['select_by_codigo'] = self.session.prepare(
            "SELECT * FROM atendimentos WHERE codigo = ?"
        )
        
        # Prepare insert statement
        self.prepared_statements['insert'] = self.session.prepare("""
            INSERT INTO atendimentos (
                codigo, titulo, data_inicio, data_fim, origem, contato, email,
                descricao, atendente, atendente_equipe, atendente_unidade,
                cliente, produto, situacao, classificacao, sub_classificacao,
                tipo, prioridade, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, toTimestamp(now()))
        """)
        
        logger.info("Prepared statements created")
    
    def query_by_codigo(self, codigos: List[str]) -> Tuple[List[Dict], float]:
        """Query records by codigo using parallel execution"""
        start_time = time.time()
        
        try:
            # Use execute_concurrent for parallel queries
            statement = self.prepared_statements.get('select_by_codigo')
            if not statement:
                # Fallback if statement not prepared
                return super().query_by_codigo(codigos)
            
            # Create list of bound statements
            statements_and_params = [
                (statement, (codigo,)) for codigo in codigos
            ]
            
            # Execute in parallel with higher concurrency
            results_list = execute_concurrent(
                self.session, 
                statements_and_params, 
                concurrency=min(100, len(codigos)),  # Adaptive concurrency
                raise_on_first_error=False
            )
            
            results = []
            for success, result in results_list:
                if success:
                    for row in result:
                        results.append(dict(row._asdict()))
                else:
                    logger.warning(f"Query failed: {result}")
            
            elapsed_time = time.time() - start_time
            logger.debug(f"Parallel queried {len(codigos)} codigos in {elapsed_time:.3f}s, found {len(results)} records")
            
            return results, elapsed_time
            
        except Exception as e:
            logger.error(f"Parallel query failed: {e}")
            # Fallback to sequential
            return super().query_by_codigo(codigos)
    
    def insert_batch(self, data: List[Dict[str, Any]]) -> float:
        """Insert with optimized batching"""
        start_time = time.time()
        
        try:
            # Use prepared insert statement
            insert_stmt = self.prepared_statements.get('insert')
            if not insert_stmt:
                # Fallback if statement not prepared
                return super().insert_batch(data)
            
            # Create list of statements with parameters
            statements_and_params = []
            for record in data:
                params = (
                    str(record.get('codigo', '')),
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
                )
                statements_and_params.append((insert_stmt, params))
            
            # Execute in parallel instead of batches
            results = execute_concurrent(
                self.session,
                statements_and_params,
                concurrency=50,
                raise_on_first_error=False
            )
            
            # Check for errors
            errors = [r for s, r in results if not s]
            if errors:
                logger.warning(f"Insert had {len(errors)} errors")
            
            elapsed_time = time.time() - start_time
            logger.debug(f"Parallel inserted {len(data)} records in {elapsed_time:.3f}s")
            return elapsed_time
            
        except Exception as e:
            logger.error(f"Optimized insert failed: {e}")
            # Fallback to batch insert
            return super().insert_batch(data)
    
    def optimize_for_load_test(self):
        """Cassandra-specific optimizations"""
        # Increase timeouts
        self.cluster.read_timeout = 30.0
        self.cluster.write_timeout = 30.0
        
        # Set consistency level for better performance
        from cassandra import ConsistencyLevel
        self.session.default_consistency_level = ConsistencyLevel.LOCAL_ONE
        
        # Ensure prepared statements are ready
        if not self.prepared_statements:
            self._prepare_statements()
        
        logger.info("Cassandra optimizations applied for load test") 