"""Full Artifact Restorer.

Restores database from encrypted backup, generates test datasets,
and verifies model pipelines.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scripts.download_models import verify_models
from scripts.generate_sample_data import generate_all_samples
from scripts.restore_database import main as restore_db_main


def main():
    print("\n" + "=" * 80)
    print("RESTORING ALL PROJECT ARTIFACTS")
    print("=" * 80)

    # 1. Restore Models
    print("[1/3] Verifying and restoring model definitions...")
    if not verify_models():
        print("[!] Model verification failed.", file=sys.stderr)
        sys.exit(1)

    # 2. Restore Datasets & Samples
    print("[2/3] Generating datasets and test fixtures...")
    generate_all_samples()

    # 3. Restore Database if encrypted backup exists
    latest_enc = ROOT_DIR / "backups" / "database" / "heart_disease_backup_latest.db.gz.enc"
    print("[3/3] Checking for database backups...")
    if latest_enc.exists():
        print(f"[*] Restoring database from: {latest_enc.name}")
        restore_db_main()
    else:
        print("[*] No existing backup found; database will initialize on first run.")

    print("\n" + "=" * 80)
    print("[SUCCESS] All artifacts and data restored successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
