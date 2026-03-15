<#
  setup.ps1 - bootstraps local dev for PhishDefense
  Usage:
    .\setup.ps1 run        # Full bootstrap then run uvicorn
    .\setup.ps1 migrate    # Run alembic upgrade head
    .\setup.ps1 up         # Only docker compose up -d
#>

param(
    [ValidateSet('run', 'migrate', 'up')]
    [string]$Action = 'run'
)

$ErrorActionPreference = 'Stop'
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT

function Ensure-Venv {
    if (-not (Test-Path "$ROOT\.venv\Scripts\python.exe")) {
        Write-Host "Creating virtual environment..." -ForegroundColor Cyan
        python -m venv .venv
    }
    & "$ROOT\.venv\Scripts\Activate.ps1"
}

function Install-Requirements {
    Write-Host "Installing requirements..." -ForegroundColor Cyan
    pip install --upgrade pip
    pip install -r requirements.txt
}

function Docker-Up {
    Write-Host "Starting Docker services..." -ForegroundColor Cyan
    docker compose up -d
}

function Wait-Postgres {
    Write-Host "Waiting for Postgres to be healthy..." -ForegroundColor Cyan
    $max = 40
    for ($i = 0; $i -lt $max; $i++) {
        $state = (docker inspect -f "{{.State.Health.Status}}" phish_db 2>$null)
        if ($state -eq "healthy") {
            Write-Host "Postgres is healthy." -ForegroundColor Green
            return
        }
        Start-Sleep -Seconds 2
    }
    throw "Postgres did not become healthy in time."
}

function Alembic-Upgrade {
    Write-Host "Running alembic upgrade head..." -ForegroundColor Cyan
    python -m alembic upgrade head
}

function Run-Uvicorn {
    Write-Host "Starting uvicorn (http://localhost:8000)..." -ForegroundColor Cyan
    uvicorn app.main:app --reload --port 8000
}

if ($Action -eq 'up') {
    Docker-Up
    exit 0
}

Ensure-Venv
Install-Requirements
Docker-Up
Wait-Postgres

if ($Action -eq 'migrate') {
    Alembic-Upgrade
    exit 0
}

# default 'run'
Alembic-Upgrade
Run-Uvicorn