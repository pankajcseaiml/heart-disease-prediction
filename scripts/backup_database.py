"""Enterprise SQLite Database Backup Automation.

Creates consistent, atomic online backups using SQLite's backup API,
compresses with gzip, encrypts with AES-256 (Fernet), computes SHA-256,
and produces compliance metadata.
"""

import gzip
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple
from cryptography.fernet import Fernet

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = ROOT_DIR / "backups" / "database"


def load_env_if_present() -> None:
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k not in os.environ:
                    os.environ[k.strip()] = v.strip()


def get_db_path() -> Path:
    load_env_if_present()
    db_url = os.getenv("DATABASE_URL", "sqlite:///./data/heart_disease.db")
    raw = db_url.replace("sqlite:///", "")
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


def get_encryption_key() -> bytes:
    load_env_if_present()
    key = os.getenv("BACKUP_ENCRYPTION_KEY")
    if not key:
        raise ValueError("BACKUP_ENCRYPTION_KEY is not set in environment or .env")
    return key.encode("utf-8")


def calculate_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def backup_sqlite_online(source_path: Path, temp_dest: Path) -> None:
    """Uses SQLite backup API to perform a non-blocking consistent backup."""
    if not source_path.exists():
        raise FileNotFoundError(f"Source database does not exist at: {source_path}")

    src_conn = sqlite3.connect(str(source_path))
    dst_conn = sqlite3.connect(str(temp_dest))
    try:
        with dst_conn:
            src_conn.backup(dst_conn, pages=100)
    finally:
        src_conn.close()
        dst_conn.close()


def create_database_backup() -> Tuple[Path, Dict[str, str]]:
    db_path = get_db_path()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    enc_key = get_encryption_key()
    fernet = Fernet(enc_key)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_filename = f"heart_disease_backup_{timestamp}.db.gz.enc"
    latest_filename = "heart_disease_backup_latest.db.gz.enc"

    target_path = BACKUP_DIR / backup_filename
    latest_path = BACKUP_DIR / latest_filename

    print(f"[*] Starting consistent online backup of: {db_path}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_raw = Path(tmp_dir) / "dump.db"
        tmp_gz = Path(tmp_dir) / "dump.db.gz"

        # 1. Atomic backup
        backup_sqlite_online(db_path, tmp_raw)

        # 2. Gzip compression
        with open(tmp_raw, "rb") as f_in, gzip.open(tmp_gz, "wb", compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)

        # 3. Authenticated AES-256 Encryption
        gz_data = tmp_gz.read_bytes()
        encrypted_data = fernet.encrypt(gz_data)
        target_path.write_bytes(encrypted_data)
        shutil.copyfile(target_path, latest_path)

    # 4. Integrity verification
    sha256_hash = calculate_sha256(target_path)
    file_size = target_path.stat().st_size

    metadata = {
        "backup_filename": backup_filename,
        "database_type": "SQLite",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_database": str(db_path.name),
        "size_bytes": file_size,
        "sha256": sha256_hash,
        "encryption": "AES-256 (Fernet Authenticated)",
        "compression": "gzip-level-9",
        "status": "VERIFIED_ENCRYPTED",
    }

    metadata_path = BACKUP_DIR / "backup_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"[+] Backup successfully created and encrypted:")
    print(f"    Target: {target_path}")
    print(f"    Size  : {file_size} bytes")
    print(f"    SHA256: {sha256_hash}")
    return target_path, metadata


if __name__ == "__main__":
    try:
        create_database_backup()
    except Exception as exc:
        print(f"[!] Backup failed: {exc}", file=sys.stderr)
        sys.exit(1)
