#!/bin/bash

# Script para executar todos os benchmarks sequencialmente

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se o arquivo de dados foi fornecido
if [ $# -eq 0 ]; then
    echo -e "${RED}Erro: Forneça o caminho para o arquivo de dados JSON${NC}"
    echo "Uso: ./run_all_benchmarks.sh <caminho_para_arquivo_json>"
    exit 1
fi

DATA_FILE=$1

# Verificar se o arquivo existe
if [ ! -f "$DATA_FILE" ]; then
    echo -e "${RED}Erro: Arquivo $DATA_FILE não encontrado${NC}"
    exit 1
fi

echo -e "${GREEN}=== Iniciando Benchmark de Bancos de Dados ===${NC}"
echo -e "Arquivo de dados: $DATA_FILE\n"

# Lista de bancos de dados
DBS=("postgres" "mongodb" "couchdb" "cassandra" "scylladb")

# Verificar se Docker Compose está rodando
echo -e "${YELLOW}Verificando serviços Docker...${NC}"
docker compose ps

echo -e "\n${YELLOW}Aguardando 30 segundos para garantir que todos os serviços estejam prontos...${NC}"
sleep 30

# Executar benchmarks
for db in "${DBS[@]}"; do
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}Executando benchmark para: $db${NC}"
    echo -e "${GREEN}========================================${NC}\n"
    
    # Executar todos os testes para o banco atual
    python scripts/benchmark_runner.py \
        --db "$db" \
        --test all \
        --data-file "$DATA_FILE" \
        --iterations 1000 \
        --warmup 100 \
        --batch-size 1000
    
    # Verificar se o comando foi bem-sucedido
    if [ $? -eq 0 ]; then
        echo -e "\n${GREEN}✓ Benchmark para $db concluído com sucesso${NC}"
    else
        echo -e "\n${RED}✗ Erro ao executar benchmark para $db${NC}"
    fi
    
    # Pequena pausa entre bancos
    echo -e "\n${YELLOW}Aguardando 10 segundos antes do próximo banco...${NC}"
    sleep 10
done

echo -e "\n${GREEN}=== Todos os benchmarks foram executados ===${NC}"
echo -e "\n${YELLOW}Gerando visualizações e relatórios...${NC}\n"

# Gerar relatórios e visualizações
python scripts/compare_results.py

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Relatórios gerados com sucesso!${NC}"
    echo -e "${GREEN}Verifique os resultados em:${NC}"
    echo -e "  - results/visualizations/scalability_comparison.png"
    echo -e "  - results/visualizations/load_test_distribution.png"
    echo -e "  - results/visualizations/substring_search_comparison.png"
    echo -e "  - results/visualizations/summary_table.md"
else
    echo -e "\n${RED}✗ Erro ao gerar relatórios${NC}"
fi

echo -e "\n${GREEN}=== Benchmark completo! ===${NC}" 