# API Contract Studio Windows PowerShell development helper

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

switch ($Command) {
    "setup" {
        Write-Host "Setting up Python virtual environment and dependencies..." -ForegroundColor Cyan
        uv venv --python 3.12 .venv
        uv pip install -e ".[api,dev]"
        uv pip install email-validator
        cd apps/web
        npm install --ignore-scripts
        cd ../..
    }
    "test" {
        Write-Host "Running test suite..." -ForegroundColor Cyan
        uv run pytest -v
    }
    "api" {
        Write-Host "Starting API backend..." -ForegroundColor Cyan
        uv run uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000 --reload
    }
    "web" {
        Write-Host "Starting Next.js frontend..." -ForegroundColor Cyan
        cd apps/web
        npm run dev
    }
    "migrate" {
        Write-Host "Applying database migrations..." -ForegroundColor Cyan
        uv run alembic upgrade head
    }
    "build" {
        Write-Host "Building web assets..." -ForegroundColor Cyan
        cd apps/web
        npm run build
    }
    Default {
        Write-Host "API Contract Studio PowerShell Helper" -ForegroundColor Green
        Write-Host "Usage: .\scripts\dev.ps1 [setup|test|api|web|migrate|build]"
    }
}
