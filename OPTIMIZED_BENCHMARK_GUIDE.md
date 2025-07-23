# 🚀 Guia para Executar Benchmarks Otimizados

## ✅ O que foi otimizado?

### 1. **Configurações Docker** (`docker-compose.yml`)
- **PostgreSQL**: Buffer aumentado para 512MB, cache 2GB
- **MongoDB**: WiredTiger cache 2GB, compressão ativada
- **CouchDB**: Cache 2GB, timeouts ajustados
- **Cassandra**: Heap 2GB, concurrent reads/writes aumentado
- **ScyllaDB**: 4 threads SMP, 4GB RAM

### 2. **Código Otimizado**
- **CouchDB**: Batch queries usando POST para views
- **Cassandra**: Queries paralelas com `execute_concurrent`
- Ambos com prepared statements e warmup otimizado

## 📋 Como Executar

### Opção 1: Script Interativo (Recomendado)
```bash
./run_optimized_benchmark.sh
```

Este script oferece um menu interativo onde você pode:
- Escolher o tipo de teste (rápido, escalabilidade, carga)
- Selecionar quais bancos testar
- Reiniciar containers com otimizações

### Opção 2: Comando Manual
```bash
# 1. Reiniciar containers com otimizações
docker compose down
docker compose up -d

# 2. Aguardar 30 segundos
sleep 30

# 3. Executar teste específico
python scripts/benchmark_runner.py \
    --db couchdb \
    --test scalability \
    --data-file data/atendimentos_2019-08-22_to_2025-06-11.json \
    --num-records 5000 \
    --batch-size 100 \
    --verbose
```

### Opção 3: Executar Todos de Uma Vez
```bash
# Teste rápido em todos os bancos
for db in postgres mongodb couchdb cassandra scylladb; do
    echo "Testing $db..."
    python scripts/benchmark_runner.py \
        --db $db \
        --test scalability \
        --data-file data/atendimentos_2019-08-22_to_2025-06-11.json \
        --num-records 1000 \
        --batch-size 100
done

# Gerar relatórios
python scripts/compare_results.py
```

## 📊 Resultados Esperados

### Antes das Otimizações
- **CouchDB**: ~24s para teste de carga
- **Cassandra**: ~6s para teste de carga
- **PostgreSQL**: ~5s (já rápido)
- **MongoDB**: ~2s (já rápido)

### Depois das Otimizações
- **CouchDB**: ~8-12s (2-3x mais rápido)
- **Cassandra**: ~2-3s (2-3x mais rápido)
- **PostgreSQL**: ~4s (20% mais rápido)
- **MongoDB**: ~1.8s (10% mais rápido)

## 🎯 Dicas Importantes

1. **Primeira Execução**: Sempre mais lenta (cold cache)
2. **Warmup**: O código já faz warmup automático
3. **Memória**: Certifique-se de ter pelo menos 16GB RAM
4. **SSD**: Performance muito melhor com SSD

## 🐛 Troubleshooting

### Container não sobe
```bash
# Ver logs
docker compose logs cassandra

# Aumentar timeout do healthcheck
# Editar docker-compose.yml: start_period: 120s
```

### Out of Memory
```bash
# Reduzir configurações no docker-compose.yml
# Ex: ScyllaDB --memory 2G ao invés de 4G
```

### CouchDB ainda lento
```bash
# Verificar se views foram criadas
curl -u benchmark:benchmark123 http://localhost:5984/benchmark_db/_design/queries

# Forçar rebuild da view
curl -u benchmark:benchmark123 http://localhost:5984/benchmark_db/_design/queries/_view/by_codigo?limit=1
```

## 📈 Próximos Passos

1. **Ajustar parâmetros** conforme seu hardware
2. **Testar com mais dados** (100k+ registros)
3. **Monitorar recursos** durante execução:
   ```bash
   docker stats
   ```

## 💡 Quick Start

```bash
# Comando mais simples para testar tudo com otimizações:
./run_optimized_benchmark.sh
# Escolha opção 1 (teste rápido)
# Escolha opção 1 (todos os bancos)
``` 