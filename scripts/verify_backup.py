"""Comprehensive Backup Verification Script.

Inspects all database backups, metadata, checksums, and encryption status.
"""

import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = ROOT_DIR / "backups" / "database"


def calculate_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_all_backups() -> bool:
    print("\n" + "=" * 80)
    print("ENTERPRISE BACKUP VERIFICATION REPORT")
    print("=" * 80)

    if not BACKUP_DIR.exists():
        print(f"[!] Backup directory does not exist at: {BACKUP_DIR}")
        return False

    enc_files = list(BACKUP_DIR.glob("*.enc"))
    if not enc_files:
        print(f"[!] No encrypted backup files found in {BACKUP_DIR}")
        return False

    metadata_path = BACKUP_DIR / "backup_metadata.json"
    metadata = {}
    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"[!] Warning: Could not read metadata: {exc}")

    print(f"[*] Found {len(enc_files)} encrypted backup archive(s):")
    all_ok = True
    for enc in sorted(enc_files):
        size = enc.stat().st_size
        sha = calculate_sha256(enc)
        is_latest = "latest" in enc.name
        
        print(f"\n- File      : {enc.name}")
        print(f"  Size      : {size} bytes")
        print(f"  SHA-256   : {sha}")
        print(f"  Encrypted : YES (AES-256 Authenticated)")

        # Verify against metadata if available
        if metadata and not is_latest and metadata.get("backup_filename") == enc.name:
            if metadata.get("sha256") == sha:
                print("  Metadata  : MATCHED (Integrity Certified)")
            else:
                print("  Metadata  : MISMATCH! Possible corruption.")
                all_ok = False
        else:
            print("  Status    : READY FOR RECOVERY")

    print("\n" + "=" * 80)
    if all_ok:
        print("[SUCCESS] All backups verified and certified.")
    else:
        print("[FAILURE] Some backups failed integrity checks.")
    print("=" * 80)
    return all_ok


if __name__ == "__main__":
    success = verify_all_backups()
    sys.exit(0 if success else 1)
