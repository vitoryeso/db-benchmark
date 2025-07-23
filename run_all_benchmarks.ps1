# PowerShell script to run all database benchmarks
# Equivalente ao run_all_benchmarks.sh

Write-Host "🚀 Running All Database Benchmarks" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Check if docker compose is running
Write-Host "`n📋 Checking Docker containers..." -ForegroundColor Blue
docker compose ps

# Ask if user wants to start containers
$response = Read-Host "`nDo you want to start/restart the containers? (y/n)"
if ($response -eq 'y' -or $response -eq 'Y') {
    Write-Host "`n🔄 Restarting containers..." -ForegroundColor Yellow
    docker compose down
    docker compose up -d
    
    Write-Host "⏳ Waiting 30 seconds for containers to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
}

# Configuration
$DATABASES = @("postgres", "mongodb", "couchdb", "cassandra", "scylladb")
$DATA_FILE = "data/atendimentos_2019-08-22_to_2025-06-11.json"
$NUM_RECORDS = 50000
$BATCH_SIZE = 1000
$LOAD_ITERATIONS = 1000

# Create directories if they don't exist
New-Item -ItemType Directory -Force -Path "results" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

Write-Host "`n📊 Benchmark Configuration:" -ForegroundColor Cyan
Write-Host "  - Databases: $($DATABASES -join ', ')"
Write-Host "  - Records: $NUM_RECORDS"
Write-Host "  - Batch Size: $BATCH_SIZE"
Write-Host "  - Load Test Iterations: $LOAD_ITERATIONS"

# Function to run benchmark for a specific database
function Run-Benchmark {
    param(
        [string]$Database
    )
    
    Write-Host "`n" -NoNewline
    Write-Host "="*60 -ForegroundColor Yellow
    Write-Host "Testing $Database" -ForegroundColor Yellow
    Write-Host "="*60 -ForegroundColor Yellow
    
    # Scalability Test
    Write-Host "`n🔍 Running Scalability Test..." -ForegroundColor Blue
    $scalCmd = "python scripts/benchmark_runner.py --db $Database --test scalability --data-file $DATA_FILE --max-records $NUM_RECORDS --batch-size $BATCH_SIZE --warmup 100"
    
    Write-Host "Command: $scalCmd" -ForegroundColor DarkGray
    Invoke-Expression $scalCmd
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Scalability test failed for $Database" -ForegroundColor Red
        return
    }
    
    # Small pause between tests
    Start-Sleep -Seconds 5
    
    # Load Test
    Write-Host "`n🔥 Running Load Test..." -ForegroundColor Blue
    $loadCmd = "python scripts/benchmark_runner.py --db $Database --test load --data-file $DATA_FILE --max-records $NUM_RECORDS --batch-size $BATCH_SIZE --iterations $LOAD_ITERATIONS --warmup 100"
    
    Write-Host "Command: $loadCmd" -ForegroundColor DarkGray
    Invoke-Expression $loadCmd
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Load test failed for $Database" -ForegroundColor Red
        return
    }
    
    # Small pause between tests
    Start-Sleep -Seconds 5
    
    # Substring Search Test
    Write-Host "`n🔤 Running Substring Search Test..." -ForegroundColor Blue
    $substringCmd = "python scripts/benchmark_runner.py --db $Database --test substring --data-file $DATA_FILE --max-records $NUM_RECORDS --batch-size $BATCH_SIZE --warmup 50"
    
    Write-Host "Command: $substringCmd" -ForegroundColor DarkGray
    Invoke-Expression $substringCmd
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Substring search test failed for $Database" -ForegroundColor Red
        return
    }
    
    Write-Host "`n✅ All tests completed for $Database" -ForegroundColor Green
}

# Run benchmarks for each database
foreach ($db in $DATABASES) {
    Run-Benchmark -Database $db
    
    # Pause between databases
    if ($db -ne $DATABASES[-1]) {
        Write-Host "`n⏸️  Pausing 10 seconds before next database..." -ForegroundColor Gray
        Start-Sleep -Seconds 10
    }
}

# Generate comparison reports
Write-Host "`n" -NoNewline
Write-Host "="*60 -ForegroundColor Cyan
Write-Host "📊 Generating Comparison Reports..." -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

python scripts/compare_results.py

# Display summary
Write-Host "`n✅ All benchmarks completed!" -ForegroundColor Green
Write-Host "`n📁 Results saved to:" -ForegroundColor Blue
Write-Host "  - results/*.csv (raw data)"
Write-Host "  - results/visualizations/*.png (charts)"
Write-Host "  - results/visualizations/summary_table.md (summary)"

# Try to display summary if it exists
$summaryFile = "results/visualizations/summary_table.md"
if (Test-Path $summaryFile) {
    Write-Host "`n📋 Summary Preview:" -ForegroundColor Blue
    Get-Content $summaryFile -Tail 30
}

Write-Host "`n🎉 Benchmark suite completed successfully!" -ForegroundColor Green 