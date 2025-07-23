# 🚀 Otimizações de Performance para os Bancos de Dados

## 🐌 CouchDB - Por que é lento?

### Problemas Identificados:
1. **Queries individuais em loop**: O método `query_by_codigo` faz uma query por vez
2. **Busca por substring ineficiente**: Varre todos os documentos manualmente
3. **Views MapReduce**: Precisam ser construídas/atualizadas
4. **Sem cache de queries**: Cada query vai ao disco

### Otimizações Simples:

```python
# 1. Query em batch usando POST com keys
def query_by_codigo_optimized(self, codigos: List[str]) -> Tuple[List[Dict], float]:
    start_time = time.time()
    
    # Usar POST com múltiplas keys de uma vez
    view_url = f"{self.db.resource.url}/_design/queries/_view/by_codigo"
    response = self.db.resource.post_json(view_url, {"keys": codigos})
    
    results = []
    for row in response[2]['rows']:
        if 'value' in row:
            doc = row['value']
            doc.pop('_id', None)
            doc.pop('_rev', None)
            results.append(doc)
    
    elapsed_time = time.time() - start_time
    return results, elapsed_time

# 2. Usar Mango queries (CouchDB 2.0+) ao invés de views
def setup_mango_index(self):
    # Criar índice Mango é mais eficiente
    self.db.index({
        "index": {"fields": ["codigo"]},
        "name": "codigo-index",
        "type": "json"
    })

# 3. Configurar cache no CouchDB
# No docker-compose.yml:
couchdb:
  environment:
    COUCHDB_CACHE_SIZE: 2147483648  # 2GB cache
```

## ⚡ PostgreSQL - Otimizações

### Já está rápido, mas pode melhorar:

```python
# 1. Connection pooling
from psycopg2 import pool

class PostgresBenchmark(BaseBenchmark):
    def __init__(self, config):
        super().__init__(config)
        self.connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20,  # min/max connections
            host=config.get('host', 'localhost'),
            port=config.get('port', 5432),
            database=config.get('database', 'benchmark_db'),
            user=config.get('user', 'benchmark'),
            password=config.get('password', 'benchmark123')
        )

# 2. Prepared statements para queries repetitivas
def prepare_statements(self):
    with self.connection.cursor() as cursor:
        cursor.execute("""
            PREPARE query_by_codigo (text[]) AS 
            SELECT * FROM atendimentos WHERE codigo = ANY($1)
        """)

# 3. Ajustar work_mem para queries grandes
SET work_mem = '256MB';

# 4. ANALYZE após inserções grandes
ANALYZE atendimentos;
```

## 🍃 MongoDB - Otimizações

### Já está bem otimizado, mas pode melhorar:

```python
# 1. Usar projection para retornar apenas campos necessários
def query_by_codigo_optimized(self, codigos: List[str]) -> Tuple[List[Dict], float]:
    start_time = time.time()
    
    # Não retornar campos grandes desnecessários
    projection = {
        '_id': 0,
        'descricao': 0  # Campo grande que pode não ser necessário
    }
    
    results = list(self.collection.find(
        {"codigo": {"$in": codigos}}, 
        projection
    ))
    
    elapsed_time = time.time() - start_time
    return results, elapsed_time

# 2. Usar aggregation pipeline para operações complexas
def query_with_aggregation(self, codigos: List[str]):
    pipeline = [
        {"$match": {"codigo": {"$in": codigos}}},
        {"$project": {"_id": 0}},
        {"$limit": 1000}
    ]
    return list(self.collection.aggregate(pipeline, allowDiskUse=True))

# 3. Hinting do índice correto
results = self.collection.find(
    {"codigo": {"$in": codigos}}
).hint("codigo_1")  # Força uso do índice específico
```

## 🗄️ Cassandra/ScyllaDB - Otimizações

### Problemas com queries não otimizadas para o modelo:

```python
# 1. Usar prepared statements sempre
class CassandraBenchmark(BaseBenchmark):
    def setup_schema(self):
        # ... existing code ...
        
        # Preparar statements comuns
        self.select_by_codigo = self.session.prepare(
            "SELECT * FROM atendimentos WHERE codigo = ?"
        )
        self.insert_stmt = self.session.prepare("""
            INSERT INTO atendimentos (...) VALUES (?, ?, ...)
        """)

# 2. Executar queries em paralelo
from cassandra.concurrent import execute_concurrent

def query_by_codigo_optimized(self, codigos: List[str]) -> Tuple[List[Dict], float]:
    start_time = time.time()
    
    # Criar lista de statements
    statements = [(self.select_by_codigo, (codigo,)) for codigo in codigos]
    
    # Executar em paralelo
    results_list = execute_concurrent(
        self.session, statements, concurrency=50
    )
    
    results = []
    for success, result in results_list:
        if success:
            results.extend([dict(row._asdict()) for row in result])
    
    elapsed_time = time.time() - start_time
    return results, elapsed_time

# 3. Ajustar timeouts e configurações
self.cluster = Cluster(
    contact_points=contact_points,
    port=port,
    executor_threads=8,  # Mais threads
    protocol_version=4,
    connection_class=AsyncoreConnection
)

# 4. Para ScyllaDB - usar shard-aware drivers
# pip install scylla-driver
from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy

cluster = Cluster(
    contact_points=['localhost'],
    load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1'),
    protocol_version=4
)
```

## 🔧 Otimizações Gerais no docker-compose.yml

```yaml
# PostgreSQL
postgres:
  command: >
    postgres
    -c shared_buffers=512MB
    -c effective_cache_size=2GB
    -c work_mem=64MB
    -c maintenance_work_mem=256MB
    -c wal_buffers=32MB
    -c checkpoint_completion_target=0.9
    -c max_wal_size=2GB
    -c min_wal_size=1GB

# MongoDB
mongodb:
  command: >
    mongod
    --wiredTigerCacheSizeGB 2
    --wiredTigerJournalCompressor snappy
    --wiredTigerCollectionBlockCompressor snappy
    --wiredTigerIndexPrefixCompression true

# CouchDB
couchdb:
  environment:
    COUCHDB_USER: benchmark
    COUCHDB_PASSWORD: benchmark123
    COUCHDB_CACHE_SIZE: 2147483648
    COUCHDB_MAX_DBS_OPEN: 500
    
# Cassandra
cassandra:
  environment:
    HEAP_NEWSIZE: 512M
    MAX_HEAP_SIZE: 2G
    CASSANDRA_CONCURRENT_READS: 64
    CASSANDRA_CONCURRENT_WRITES: 64
    
# ScyllaDB
scylladb:
  command: >
    --smp 4
    --memory 4G
    --overprovisioned 1
    --max-io-requests 128
```

## 📊 Resumo das Melhorias Esperadas

| Banco | Problema Principal | Otimização Chave | Melhoria Esperada |
|-------|-------------------|------------------|-------------------|
| CouchDB | Queries individuais | Batch queries + Mango | 5-10x |
| PostgreSQL | Já otimizado | Connection pool | 20-30% |
| MongoDB | Já otimizado | Projections | 10-20% |
| Cassandra | Queries sequenciais | Parallelização | 3-5x |
| ScyllaDB | Batch size | Aumentar batch + parallel | 2-3x |

## 🎯 Quick Wins (Implementação Rápida)

1. **CouchDB**: Mudar para Mango queries ao invés de views
2. **Cassandra/ScyllaDB**: Usar `execute_concurrent` 
3. **Todos**: Aumentar cache/buffer no docker-compose
4. **PostgreSQL**: Adicionar `ANALYZE` após inserções
5. **MongoDB**: Usar projections para reduzir I/O 