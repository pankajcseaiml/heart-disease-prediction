"""Automated Project Setup and Environment Provisioning.

Provisions the development environment, installs dependencies,
initializes the SQLite database, configures local secrets / .env,
and generates test fixtures for a complete zero-configuration boot.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def run_cmd(cmd: list, cwd: Path = ROOT_DIR) -> bool:
    print(f"[*] Running: {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=cwd)
    return proc.returncode == 0


def check_prerequisites():
    print("[1/6] Checking system prerequisites...")
    if sys.version_info < (3, 10):
        print(f"[!] Python 3.10+ required. Current version: {sys.version}", file=sys.stderr)
        sys.exit(1)
    print(f"[+] Python {sys.version.split()[0]} verified.")


def install_dependencies():
    print("[2/6] Installing backend and frontend dependencies...")
    python_bin = sys.executable
    run_cmd([python_bin, "-m", "pip", "install", "--upgrade", "pip"])
    run_cmd([python_bin, "-m", "pip", "install", "-r", "backend/requirements.txt"])
    run_cmd([python_bin, "-m", "pip", "install", "-r", "frontend/requirements.txt"])
    run_cmd([python_bin, "-m", "pip", "install", "cryptography>=42.0.0", "httpx>=0.27.0"])


def setup_secrets():
    print("[3/6] Configuring local secrets and .env...")
    python_bin = sys.executable
    run_cmd([python_bin, "scripts/manage_secrets.py", "setup"])


def setup_database():
    print("[4/6] Initializing database schema...")
    python_bin = sys.executable
    run_cmd([python_bin, "backend/app/db/init_db.py"])


def generate_fixtures():
    print("[5/6] Generating sample test data fixtures...")
    python_bin = sys.executable
    run_cmd([python_bin, "scripts/generate_sample_data.py"])


def run_self_test():
    print("[6/6] Executing quick verification test...")
    python_bin = sys.executable
    run_cmd([python_bin, "scripts/verify.py"])


def main():
    print("\n" + "=" * 80)
    print("HEART DISEASE EARLY RISK PREDICTION - AUTOMATED SETUP")
    print("=" * 80)
    check_prerequisites()
    install_dependencies()
    setup_secrets()
    setup_database()
    generate_fixtures()
    print("\n[+] Setup complete! You can run the application with:")
    print("    powershell -File scripts/run_all.ps1")
    print("=" * 80)


if __name__ == "__main__":
    main()
