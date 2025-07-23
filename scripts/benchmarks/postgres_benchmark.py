import psycopg2
import psycopg2.extras
import time
import logging
from typing import List, Dict, Any, Tuple
from .base_benchmark import BaseBenchmark

logger = logging.getLogger(__name__)


class PostgresBenchmark(BaseBenchmark):
    """PostgreSQL benchmark implementation"""
    
    def connect(self):
        """Establish connection to PostgreSQL"""
        try:
            self.connection = psycopg2.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5432),
                database=self.config.get('database', 'benchmark_db'),
                user=self.config.get('user', 'benchmark'),
                password=self.config.get('password', 'benchmark123')
            )
            self.connection.autocommit = False
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def disconnect(self):
        """Close PostgreSQL connection"""
        if self.connection:
            self.connection.close()
            logger.info("Disconnected from PostgreSQL")
    
    def setup_schema(self):
        """Create table and indexes"""
        with self.connection.cursor() as cursor:
            # Create table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS atendimentos (
                    id SERIAL PRIMARY KEY,
                    codigo VARCHAR(255) NOT NULL,
                    titulo TEXT,
                    data_inicio VARCHAR(255),
                    data_fim VARCHAR(255),
                    origem VARCHAR(255),
                    contato TEXT,
                    email VARCHAR(255),
                    descricao TEXT,
                    atendente VARCHAR(255),
                    atendente_equipe VARCHAR(255),
                    atendente_unidade VARCHAR(255),
                    cliente TEXT,
                    produto TEXT,
                    situacao VARCHAR(255),
                    classificacao VARCHAR(255),
                    sub_classificacao VARCHAR(255),
                    tipo VARCHAR(255),
                    prioridade VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_codigo ON atendimentos(codigo)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cliente ON atendimentos(cliente)")
            
            # Create GIN index for full-text search on cliente
            cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cliente_trgm ON atendimentos USING gin(cliente gin_trgm_ops)")
            
            self.connection.commit()
            logger.info("PostgreSQL schema created")
    
    def teardown(self):
        """Drop table and clean up"""
        with self.connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS atendimentos CASCADE")
            self.connection.commit()
        logger.info("PostgreSQL schema dropped")
    
    def insert_batch(self, data: List[Dict[str, Any]]) -> float:
        """Insert a batch of records"""
        start_time = time.time()
        
        with self.connection.cursor() as cursor:
            # Prepare insert query
            insert_query = """
                INSERT INTO atendimentos (
                    codigo, titulo, data_inicio, data_fim, origem, contato, email,
                    descricao, atendente, atendente_equipe, atendente_unidade,
                    cliente, produto, situacao, classificacao, sub_classificacao,
                    tipo, prioridade
                ) VALUES %s
            """
            
            # Prepare data tuples
            values = []
            for record in data:
                values.append((
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
            
            # Execute batch insert
            psycopg2.extras.execute_values(cursor, insert_query, values)
            self.connection.commit()
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Inserted {len(data)} records in {elapsed_time:.3f}s")
        return elapsed_time
    
    def query_by_codigo(self, codigos: List[str]) -> Tuple[List[Dict], float]:
        """Query records by codigo"""
        start_time = time.time()
        
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # Use ANY for efficient IN query
            cursor.execute(
                "SELECT * FROM atendimentos WHERE codigo = ANY(%s)",
                (codigos,)
            )
            results = cursor.fetchall()
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Queried {len(codigos)} codigos in {elapsed_time:.3f}s, found {len(results)} records")
        
        return results, elapsed_time
    
    def query_by_cliente_substring(self, substring: str, limit: int = 100) -> Tuple[List[Dict], float]:
        """Query records by cliente substring using trigram similarity"""
        start_time = time.time()
        
        with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            # Use trigram index for efficient substring search
            cursor.execute(
                "SELECT * FROM atendimentos WHERE cliente ILIKE %s LIMIT %s",
                (f'%{substring}%', limit)
            )
            results = cursor.fetchall()
        
        elapsed_time = time.time() - start_time
        logger.debug(f"Queried cliente substring '{substring}' in {elapsed_time:.3f}s, found {len(results)} records")
        
        return results, elapsed_time
    
    def get_record_count(self) -> int:
        """Get total number of records"""
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM atendimentos")
            count = cursor.fetchone()[0]
        return count
    
    def get_all_codigos(self) -> List[str]:
        """Get all codigo values for load testing"""
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT codigo FROM atendimentos")
            return [row[0] for row in cursor.fetchall()] 