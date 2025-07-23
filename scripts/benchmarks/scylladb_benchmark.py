import logging
from typing import List, Dict, Any
from .cassandra_benchmark import CassandraBenchmark

logger = logging.getLogger(__name__)


class ScylladbBenchmark(CassandraBenchmark):
    """ScyllaDB benchmark implementation
    
    ScyllaDB is compatible with Cassandra, so we inherit most functionality.
    This class contains ScyllaDB-specific optimizations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        # Override default port if not specified
        if 'port' not in config:
            config['port'] = 9043  # Using different port to avoid conflict with Cassandra
        super().__init__(config)
        self.db_name = 'scylladb'  # Override db_name
    
    def setup_schema(self):
        """Create table with ScyllaDB-specific optimizations"""
        # Create table with appropriate settings for ScyllaDB
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
            ) WITH 
                compression = {'sstable_compression': 'LZ4Compressor'} AND
                compaction = {'class': 'LeveledCompactionStrategy'} AND
                caching = {'keys': 'ALL', 'rows_per_partition': 'ALL'}
        """)
        
        # Create secondary index on cliente
        self.session.execute("""
            CREATE INDEX IF NOT EXISTS idx_cliente ON atendimentos (cliente)
        """)
        
        # ScyllaDB supports local secondary indexes for better performance
        try:
            self.session.execute("""
                CREATE INDEX IF NOT EXISTS idx_cliente_local ON atendimentos ((codigo), cliente)
            """)
            logger.info("Local secondary index created")
        except Exception as e:
            logger.warning(f"Could not create local secondary index: {e}")
        
        logger.info("ScyllaDB schema created with optimizations")
    
    def optimize_for_load_test(self):
        """ScyllaDB-specific optimizations"""
        # ScyllaDB handles many optimizations automatically
        # but we can tune some parameters
        
        # Increase timeout for large queries
        self.cluster.read_timeout = 20.0  # ScyllaDB is generally faster
        
        # Enable speculative execution for better tail latency
        from cassandra.policies import ConstantSpeculativeExecutionPolicy
        self.cluster.speculative_execution_policy = ConstantSpeculativeExecutionPolicy(
            delay=50,  # milliseconds
            max_attempts=2
        )
        
        # Pre-compile frequently used statements
        self.select_by_codigo_stmt = self.session.prepare("""
            SELECT * FROM atendimentos WHERE codigo = ?
        """)
        
        # Enable tracing for debugging (optional)
        # self.session.default_trace = True
        
        logger.info("ScyllaDB optimizations applied")
    
    def insert_batch(self, data: List[Dict[str, Any]]) -> float:
        """Insert with ScyllaDB optimizations"""
        # ScyllaDB can handle larger batches than Cassandra
        import time
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
        
        # Execute batch insert with larger batch size for ScyllaDB
        from cassandra import ConsistencyLevel
        from cassandra.query import BatchStatement
        
        batch_size = 100  # ScyllaDB can handle larger batches
        for i in range(0, len(data), batch_size):
            batch = BatchStatement(consistency_level=ConsistencyLevel.LOCAL_ONE)
            
            for record in data[i:i+batch_size]:
                batch.add(insert_stmt, (
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
                ))
            
            self.session.execute(batch)
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Inserted {len(data)} records in {elapsed_time:.3f}s")
        return elapsed_time 