# PowerShell script para executar benchmarks com otimizações
# Versão PowerShell do run_optimized_benchmark.sh

Write-Host "🚀 Database Benchmark com Otimizações" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

# Verificar se docker compose está rodando
Write-Host "`n1. Verificando containers Docker..." -ForegroundColor Blue
docker compose ps

# Perguntar se quer reiniciar os containers
$restart = Read-Host "`nDeseja reiniciar os containers com as novas otimizações? (s/n)"
if ($restart -eq 's' -or $restart -eq 'S') {
    Write-Host "`nReiniciando containers..." -ForegroundColor Yellow
    docker compose down
    docker compose up -d
    
    # Aguardar containers subirem
    Write-Host "Aguardando 30s para containers iniciarem..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
}

# Criar diretórios necessários
New-Item -ItemType Directory -Force -Path "results" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

# Menu de opções - Tipo de teste
Write-Host "`n2. Escolha o tipo de teste:" -ForegroundColor Blue
Write-Host "   1) Teste rápido (1000 registros)"
Write-Host "   2) Teste de escalabilidade (10k registros)"
Write-Host "   3) Teste de carga completo (50k registros)"
Write-Host "   4) Teste customizado"
$testOption = Read-Host "Opção"

switch ($testOption) {
    "1" {
        $RECORDS = 1000
        $TEST_TYPE = "quick"
    }
    "2" {
        $RECORDS = 10000
        $TEST_TYPE = "scalability"
    }
    "3" {
        $RECORDS = 50000
        $TEST_TYPE = "load"
    }
    "4" {
        $RECORDS = Read-Host "Quantidade de registros"
        $TEST_TYPE = "custom"
    }
    default {
        Write-Host "Opção inválida" -ForegroundColor Red
        exit 1
    }
}

# Menu de bancos
Write-Host "`n3. Escolha os bancos para testar:" -ForegroundColor Blue
Write-Host "   1) Todos os bancos"
Write-Host "   2) Apenas PostgreSQL e MongoDB"
Write-Host "   3) Apenas CouchDB (com otimizações)"
Write-Host "   4) Apenas Cassandra e ScyllaDB (com otimizações)"
Write-Host "   5) Escolher específicos"
$dbOption = Read-Host "Opção"

switch ($dbOption) {
    "1" {
        $DATABASES = @("postgres", "mongodb", "couchdb", "cassandra", "scylladb")
    }
    "2" {
        $DATABASES = @("postgres", "mongodb")
    }
    "3" {
        $DATABASES = @("couchdb")
    }
    "4" {
        $DATABASES = @("cassandra", "scylladb")
    }
    "5" {
        Write-Host "Bancos disponíveis: postgres mongodb couchdb cassandra scylladb"
        $dbInput = Read-Host "Digite os bancos separados por espaço"
        $DATABASES = $dbInput -split ' '
    }
    default {
        Write-Host "Opção inválida" -ForegroundColor Red
        exit 1
    }
}

# Configuração do arquivo de dados
$DATA_FILE = "data/atendimentos_2019-08-22_to_2025-06-11.json"
$BATCH_SIZE = 100

# Executar benchmarks
Write-Host "`n4. Executando benchmarks..." -ForegroundColor Green
Write-Host "   Tipo: $TEST_TYPE"
Write-Host "   Registros: $RECORDS"
Write-Host "   Bancos: $($DATABASES -join ', ')"
Write-Host ""

foreach ($db in $DATABASES) {
    Write-Host "`n" -NoNewline
    Write-Host "=== Testando $db ===" -ForegroundColor Yellow
    
    # Teste de escalabilidade
    Write-Host "Teste de Escalabilidade:" -ForegroundColor Blue
    $scalCmd = "python scripts/benchmark_runner.py --db $db --test scalability --data-file $DATA_FILE --max-records $RECORDS --batch-size $BATCH_SIZE --warmup 50"
    
    Write-Host "Comando: $scalCmd" -ForegroundColor DarkGray
    Invoke-Expression $scalCmd
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Falha no teste de escalabilidade para $db" -ForegroundColor Red
        continue
    }
    
    # Pequena pausa entre testes
    Start-Sleep -Seconds 5
    
    # Teste de carga (apenas se não for teste rápido)
    if ($TEST_TYPE -ne "quick") {
        Write-Host "`nTeste de Carga:" -ForegroundColor Blue
        $loadCmd = "python scripts/benchmark_runner.py --db $db --test load --data-file $DATA_FILE --max-records $RECORDS --batch-size $BATCH_SIZE --iterations 100 --warmup 50"
        
        Write-Host "Comando: $loadCmd" -ForegroundColor DarkGray
        Invoke-Expression $loadCmd
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Falha no teste de carga para $db" -ForegroundColor Red
            continue
        }
        
        Start-Sleep -Seconds 5
    }
}

# Gerar relatórios
Write-Host "`n5. Gerando relatórios comparativos..." -ForegroundColor Green
python scripts/compare_results.py

Write-Host "`n✅ Benchmark concluído!" -ForegroundColor Green
Write-Host "Resultados salvos em:"
Write-Host "  - results/ (CSVs com dados brutos)"
Write-Host "  - results/visualizations/ (gráficos e tabela resumo)"

# Mostrar resumo rápido
$summaryFile = "results/visualizations/summary_table.md"
if (Test-Path $summaryFile) {
    Write-Host "`nResumo dos resultados:" -ForegroundColor Blue
    Get-Content $summaryFile -Tail 20
}

# Menu final
Write-Host "`n" -NoNewline
Write-Host "="*60 -ForegroundColor Cyan
Write-Host "O que deseja fazer agora?" -ForegroundColor Cyan
Write-Host "1) Ver gráficos (abre pasta de resultados)"
Write-Host "2) Executar novo teste"
Write-Host "3) Sair"
$finalOption = Read-Host "Opção"

switch ($finalOption) {
    "1" {
        # Abrir pasta de resultados no Explorer
        if (Test-Path "results/visualizations") {
            explorer.exe "results\visualizations"
        } else {
            Write-Host "Pasta de visualizações não encontrada" -ForegroundColor Red
        }
    }
    "2" {
        # Executar novamente
        & $PSCommandPath
    }
    "3" {
        Write-Host "Até logo! 👋" -ForegroundColor Green
    }
}

# Dica sobre otimizações
Write-Host "`n💡 Dica: Para mais detalhes sobre as otimizações aplicadas, veja:" -ForegroundColor Yellow
Write-Host "   - OPTIMIZATIONS.md"
Write-Host "   - OPTIMIZED_BENCHMARK_GUIDE.md" 