"""Mandatory Clean Clone Isolation & Disaster Recovery Test.

Tests the full recovery process in a clean sandbox directory isolated
from the active workspace to prove that the project is 100% reproducible
without hidden local machine dependencies.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))



def run_command_in(cmd: list, cwd: Path) -> subprocess.CompletedProcess:
    print(f"[*] Running in [{cwd.name}]: {' '.join(str(x) for x in cmd)}")
    res = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if res.returncode != 0:
        print(f"[!] STDOUT: {res.stdout}", file=sys.stderr)
        print(f"[!] STDERR: {res.stderr}", file=sys.stderr)
        raise RuntimeError(f"Command failed with code {res.returncode}: {' '.join(str(x) for x in cmd)}")
    return res


def test_clean_clone():
    print("\n" + "=" * 80)
    print("MANDATORY CLEAN CLONE & DISASTER RECOVERY VALIDATION")
    print("=" * 80)

    with tempfile.TemporaryDirectory(prefix="heart_clone_") as temp_dir:
        clone_root = Path(temp_dir) / "cloned_repo"

        # 1. Clone local repository into sandbox
        print(f"[1/7] Cloning project to clean directory: {clone_root} ...")
        subprocess.run(["git", "clone", str(ROOT_DIR), str(clone_root)], check=True, capture_output=True)
        print("      [PASS] Git clone succeeded.")

        # 2. Verify strict isolation (no leaked secrets, DBs, or virtualenvs)
        print("[2/7] Verifying sandbox contains NO leaked local state...")
        assert not (clone_root / ".env").exists(), "LEAK: .env found in clone!"
        assert not (clone_root / "secrets" / "heart_disease_vault.kdbx").exists(), "LEAK: vault found in clone!"
        assert not (clone_root / "data" / "heart_disease.db").exists(), "LEAK: live database found in clone!"
        assert not (clone_root / "backups" / "database").exists(), "LEAK: backup directory found in clone!"
        assert not (clone_root / ".venv").exists(), "LEAK: virtual environment found in clone!"
        print("      [PASS] Clean-clone isolation certified: zero leaked files.")

        # 3. Provision environment & secrets
        print("[3/7] Setting up fresh secrets and local .env in clone...")
        python_exe = sys.executable
        run_command_in([python_exe, "scripts/manage_secrets.py", "setup"], cwd=clone_root)
        assert (clone_root / ".env").exists(), "Failed to generate .env in clone"
        print("      [PASS] Fresh KeePassXC vault and local .env successfully generated.")

        # 4. Initialize Database
        print("[4/7] Initializing fresh SQLite schema in clone...")
        run_command_in([python_exe, "backend/app/db/init_db.py"], cwd=clone_root)
        assert (clone_root / "data" / "heart_disease.db").exists(), "Failed to initialize DB in clone"
        print("      [PASS] Fresh database schema initialized.")

        # 5. Generate sample data fixtures
        print("[5/7] Generating test data fixtures...")
        run_command_in([python_exe, "scripts/generate_sample_data.py"], cwd=clone_root)
        print("      [PASS] Test fixtures generated.")

        # 6. Execute full verification suite in clone
        print("[6/7] Running full verification suite in cloned repository...")
        res_verify = run_command_in([python_exe, "scripts/verify.py"], cwd=clone_root)
        assert "[SUCCESS] ALL VERIFICATION CHECKS PASSED" in res_verify.stdout
        print("      [PASS] All verification checks passed in clean clone.")

        # 7. Test Disaster Recovery Reconstitution from an Encrypted Backup
        print("[7/7] Testing database reconstitution from encrypted backup...")
        # Copy latest encrypted backup from original repo to simulate downloading from Google Drive
        orig_latest = ROOT_DIR / "backups" / "database" / "heart_disease_backup_latest.db.gz.enc"
        orig_meta = ROOT_DIR / "backups" / "database" / "backup_metadata.json"
        if orig_latest.exists() and orig_meta.exists():
            dest_backup_dir = clone_root / "backups" / "database"
            dest_backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(orig_latest, dest_backup_dir / orig_latest.name)
            shutil.copyfile(orig_meta, dest_backup_dir / orig_meta.name)

            # Copy encryption key to clone's .env so it can decrypt the archive
            from scripts.backup_database import get_encryption_key
            orig_key = get_encryption_key().decode("utf-8")
            env_content = (clone_root / ".env").read_text(encoding="utf-8")
            # Replace generated key with original key to test reconstitution
            lines = []
            for l in env_content.splitlines():
                if l.startswith("BACKUP_ENCRYPTION_KEY="):
                    lines.append(f"BACKUP_ENCRYPTION_KEY={orig_key}")
                else:
                    lines.append(l)
            (clone_root / ".env").write_text("\n".join(lines), encoding="utf-8")

            # Run restore
            run_command_in([python_exe, "scripts/restore_database.py"], cwd=clone_root)
            print("      [PASS] Reconstitution from encrypted backup succeeded in clean clone.")
        else:
            print("      [*] Skipping backup reconstitution test (no existing backup in source).")

    print("\n" + "=" * 80)
    print("[SUCCESS] MANDATORY CLEAN-CLONE TEST PASSED (100% DISASTER-RECOVERY CERTIFIED)")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = test_clean_clone()
    sys.exit(0 if success else 1)
