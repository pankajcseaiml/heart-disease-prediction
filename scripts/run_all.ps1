# Heart Disease Early Risk Prediction - Launch Backend and Frontend
$ErrorActionPreference = "Stop"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "STARTING HEART DISEASE RISK PREDICTION SYSTEM" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# 1. Activate Python Environment
$PythonExe = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

# 2. Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[!] No .env found. Initializing local secrets..." -ForegroundColor Yellow
    & $PythonExe scripts/manage_secrets.py setup
}

Write-Host "[*] Starting FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
$BackendJob = Start-Process -FilePath $PythonExe -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload" -WorkingDirectory "$PSScriptRoot\..\backend" -PassThru

Write-Host "[*] Starting Streamlit Frontend on http://localhost:8501 ..." -ForegroundColor Green
Start-Process -FilePath $PythonExe -ArgumentList "-m streamlit run app.py" -WorkingDirectory "$PSScriptRoot\..\frontend"

Write-Host "`n[+] System started successfully!" -ForegroundColor Green
Write-Host "    Backend API Docs : http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "    Frontend UI      : http://localhost:8501" -ForegroundColor Cyan
