# =============================================================================
# BAL-AGENTIC-BACKEND PLATFORM - DEPLOYMENT SCRIPT (Windows PowerShell)
# =============================================================================
# Version: 3.0.0
# Usage: .\deploy.ps1
# =============================================================================

Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host "BAL-AGENTIC-BACKEND PLATFORM - DEPLOYMENT SCRIPT" -ForegroundColor Cyan
Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host ""

# =============================================================================
# STEP 1: Pre-flight Checks
# =============================================================================
Write-Host "[1/6] Running pre-flight checks..." -ForegroundColor Yellow

# Check if Docker is installed
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop" -ForegroundColor Red
    exit 1
}

# Check if Docker is running
try {
    docker ps | Out-Null
    Write-Host "  Docker is running" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker daemon is not running" -ForegroundColor Red
    Write-Host "Please start Docker Desktop" -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host "WARNING: .env file not found!" -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host "Please edit .env file with your configuration" -ForegroundColor Yellow
        Write-Host "Then run this script again" -ForegroundColor Yellow
        exit 0
    } else {
        Write-Host "ERROR: Neither .env nor .env.example found" -ForegroundColor Red
        exit 1
    }
}

Write-Host "  .env file found" -ForegroundColor Green

# Check required directories
$required_dirs = @("departments", "templates", "addons", "core", "config_modules")
foreach ($dir in $required_dirs) {
    if (!(Test-Path $dir)) {
        Write-Host "ERROR: Required directory not found: $dir" -ForegroundColor Red
        exit 1
    }
}
Write-Host "  All required directories present" -ForegroundColor Green

Write-Host ""

# =============================================================================
# STEP 2: Create directories if they don't exist
# =============================================================================
Write-Host "[2/6] Creating directories..." -ForegroundColor Yellow

$dirs = @(
    "generated_dashboards",
    "logs",
    "config_modules/generated_dashboards",
    "config_modules/logs"
)

foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "  Exists: $dir" -ForegroundColor Gray
    }
}

Write-Host ""

# =============================================================================
# STEP 3: Stop existing containers
# =============================================================================
Write-Host "[3/6] Stopping existing containers..." -ForegroundColor Yellow

docker-compose down
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Containers stopped successfully" -ForegroundColor Green
} else {
    Write-Host "  No containers to stop (first deployment?)" -ForegroundColor Gray
}

Write-Host ""

# =============================================================================
# STEP 4: Build Docker image
# =============================================================================
Write-Host "[4/6] Building Docker image..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes on first build..." -ForegroundColor Gray

docker-compose build --no-cache
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker build failed" -ForegroundColor Red
    exit 1
}

Write-Host "  Build completed successfully" -ForegroundColor Green
Write-Host ""

# =============================================================================
# STEP 5: Start containers
# =============================================================================
Write-Host "[5/6] Starting BAL-Agentic-Backend platform..." -ForegroundColor Yellow

docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to start containers" -ForegroundColor Red
    exit 1
}

Write-Host "  Containers started successfully" -ForegroundColor Green
Write-Host ""

# =============================================================================
# STEP 6: Health check
# =============================================================================
Write-Host "[6/6] Waiting for services to be healthy..." -ForegroundColor Yellow

$max_retries = 30
$retry_count = 0
$healthy = $false

while ($retry_count -lt $max_retries) {
    Start-Sleep -Seconds 2
    $retry_count++

    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5100/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    } catch {
        Write-Host "  Attempt $retry_count/$max_retries - Service not ready yet..." -ForegroundColor Gray
    }
}

Write-Host ""

if ($healthy) {
    Write-Host "=============================================================================" -ForegroundColor Green
    Write-Host "DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
    Write-Host "=============================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "BAL-Agentic-Backend platform is running on: http://localhost:5100" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Available endpoints:" -ForegroundColor Yellow
    Write-Host "  Health Check:  http://localhost:5100/health" -ForegroundColor White
    Write-Host "  Departments:   http://localhost:5100/api/v1/departments" -ForegroundColor White
    Write-Host "  Dashboard:     http://localhost:5100/api/v1/dashboard/<dept_id>?date=YYYY-MM-DD" -ForegroundColor White
    Write-Host ""
    Write-Host "Useful commands:" -ForegroundColor Yellow
    Write-Host "  View logs:     docker-compose logs -f bal-agentic-backend" -ForegroundColor White
    Write-Host "  Stop service:  docker-compose down" -ForegroundColor White
    Write-Host "  Restart:       docker-compose restart bal-agentic-backend" -ForegroundColor White
    Write-Host "  Status:        docker-compose ps" -ForegroundColor White
    Write-Host ""
    Write-Host "Container status:" -ForegroundColor Yellow
    docker-compose ps
} else {
    Write-Host "=============================================================================" -ForegroundColor Red
    Write-Host "WARNING: Service started but health check failed" -ForegroundColor Red
    Write-Host "=============================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check logs with: docker-compose logs bal-agentic-backend" -ForegroundColor Yellow
    Write-Host ""
    docker-compose logs --tail=50 bal-agentic-backend
}

Write-Host ""
Write-Host "=============================================================================" ss