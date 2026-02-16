# RAG Agent Startup Script
# This script helps you start all components in the correct order

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "RAG Agent Startup Helper" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path "backend\.env")) {
    Write-Host "ERROR: .env file not found in backend folder!" -ForegroundColor Red
    Write-Host "Please create backend\.env and add your API key" -ForegroundColor Yellow
    exit 1
}

Write-Host "Choose what to start:" -ForegroundColor Green
Write-Host "1. Start Qdrant (Docker)" -ForegroundColor White
Write-Host "2. Start Backend (FastAPI)" -ForegroundColor White
Write-Host "3. Start Frontend (React)" -ForegroundColor White
Write-Host "4. Run Setup Check" -ForegroundColor White
Write-Host "5. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-5)"

switch ($choice) {
    "1" {
        Write-Host "`nStarting Qdrant with Docker..." -ForegroundColor Yellow
        Write-Host "Access Qdrant Dashboard at: http://localhost:6333/dashboard" -ForegroundColor Cyan
        docker run -p 6333:6333 qdrant/qdrant
    }
    "2" {
        Write-Host "`nStarting FastAPI Backend..." -ForegroundColor Yellow
        Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "API Docs at: http://localhost:8000/docs" -ForegroundColor Cyan
        Set-Location backend
        python main.py
    }
    "3" {
        Write-Host "`nStarting React Frontend..." -ForegroundColor Yellow
        Write-Host "Frontend will be available at: http://localhost:5173" -ForegroundColor Cyan
        Set-Location frontend
        npm run dev
    }
    "4" {
        Write-Host "`nRunning setup check..." -ForegroundColor Yellow
        Set-Location backend
        python setup_check.py
        Write-Host "`nPress any key to continue..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    "5" {
        Write-Host "`nExiting..." -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "`nInvalid choice. Exiting..." -ForegroundColor Red
        exit 1
    }
}
