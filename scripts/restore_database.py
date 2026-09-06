"""Enterprise SQLite Database Restoration Automation.

Decrypts AES-256 encrypted backups, decompresses gzip archive,
restores SQLite database to target destination, and runs PRAGMA integrity checks.
"""

import gzip
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Optional
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


def get_encryption_key() -> bytes:
    load_env_if_present()
    key = os.getenv("BACKUP_ENCRYPTION_KEY")
    if not key:
        raise ValueError("BACKUP_ENCRYPTION_KEY is not set in environment or .env")
    return key.encode("utf-8")


def restore_database(
    encrypted_backup_path: Path,
    target_db_path: Path,
    expected_sha256: Optional[str] = None,
) -> bool:
    print(f"[*] Restoring from encrypted backup: {encrypted_backup_path}")
    print(f"    Target database: {target_db_path}")

    if not encrypted_backup_path.exists():
        raise FileNotFoundError(f"Backup file not found at: {encrypted_backup_path}")

    # 1. Verify checksum if provided
    if expected_sha256:
        h = hashlib.sha256()
        with open(encrypted_backup_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        actual_sha256 = h.hexdigest()
        if actual_sha256.lower() != expected_sha256.lower():
            raise ValueError(f"Checksum mismatch! Expected: {expected_sha256}, Actual: {actual_sha256}")
        print("[+] SHA-256 integrity checksum verified.")

    # 2. Decrypt
    enc_key = get_encryption_key()
    fernet = Fernet(enc_key)
    encrypted_bytes = encrypted_backup_path.read_bytes()
    try:
        compressed_bytes = fernet.decrypt(encrypted_bytes)
    except Exception as exc:
        raise ValueError("Decryption failed! Invalid encryption key or corrupted backup.") from exc

    # 3. Decompress and write to target
    target_db_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_db = Path(tmp_dir) / "restored.db"
        decompressed_bytes = gzip.decompress(compressed_bytes)
        tmp_db.write_bytes(decompressed_bytes)

        # 4. PRAGMA integrity check before moving into place
        conn = sqlite3.connect(str(tmp_db))
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        res = cursor.fetchone()
        conn.close()

        if not res or res[0].lower() != "ok":
            raise ValueError(f"SQLite integrity check failed: {res}")
        print("[+] SQLite PRAGMA integrity check passed: OK")

        # Copy into place
        shutil.copyfile(tmp_db, target_db_path)

    print(f"[+] Database successfully restored to: {target_db_path}")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Restore database from encrypted backup")
    parser.add_argument("--backup", help="Path to encrypted .enc backup file")
    parser.add_argument("--target", help="Path to destination SQLite database file")
    args = parser.parse_args()

    load_env_if_present()
    backup_file = Path(args.backup) if args.backup else (BACKUP_DIR / "heart_disease_backup_latest.db.gz.enc")
    target_file = Path(args.target) if args.target else (ROOT_DIR / "data" / "heart_disease.db")

    metadata_file = BACKUP_DIR / "backup_metadata.json"
    expected_sha = None
    if metadata_file.exists():
        try:
            meta = json.loads(metadata_file.read_text(encoding="utf-8"))
            expected_sha = meta.get("sha256")
        except Exception:
            pass

    restore_database(backup_file, target_file, expected_sha)


if __name__ == "__main__":
    main()
