#!/bin/bash
# Script para executar benchmarks com otimizações

echo "🚀 Database Benchmark com Otimizações"
echo "===================================="

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se docker compose está rodando
echo -e "${BLUE}1. Verificando containers Docker...${NC}"
docker compose ps

# Perguntar se quer reiniciar os containers
read -p "Deseja reiniciar os containers com as novas otimizações? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo -e "${YELLOW}Reiniciando containers...${NC}"
    docker compose down
    docker compose up -d
    
    # Aguardar containers subirem
    echo -e "${YELLOW}Aguardando 30s para containers iniciarem...${NC}"
    sleep 30
fi

# Criar diretórios necessários
mkdir -p results logs

# Menu de opções
echo -e "\n${BLUE}2. Escolha o tipo de teste:${NC}"
echo "   1) Teste rápido (1000 registros)"
echo "   2) Teste de escalabilidade (10k registros)"
echo "   3) Teste de carga completo (50k registros)"
echo "   4) Teste customizado"
read -p "Opção: " test_option

case $test_option in
    1)
        RECORDS=1000
        TEST_TYPE="quick"
        ;;
    2)
        RECORDS=10000
        TEST_TYPE="scalability"
        ;;
    3)
        RECORDS=50000
        TEST_TYPE="load"
        ;;
    4)
        read -p "Quantidade de registros: " RECORDS
        TEST_TYPE="custom"
        ;;
    *)
        echo "Opção inválida"
        exit 1
        ;;
esac

# Menu de bancos
echo -e "\n${BLUE}3. Escolha os bancos para testar:${NC}"
echo "   1) Todos os bancos"
echo "   2) Apenas PostgreSQL e MongoDB"
echo "   3) Apenas CouchDB (com otimizações)"
echo "   4) Apenas Cassandra e ScyllaDB (com otimizações)"
echo "   5) Escolher específicos"
read -p "Opção: " db_option

case $db_option in
    1)
        DATABASES="postgres mongodb couchdb cassandra scylladb"
        ;;
    2)
        DATABASES="postgres mongodb"
        ;;
    3)
        DATABASES="couchdb"
        ;;
    4)
        DATABASES="cassandra scylladb"
        ;;
    5)
        echo "Bancos disponíveis: postgres mongodb couchdb cassandra scylladb"
        read -p "Digite os bancos separados por espaço: " DATABASES
        ;;
    *)
        echo "Opção inválida"
        exit 1
        ;;
esac

# Executar benchmarks
echo -e "\n${GREEN}4. Executando benchmarks...${NC}"
echo "   Tipo: $TEST_TYPE"
echo "   Registros: $RECORDS"
echo "   Bancos: $DATABASES"
echo

for db in $DATABASES; do
    echo -e "\n${YELLOW}=== Testando $db ===${NC}"
    
    # Teste de escalabilidade
    echo -e "${BLUE}Teste de Escalabilidade:${NC}"
    python scripts/benchmark_runner.py \
        --db $db \
        --test scalability \
        --data-file data/atendimentos_2019-08-22_to_2025-06-11.json \
        --num-records $RECORDS \
        --batch-size 100 \
        --verbose
    
    # Pequena pausa entre testes
    sleep 5
    
    # Teste de carga (apenas se não for teste rápido)
    if [ "$TEST_TYPE" != "quick" ]; then
        echo -e "\n${BLUE}Teste de Carga:${NC}"
        python scripts/benchmark_runner.py \
            --db $db \
            --test load \
            --data-file data/atendimentos_2019-08-22_to_2025-06-11.json \
            --num-records $RECORDS \
            --batch-size 100 \
            --load-iterations 100 \
            --verbose
        
        sleep 5
    fi
done

# Gerar relatórios
echo -e "\n${GREEN}5. Gerando relatórios comparativos...${NC}"
python scripts/compare_results.py

echo -e "\n${GREEN}✅ Benchmark concluído!${NC}"
echo "Resultados salvos em:"
echo "  - results/ (CSVs com dados brutos)"
echo "  - results/comparison_*.png (gráficos)"
echo "  - results/summary.md (tabela resumo)"

# Mostrar resumo rápido
if [ -f "results/summary.md" ]; then
    echo -e "\n${BLUE}Resumo dos resultados:${NC}"
    tail -n 20 results/summary.md
fi 