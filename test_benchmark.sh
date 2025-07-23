#!/bin/bash

# Script de teste rápido do benchmark

echo "=== Teste Rápido do Benchmark ==="
echo "Usando arquivo: data/atendimentos_2019-08-22_to_2025-06-11.json"
echo ""

# Testar com PostgreSQL primeiro (geralmente o mais estável)
echo "Testando PostgreSQL com apenas 1000 registros..."
python scripts/benchmark_runner.py \
    --db postgres \
    --test scalability \
    --data-file data/atendimentos_2019-08-22_to_2025-06-11.json \
    --max-records 1000 \
    --batch-size 100 \
    --iterations 10 \
    --warmup 5

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Teste bem-sucedido!"
    echo ""
    echo "Agora você pode executar o benchmark completo com:"
    echo "  ./run_all_benchmarks.sh data/atendimentos_2019-08-22_to_2025-06-11.json"
    echo ""
    echo "Ou testar um banco específico:"
    echo "  python scripts/benchmark_runner.py --db mongodb --test all --data-file data/atendimentos_2019-08-22_to_2025-06-11.json"
else
    echo ""
    echo "✗ Erro no teste. Verifique:"
    echo "  1. Se o Docker Compose está rodando: docker compose ps"
    echo "  2. Os logs de erro acima"
    echo "  3. Se o arquivo de dados está no formato correto"
fi 