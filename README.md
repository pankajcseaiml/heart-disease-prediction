# Heart Disease Early Risk Prediction (Enterprise-Grade)

An enterprise-ready multimodal decision support system combining Chest X-ray image analysis and multi-parameter clinical data to estimate heart disease risk.

---

## Key Features
- **Multimodal AI Architecture**: Blends thoracic radiograph opacity metrics and normalized clinical indicators.
- **Explainability**: Intensity-based saliency heatmaps highlighting thoracic opacity, plus key driver feature attribution.
- **Persistent Audit Logging**: SQLite database in WAL mode logging risk percentages, categories, confidence, and timestamps.
- **Enterprise Secret Management**: Zero secret exposure in Git. KeePassXC (`.kdbx`) encrypted storage with local `.env` generation.
- **Encrypted Backups & Disaster Recovery**: Online non-blocking database backups, AES-256 (Fernet) authenticated encryption, SHA-256 integrity verification, and automated Google Drive synchronization via `rclone`.
- **Reproducible Zero-Configuration Setup**: Single-command provisioning, dependency installation, and end-to-end self-testing.

---

## Target Architecture

```text
                         ┌──────────────────────────────┐
                         │       PRIVATE GITHUB         │
                         │                              │
                         │ Source Code (Backend/Frontend│
                         │ Schema & Migrations          │
                         │ Automated Scripts & Tests    │
                         │ .env.example (Safe template) │
                         │ Documentation & Runbooks     │
                         └──────────────┬───────────────┘
                                        │
                                  git clone / pull
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │      NEW LOCAL MACHINE       │
                         │                              │
                         │ Development Environment      │
                         │ Dependencies (Python 3.10+)  │
                         │ App (FastAPI + Streamlit)    │
                         └───────┬────────┬─────────────┘
                                 │        │
                    ┌────────────┘        └───────────────┐
                    ▼                                     ▼
       ┌────────────────────────┐             ┌────────────────────────┐
       │   SECURE SECRET        │             │   EXTERNAL STORAGE     │
       │       STORAGE          │             │                        │
       │ KeePassXC (.kdbx)      │             │ Google Drive (rclone)  │
       │ API Keys & Tokens      │             │ Encrypted DB Backups   │
       │ App Secret Keys        │             │ Encrypted Archives     │
       │ Encryption Master Keys │             │ Checksums (SHA-256)    │
       │ Local .env Generation  │             │ Disaster Recovery Kits │
       └────────────────────────┘             └────────────────────────┘
```

---

## Quick Start (Automated)

### 1. One-Click Setup
```powershell
# In Windows PowerShell:
.\scripts\setup.ps1

# Or cross-platform via Python:
python scripts/setup.py
```
This automatically:
1. Validates Python 3.10+ prerequisites.
2. Creates virtual environment and installs dependencies.
3. Generates KeePassXC vault and local `.env` with strong random keys.
4. Initializes the SQLite database schema in `data/heart_disease.db`.
5. Generates synthetic test fixtures (X-ray images & clinical samples).

### 2. Launch Services
```powershell
.\scripts\run_all.ps1
```
- **Backend API**: `http://127.0.0.1:8000` (Docs: `http://127.0.0.1:8000/docs`)
- **Frontend App**: `http://localhost:8501`

---

## Manual Execution

### 1. Run Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check:
```powershell
curl http://127.0.0.1:8000/health
```

### 2. Run Frontend
In a separate terminal:
```powershell
cd frontend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

---

## API Specification

### `POST /predict` (Multipart Form Data)
- **`xray`**: Image file (`png`, `jpg`, `jpeg`).
- **`clinical_data`**: JSON string containing:
  - `age` (18-100)
  - `systolic_bp` (80-220)
  - `cholesterol` (100-400)
  - `fasting_blood_sugar` (70-250)
  - `ecg_abnormality` (0 or 1)
  - `bmi` (12.0-60.0)
  - `smoking` (0 or 1)
  - `physical_inactivity` (0 or 1)
  - `family_history` (0 or 1)

**Response**:
```json
{
  "risk_percentage": 65.08,
  "risk_category": "Medium",
  "confidence": 0.651,
  "feature_importance": [
    {"feature": "systolic_bp", "contribution": 0.06},
    {"feature": "cholesterol", "contribution": 0.048}
  ],
  "clinical_score": 0.52,
  "image_score": 0.831,
  "fusion_score": 0.6508,
  "explanation": "Predicted Medium risk. Key drivers: systolic_bp, cholesterol. X-ray analysis contributed strong evidence.",
  "heatmap_image_base64": "...",
  "normalized_inputs": {"age": 0.6098, "cholesterol": 0.7}
}
```

### `GET /history`
Returns recent prediction records stored in SQLite database.

---

## Backup & Disaster Recovery Automation

### 1. Create Encrypted Database Backup
```powershell
python scripts/backup_database.py
```
- Creates an online snapshot of `data/heart_disease.db`.
- Compresses with gzip.
- Encrypts with AES-256 (Fernet) using `BACKUP_ENCRYPTION_KEY`.
- Generates SHA-256 checksum and metadata in `backups/database/backup_metadata.json`.

### 2. Verify Backup & Isolated Restoration Test
```powershell
python scripts/verify_database_backup.py
```
- Seeds a canary record.
- Takes encrypted backup.
- Restores in an isolated sandbox.
- Runs `PRAGMA integrity_check;` and asserts 100% data fidelity.

### 3. Sync to Google Drive
```powershell
python scripts/backup_to_drive.py
```
- Syncs encrypted backups to `Google Drive:HeartDiseasePrediction-Backups/` using `rclone`.

### 4. Restore from Google Drive
```powershell
python scripts/restore_from_drive.py
python scripts/restore_database.py
```

### 5. Full Reconstitution Guide
For the complete 25-step protocol to rebuild on a brand-new machine, see [docs/DISASTER_RECOVERY.md](docs/DISASTER_RECOVERY.md).

---

## Secret Management (KeePassXC)
All sensitive secrets (`API_SECRET_KEY`, `BACKUP_ENCRYPTION_KEY`) are managed via KeePassXC:
- See [docs/SECRET_MANAGEMENT.md](docs/SECRET_MANAGEMENT.md)
- Audit secret inventory without revealing values:
  ```powershell
  python scripts/manage_secrets.py inventory
  ```

---

## System Verification Suite
Run the full verification suite anytime:
```powershell
python scripts/verify.py
```
Verifies:
1. Secret & Git history scanning (certifies 0 leaked credentials).
2. API health and prediction pipeline.
3. Database persistence and query retrieval.
4. Online backup, AES-256 encryption, and isolated sandbox restore.
5. Mathematical sanity of risk scoring models.

---

## Important Clinical Note
This baseline implementation provides a **workable full-stack prototype** for demonstration and decision-support integration. It is not a certified medical device and must be clinically validated before diagnostic use.
