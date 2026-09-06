# Disaster Recovery & Clean Environment Reconstitution Runbook

## Objective
Enable complete recovery of the **Heart Disease Early Risk Prediction System** on a brand-new, clean laptop or server in the event the current development machine is lost, stolen, or destroyed.

---

## Prerequisites Available in Target Architecture
1. Access to the private GitHub repository: `https://github.com/pankajcseaiml/heart-disease-prediction`
2. KeePassXC secret database (`heart_disease_vault.kdbx`) or Master Password.
3. Google Drive encrypted backup folder: `HeartDiseasePrediction-Backups/`
4. Base tools: Python 3.10+, Git, KeePassXC (optional desktop/CLI), Rclone (optional).

---

## 25-Step Disaster Recovery Procedure

### Step 1: Initialize New Machine
- Ensure Windows, Linux, or macOS environment has Python 3.10+ installed and accessible via `PATH`.
- Ensure Git is installed (`git --version`).

### Step 2: Clone Private GitHub Repository
```bash
git clone https://github.com/pankajcseaiml/heart-disease-prediction.git
cd heart-disease-prediction
```

### Step 3: Verify Clean Git Status
```bash
git status
# Confirm on branch main, working tree clean
```

### Step 4: Create Isolated Virtual Environment
```bash
# On Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# On Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 5: Install Python Prerequisites
```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
pip install cryptography httpx
```

### Step 6: Configure Secret Storage (KeePassXC)
- If you have your `heart_disease_vault.kdbx` file from secure external storage, place it in `secrets/heart_disease_vault.kdbx`.
- Open KeePassXC and verify keys:
  - `API_SECRET_KEY`
  - `BACKUP_ENCRYPTION_KEY`
  - `DATABASE_URL`

### Step 7: Generate Local `.env`
- Either export from KeePassXC using `scripts/manage_secrets.py`:
```bash
python scripts/manage_secrets.py setup
```
- Or copy `.env.example` to `.env` and fill in secrets:
```bash
cp .env.example .env
```

### Step 8: Verify Secret Storage Protection
```bash
git status
# CRITICAL: Confirm .env and secrets/ are NOT tracked
```

### Step 9: Configure Google Drive Access via Rclone
- If rclone is not yet configured:
```bash
rclone config
# Name: gdrive, Type: drive
```

### Step 10: Download Encrypted Database Backups from Google Drive
```bash
python scripts/restore_from_drive.py
# Or manually:
# rclone copy gdrive:HeartDiseasePrediction-Backups/database backups/database
```

### Step 11: Verify Encrypted Backup Checksum & Integrity
```bash
python scripts/verify_backup.py
# Confirms file exists, SHA-256 matches metadata, and AES-256 headers are intact
```

### Step 12: Decrypt and Restore Primary Database
```bash
python scripts/restore_database.py
# Restores backups/database/heart_disease_backup_latest.db.gz.enc to data/heart_disease.db
```

### Step 13: Run SQLite PRAGMA Integrity Check
```bash
python -c "import sqlite3; conn = sqlite3.connect('data/heart_disease.db'); print(conn.execute('PRAGMA integrity_check;').fetchall()); conn.close()"
# Expected: [('ok',)]
```

### Step 14: Initialize Schema and Validate Table Records
```bash
python backend/app/db/init_db.py
```

### Step 15: Generate Sample Data and Test Fixtures
```bash
python scripts/generate_sample_data.py
```

### Step 16: Verify Model Definitions and Logic
```bash
python scripts/download_models.py
```

### Step 17: Run Secret & History Scan
```bash
python scripts/scan_secrets.py
# Certify 0 exposed secrets
```

### Step 18: Execute Full Automated Test Suite
```bash
python scripts/verify.py
# Verifies health check, prediction pipeline, database persistence, and backup restoration
```

### Step 19: Start FastAPI Backend Service
```powershell
cd backend
..\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 20: Test Backend Health Check
```bash
curl http://127.0.0.1:8000/health
# Expected: {"status":"ok","service":"heart-disease-prediction-api"}
```

### Step 21: Test Prediction Endpoint via API
```powershell
python -c "import requests, json; r = requests.post('http://127.0.0.1:8000/predict', files={'xray': open('data/sample_data/sample_normal_xray.png', 'rb')}, data={'clinical_data': json.dumps({'age': 45, 'systolic_bp': 130, 'cholesterol': 200, 'fasting_blood_sugar': 110, 'ecg_abnormality': 0, 'bmi': 25.0, 'smoking': 0, 'physical_inactivity': 0, 'family_history': 0})}); print(r.json())"
```

### Step 22: Start Streamlit Frontend
In a separate terminal:
```powershell
cd frontend
..\.venv\Scripts\streamlit run app.py
```

### Step 23: Verify UI in Browser
- Open `http://localhost:8501`
- Test uploading `data/sample_data/sample_normal_xray.png`
- Click **Predict Risk**
- Verify metrics, heatmap overlay, feature importance, and component scores.

### Step 24: Test Online Backup from Restored System
```bash
python scripts/backup_database.py
python scripts/verify_database_backup.py
```

### Step 25: Disaster Recovery Certification
If Steps 1 through 24 complete without errors, the project is officially certified as **Fully Reconstituted**. The previous machine copy can now be safely removed.
