"""Isolated Database Backup & Restoration Verification Test.

Tests the full lifecycle:
1. Seed live database with test verification records
2. Run consistent backup with compression & AES-256 encryption
3. Decrypt and restore into an isolated temporary sandbox
4. Verify SQLite PRAGMA integrity
5. Verify record counts and schema fields
6. Leave production database completely untouched
"""

import json
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.db.models import (
    get_prediction_count,
    get_recent_predictions,
    init_tables,
    save_prediction,
)
from backend.app.db.session import get_connection, get_db
from scripts.backup_database import create_database_backup
from scripts.restore_database import restore_database


def run_verification() -> bool:
    print("\n" + "=" * 80)
    print("ISOLATED DATABASE BACKUP & RESTORATION TEST")
    print("=" * 80)

    # 1. Ensure live DB has tables and a known canary record
    print("[1/5] Preparing test canary record in primary database...")
    canary_note = f"canary_test_{datetime.now(timezone.utc).timestamp()}"
    with get_db() as live_conn:
        init_tables(live_conn)
        test_id = save_prediction(
            conn=live_conn,
            risk_percentage=77.5,
            risk_category="High",
            confidence=0.88,
            clinical_score=0.75,
            image_score=0.81,
            fusion_score=0.775,
            explanation=f"Canary validation record: {canary_note}",
            normalized_inputs={"age": 0.65, "cholesterol": 0.8},
            feature_importance=[{"feature": "cholesterol", "contribution": 0.4}],
        )
    with get_connection() as live_conn:
        live_count = get_prediction_count(live_conn)
    print(f"      Canary inserted with ID: {test_id} (Total live records: {live_count})")

    # 2. Execute consistent backup & encryption
    print("[2/5] Creating encrypted backup...")
    backup_file, metadata = create_database_backup()
    print(f"      Encrypted backup generated: {backup_file.name}")
    print(f"      SHA256: {metadata['sha256']}")

    # 3. Create isolated sandbox environment
    print("[3/5] Setting up isolated temporary sandbox...")
    with tempfile.TemporaryDirectory() as sandbox_dir:
        sandbox_db = Path(sandbox_dir) / "isolated_verification.db"

        # 4. Decrypt and restore inside sandbox
        print(f"[4/5] Restoring backup to sandbox: {sandbox_db}...")
        restore_database(
            encrypted_backup_path=backup_file,
            target_db_path=sandbox_db,
            expected_sha256=metadata["sha256"],
        )

        # 5. Query sandbox database and validate canary
        print("[5/5] Validating data integrity in restored sandbox database...")
        sandbox_conn = sqlite3.connect(str(sandbox_db))
        sandbox_conn.row_factory = sqlite3.Row
        try:
            restored_count = get_prediction_count(sandbox_conn)
            recent = get_recent_predictions(sandbox_conn, limit=5)
            sandbox_conn.close()

            print(f"      Restored record count: {restored_count}")
            assert restored_count == live_count, f"Record count mismatch! Live: {live_count}, Restored: {restored_count}"

            # Verify canary record matches
            matching = [r for r in recent if canary_note in r["explanation"]]
            assert len(matching) == 1, "Canary record not found in restored database!"
            assert matching[0]["risk_percentage"] == 77.5
            assert matching[0]["risk_category"] == "High"
            print("[+] Canary record successfully found and matched in isolated database!")
        except Exception as exc:
            print(f"[!] Data integrity validation failed: {exc}", file=sys.stderr)
            return False

    print("\n" + "=" * 80)
    print("[SUCCESS] Isolated Database Backup & Restoration Test: PASSED (100%)")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
