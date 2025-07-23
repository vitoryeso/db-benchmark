#!/usr/bin/env python3
"""
Script para testar conexão e operações básicas em cada banco de dados
"""

import sys
import time
import json
from pathlib import Path

# Adicionar o diretório ao path para importar os benchmarks
sys.path.append(str(Path(__file__).parent))

from scripts.benchmarks import (
    PostgresBenchmark,
    MongodbBenchmark,
    CouchdbBenchmark,
    CassandraBenchmark,
    ScylladbBenchmark
)

# Configurações dos bancos
DB_CONFIGS = {
    'postgres': {
        'class': PostgresBenchmark,
        'config': {
            'host': 'localhost',
            'port': 5432,
            'database': 'benchmark_db',
            'user': 'benchmark',
            'password': 'benchmark123'
        }
    },
    'mongodb': {
        'class': MongodbBenchmark,
        'config': {
            'host': 'localhost',
            'port': 27017,
            'database': 'benchmark_db',
            'user': 'benchmark',
            'password': 'benchmark123'
        }
    },
    'couchdb': {
        'class': CouchdbBenchmark,
        'config': {
            'host': 'localhost',
            'port': 5984,
            'database': 'benchmark_db_test',  # Different DB for testing
            'user': 'benchmark',
            'password': 'benchmark123'
        }
    },
    'cassandra': {
        'class': CassandraBenchmark,
        'config': {
            'host': 'localhost',
            'port': 9042,
            'keyspace': 'benchmark_ks_test',  # Different keyspace for testing
            'user': None,
            'password': None
        }
    },
    'scylladb': {
        'class': ScylladbBenchmark,
        'config': {
            'host': 'localhost',
            'port': 9043,
            'keyspace': 'benchmark_ks_test',  # Different keyspace for testing
            'user': None,
            'password': None
        }
    }
}

# Dados de teste
TEST_DATA = [
    {
        'codigo': 'TEST001',
        'titulo': 'Teste de Conexão 1',
        'data_inicio': '2024-01-01',
        'data_fim': '2024-01-02',
        'origem': 'Teste',
        'contato': 'João Teste',
        'email': 'teste@example.com',
        'descricao': 'Descrição de teste para verificar conexão',
        'atendente': 'Maria Teste',
        'atendente_equipe': 'Equipe Teste',
        'atendente_unidade': 'Unidade Teste',
        'cliente': 'Empresa Teste LTDA',
        'produto': 'Produto Teste',
        'situacao': 'Em andamento',
        'classificacao': 'Teste',
        'sub_classificacao': 'Subteste',
        'tipo': 'Teste',
        'prioridade': 'Média'
    },
    {
        'codigo': 'TEST002',
        'titulo': 'Teste de Conexão 2',
        'data_inicio': '2024-01-03',
        'data_fim': '2024-01-04',
        'origem': 'Teste',
        'contato': 'Maria Silva',
        'email': 'maria@example.com',
        'descricao': 'Segunda descrição de teste',
        'atendente': 'Pedro Santos',
        'atendente_equipe': 'Equipe 2',
        'atendente_unidade': 'Unidade 2',
        'cliente': 'Outra Empresa LTDA',
        'produto': 'Produto 2',
        'situacao': 'Concluído',
        'classificacao': 'Teste 2',
        'sub_classificacao': 'Subteste 2',
        'tipo': 'Teste 2',
        'prioridade': 'Alta'
    }
]


def test_database(db_name):
    """Testa um banco de dados específico"""
    print(f"\n{'='*60}")
    print(f"Testando {db_name.upper()}")
    print(f"{'='*60}")
    
    config = DB_CONFIGS[db_name]
    benchmark_class = config['class']
    
    try:
        # 1. Criar instância e conectar
        print(f"1. Conectando ao {db_name}...", end=' ')
        benchmark = benchmark_class(config['config'])
        benchmark.connect()
        print("✓ OK")
        
        # 2. Configurar schema
        print(f"2. Criando schema/tabelas...", end=' ')
        benchmark.setup_schema()
        print("✓ OK")
        
        # 3. Inserir dados de teste
        print(f"3. Inserindo {len(TEST_DATA)} registros de teste...", end=' ')
        insert_time = benchmark.insert_batch(TEST_DATA)
        print(f"✓ OK ({insert_time:.3f}s)")
        
        # 4. Verificar contagem
        print(f"4. Verificando contagem de registros...", end=' ')
        count = benchmark.get_record_count()
        print(f"✓ OK (Total: {count} registros)")
        
        # 5. Testar query por código
        print(f"5. Testando busca por código...", end=' ')
        results, query_time = benchmark.query_by_codigo(['TEST001', 'TEST002'])
        print(f"✓ OK (Encontrados: {len(results)}, Tempo: {query_time:.3f}s)")
        
        # 6. Testar query por substring
        print(f"6. Testando busca por substring...", end=' ')
        results, query_time = benchmark.query_by_cliente_substring('Empresa', limit=10)
        print(f"✓ OK (Encontrados: {len(results)}, Tempo: {query_time:.3f}s)")
        
        # 7. Limpar dados de teste
        print(f"7. Limpando dados de teste...", end=' ')
        benchmark.teardown()
        print("✓ OK")
        
        # 8. Desconectar
        print(f"8. Desconectando...", end=' ')
        benchmark.disconnect()
        print("✓ OK")
        
        print(f"\n✅ {db_name.upper()} está funcionando corretamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        return False


def main():
    """Testa todos os bancos de dados"""
    print("TESTE DE CONEXÃO DOS BANCOS DE DADOS")
    print("====================================")
    
    # Ordem de teste (bancos mais rápidos primeiro)
    test_order = ['postgres', 'mongodb', 'couchdb', 'cassandra', 'scylladb']
    
    # Aguardar um pouco para garantir que todos os serviços estão prontos
    print("\nAguardando 10 segundos para garantir que todos os serviços estejam prontos...")
    time.sleep(10)
    
    results = {}
    
    for db in test_order:
        # Cassandra e ScyllaDB podem precisar de mais tempo
        if db in ['cassandra', 'scylladb']:
            print(f"\nAguardando mais 20 segundos para {db}...")
            time.sleep(20)
        
        results[db] = test_database(db)
        
        # Pequena pausa entre testes
        time.sleep(2)
    
    # Resumo final
    print(f"\n{'='*60}")
    print("RESUMO DOS TESTES")
    print(f"{'='*60}")
    
    for db, success in results.items():
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{db.upper():15} {status}")
    
    # Verificar se todos passaram
    all_passed = all(results.values())
    
    if all_passed:
        print(f"\n✅ TODOS OS BANCOS ESTÃO FUNCIONANDO!")
        print("\nAgora você pode executar o benchmark completo com:")
        print("  ./run_all_benchmarks.sh data/atendimentos_2019-08-22_to_2025-06-11.json")
    else:
        print(f"\n❌ ALGUNS BANCOS FALHARAM!")
        print("\nVerifique os logs acima e tente:")
        print("  1. docker compose logs <nome-do-servico>")
        print("  2. docker compose restart <nome-do-servico>")
        print("  3. Aguardar mais tempo e tentar novamente")


if __name__ == '__main__':
    main() 