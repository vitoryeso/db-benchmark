# PowerShell script for quick benchmark test
# Versão PowerShell do test_benchmark.sh

Write-Host "🧪 Quick Benchmark Test" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan

# Ensure Docker is running
$dockerStatus = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker is running" -ForegroundColor Green

# Check if containers are up
Write-Host "`n📋 Checking containers..." -ForegroundColor Blue
docker compose ps

# Small scalability test with PostgreSQL
Write-Host "`n🔍 Running quick test with PostgreSQL (100 records)..." -ForegroundColor Yellow

$cmd = @"
python scripts/benchmark_runner.py `
    --db postgres `
    --test scalability `
    --data-file data/atendimentos_2019-08-22_to_2025-06-11.json `
    --max-records 100 `
    --batch-size 10 `
    --warmup 5
"@

Write-Host "Command: $cmd" -ForegroundColor DarkGray
Invoke-Expression $cmd

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Test completed successfully!" -ForegroundColor Green
    Write-Host "You can now run the full benchmark with:" -ForegroundColor Blue
    Write-Host "  PowerShell: .\run_optimized_benchmark.ps1" -ForegroundColor White
    Write-Host "  or" -ForegroundColor Gray
    Write-Host "  PowerShell: .\run_all_benchmarks.ps1" -ForegroundColor White
} else {
    Write-Host "`n❌ Test failed. Please check the error messages above." -ForegroundColor Red
    Write-Host "`nTroubleshooting tips:" -ForegroundColor Yellow
    Write-Host "1. Make sure all containers are running: docker compose up -d"
    Write-Host "2. Check if Python dependencies are installed: pip install -r requirements.txt"
    Write-Host "3. Verify the data file exists: data/atendimentos_2019-08-22_to_2025-06-11.json"
} 