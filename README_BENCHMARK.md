# Database Benchmark V2

## Visão Geral

Este projeto implementa um benchmark comparativo entre 5 bancos de dados NoSQL e SQL para armazenamento e busca de documentos JSON:
- PostgreSQL
- MongoDB
- CouchDB
- Cassandra
- ScyllaDB

## Estrutura do Projeto

```
db-benchmark/
├── docker-compose.yml       # Configuração dos bancos de dados
├── requirements.txt         # Dependências Python
├── scripts/
│   ├── benchmark_runner.py  # Script principal do benchmark
│   ├── compare_results.py   # Análise e visualização de resultados
│   └── benchmarks/          # Implementações específicas por banco
│       ├── base_benchmark.py
│       ├── postgres_benchmark.py
│       ├── mongodb_benchmark.py
│       ├── couchdb_benchmark.py
│       ├── cassandra_benchmark.py
│       └── scylladb_benchmark.py
├── data/                    # Arquivos de dados JSON
├── results/                 # Resultados dos testes (CSV)
├── logs/                    # Logs de execução
└── config/                  # Configurações adicionais
```

## Requisitos

- Docker e Docker Compose
- Python 3.8+
- Arquivo JSON com dados de teste no formato especificado

## Instalação

1. Clone o repositório:
```bash
git clone <repository-url>
cd db-benchmark
```

2. Instale as dependências Python:
```bash
pip install -r requirements.txt
```

3. Inicie os bancos de dados:
```bash
docker compose up -d
```

4. Aguarde todos os serviços ficarem saudáveis:
```bash
docker compose ps
```

## Formato dos Dados

O arquivo JSON deve conter uma lista de objetos com a seguinte estrutura:

```json
[
  {
    "codigo": "12345",
    "titulo": "Título do atendimento",
    "data_inicio": "2024-01-01",
    "data_fim": "2024-01-02",
    "origem": "Web",
    "contato": "João Silva",
    "email": "joao@example.com",
    "descricao": "Descrição detalhada",
    "atendente": "Maria Santos",
    "atendente_equipe": "Suporte",
    "atendente_unidade": "São Paulo",
    "cliente": "Empresa XYZ LTDA",
    "produto": "Software ABC",
    "situacao": "Resolvido",
    "classificacao": "Técnico",
    "sub_classificacao": "Bug",
    "tipo": "Incidente",
    "prioridade": "Alta"
  }
]
```

## Executando os Benchmarks

### Teste Completo (Todos os Testes)

```bash
python scripts/benchmark_runner.py --db postgres --test all --data-file data/atendimentos.json
```

### Teste de Escalabilidade

Mede a performance conforme o banco cresce:

```bash
python scripts/benchmark_runner.py --db mongodb --test scalability --data-file data/atendimentos.json --batch-size 1000
```

### Teste de Carga

Mede a performance sob carga sustentada com banco populado:

```bash
python scripts/benchmark_runner.py --db cassandra --test load --data-file data/atendimentos.json --iterations 1000 --warmup 100
```

### Teste de Busca por Substring

Testa buscas por substring no campo cliente:

```bash
python scripts/benchmark_runner.py --db couchdb --test substring --data-file data/atendimentos.json
```

### Parâmetros Disponíveis

- `--db`: Banco de dados a testar (postgres, mongodb, couchdb, cassandra, scylladb)
- `--test`: Tipo de teste (scalability, load, substring, all)
- `--data-file`: Caminho para o arquivo JSON com os dados
- `--max-records`: Número máximo de registros a usar (padrão: todos)
- `--batch-size`: Tamanho do lote para teste de escalabilidade (padrão: 1000)
- `--iterations`: Número de iterações para teste de carga (padrão: 1000)
- `--warmup`: Número de iterações de aquecimento (padrão: 100)
- `--teardown/--no-teardown`: Se deve limpar o schema após o teste

## Analisando Resultados

Após executar os benchmarks, gere visualizações e relatórios:

```bash
python scripts/compare_results.py
```

Isso irá gerar:
- `results/visualizations/scalability_comparison.png`: Gráfico de escalabilidade
- `results/visualizations/load_test_distribution.png`: Distribuição de latência
- `results/visualizations/substring_search_comparison.png`: Comparação de busca por substring
- `results/visualizations/summary_table.md`: Tabela resumo em Markdown

## Executando Todos os Bancos

Para executar o benchmark em todos os bancos sequencialmente:

```bash
#!/bin/bash
for db in postgres mongodb couchdb cassandra scylladb; do
    echo "Running benchmark for $db..."
    python scripts/benchmark_runner.py --db $db --test all --data-file data/atendimentos.json
done

# Gerar relatórios
python scripts/compare_results.py
```

## Troubleshooting

### Bancos não conectam
- Verifique se todos os containers estão rodando: `docker compose ps`
- Verifique os logs: `docker compose logs <service-name>`
- Aguarde mais tempo para Cassandra/ScyllaDB iniciarem (podem levar até 60s)

### Erro de memória
- Reduza o número de registros: `--max-records 10000`
- Aumente a memória disponível para Docker

### Cassandra/ScyllaDB lento
- Esses bancos são otimizados para clusters distribuídos
- Performance em single-node pode não refletir uso real

## Interpretando Resultados

### Métricas Principais

1. **Latência Média**: Tempo médio de resposta das queries
2. **P95/P99**: Percentis que mostram os piores casos
3. **Escalabilidade**: Como a performance degrada com mais dados
4. **Distribuição**: Consistência da performance (menor variação é melhor)

### Considerações

- PostgreSQL: Excelente para queries complexas e ACID
- MongoDB: Bom para documentos JSON nativos
- CouchDB: Ótimo para sincronização e views MapReduce
- Cassandra: Ideal para escrita massiva e distribuição
- ScyllaDB: Cassandra otimizado com melhor performance

## Desenvolvimento

Para adicionar um novo banco de dados:

1. Crie uma classe em `scripts/benchmarks/novo_benchmark.py`
2. Herde de `BaseBenchmark` e implemente todos os métodos abstratos
3. Adicione a configuração em `benchmark_runner.py`
4. Adicione o serviço no `docker-compose.yml`

## Licença

MIT License - veja LICENSE para detalhes 