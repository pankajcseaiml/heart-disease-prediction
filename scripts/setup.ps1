# PowerShell Automated Setup Script for Heart Disease Early Risk Prediction
$ErrorActionPreference = "Stop"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "HEART DISEASE PREDICTION - POWERSHELL AUTOMATED SETUP" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

# 1. Check Python
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    Write-Error "Python is not installed or not in PATH. Please install Python 3.10+."
    exit 1
}
Write-Host "[+] Python detected: $($PythonCmd.Source)" -ForegroundColor Green

# 2. Virtual Environment
if (-not (Test-Path ".venv")) {
    Write-Host "[*] Creating virtual environment at .venv..." -ForegroundColor Yellow
    python -m venv .venv
}
Write-Host "[+] Activating virtual environment..." -ForegroundColor Green
& ".\.venv\Scripts\Activate.ps1"

# 3. Install packages
Write-Host "[*] Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
python -m pip install -r frontend/requirements.txt
python -m pip install cryptography httpx

# 4. Run Python Setup
Write-Host "[*] Initializing secrets, database, and fixtures..." -ForegroundColor Yellow
python scripts/setup.py

Write-Host "`n[+] SUCCESS: Project is fully configured and ready!" -ForegroundColor Green
Write-Host "To start the application run: .\scripts\run_all.ps1" -ForegroundColor Cyan
