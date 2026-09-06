# Enterprise Secret Management Guide (KeePassXC & Local .env)

## Overview
This project strictly enforces **Zero Secret Exposure in Version Control**:
- Secrets are **never** committed to Git, even in private repositories.
- Secrets are managed locally in encrypted KeePassXC (`.kdbx`) vaults and injected at runtime via local `.env`.
- `.env` and `secrets/` are strictly ignored by `.gitignore`.

---

## Secret Inventory

| Variable Name | Purpose | Target Storage | Rotation Required | Format |
|---|---|---|---|---|
| `API_SECRET_KEY` | Backend API token & endpoint protection | KeePassXC / Local `.env` | No | 32-byte hex token |
| `BACKUP_ENCRYPTION_KEY` | AES-256 (Fernet) key for database & archive dumps | KeePassXC / Local `.env` | No | 32-byte urlsafe base64 key |
| `DATABASE_URL` | SQLite database URI | Local `.env` | No | `sqlite:///./data/heart_disease.db` |
| `RCLONE_REMOTE_NAME` | Google Drive remote target | Local `.env` | No | String (`gdrive`) |
| `RCLONE_BACKUP_DIR` | Backup directory name on Google Drive | Local `.env` | No | String (`HeartDiseasePrediction-Backups`) |

---

## KeePassXC Vault Setup

### Automated Setup
```powershell
python scripts/manage_secrets.py setup
```
This command:
1. Creates `secrets/heart_disease_vault.kdbx` using `keepassxc-cli`.
2. Generates cryptographically secure keys for `API_SECRET_KEY` and `BACKUP_ENCRYPTION_KEY`.
3. Writes a local `.env` configuration file outside Git.

### Inspect Secret Inventory
To audit the secret inventory without revealing plaintext secret values:
```powershell
python scripts/manage_secrets.py inventory
```

### Rotating Secrets
If an encryption key or API token needs rotation:
1. Generate a new key:
```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode('utf-8'))"
```
2. Update `.env` and KeePassXC vault.
3. Re-encrypt the latest database backup with the new key.
4. Run `python scripts/verify_database_backup.py` to confirm the new key decrypts cleanly.
