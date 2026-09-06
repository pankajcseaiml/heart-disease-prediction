"""Enterprise Secret Management using KeePassXC.

Automates the creation of a local encrypted KeePassXC (.kdbx) vault,
secure storage of application secrets, local .env generation, and
secret auditing. NEVER displays or logs secret values.
"""

import os
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
from cryptography.fernet import Fernet

KEEPASSXC_CLI_DEFAULT = r"C:\Program Files\KeePassXC\keepassxc-cli.exe"
VAULT_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "secrets" / "heart_disease_vault.kdbx"
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

SECRET_INVENTORY = [
    {
        "variable": "API_SECRET_KEY",
        "purpose": "Backend API authentication and route protection",
        "target_storage": "KeePassXC / Local .env",
        "rotation_required": "NO",
        "status": "MANAGED",
    },
    {
        "variable": "BACKUP_ENCRYPTION_KEY",
        "purpose": "AES-256 (Fernet) encryption key for database dumps & archives",
        "target_storage": "KeePassXC / Local .env",
        "rotation_required": "NO",
        "status": "MANAGED",
    },
    {
        "variable": "DATABASE_URL",
        "purpose": "Connection string for SQLite database persistence",
        "target_storage": "Local .env / KeePassXC",
        "rotation_required": "NO",
        "status": "MANAGED",
    },
    {
        "variable": "RCLONE_REMOTE_NAME",
        "purpose": "Remote target name for Google Drive backups",
        "target_storage": "Local .env",
        "rotation_required": "NO",
        "status": "MANAGED",
    },
]


def find_keepassxc_cli() -> str:
    candidate = os.getenv("KEEPASSXC_CLI", KEEPASSXC_CLI_DEFAULT)
    if Path(candidate).exists():
        return candidate
    import shutil
    which_cli = shutil.which("keepassxc-cli")
    if which_cli:
        return which_cli
    return candidate


def create_vault(vault_path: Path, master_password: str) -> bool:
    """Creates a new KeePassXC .kdbx database non-interactively."""
    cli = find_keepassxc_cli()
    if not Path(cli).exists():
        print(f"[!] KeePassXC CLI not found at: {cli}", file=sys.stderr)
        return False

    vault_path.parent.mkdir(parents=True, exist_ok=True)
    if vault_path.exists():
        print(f"[*] KeePassXC vault already exists at: {vault_path}")
        return True

    cmd = [cli, "db-create", "-p", "-q", str(vault_path)]
    # Feed master password twice via stdin
    input_text = f"{master_password}\n{master_password}\n"
    proc = subprocess.run(cmd, input=input_text, text=True, capture_output=True)
    if proc.returncode == 0:
        print(f"[+] Successfully created KeePassXC vault at: {vault_path}")
        return True
    else:
        print(f"[!] Failed to create KeePassXC vault: {proc.stderr}", file=sys.stderr)
        return False


def store_secret(vault_path: Path, master_password: str, entry_title: str, secret_val: str) -> bool:
    """Adds or updates an entry in the KeePassXC database."""
    cli = find_keepassxc_cli()
    cmd = [cli, "add", "-p", "-q", str(vault_path), entry_title]
    # keepassxc-cli add prompts for:
    # 1. db master password
    # 2. entry password
    # 3. repeat entry password
    input_text = f"{master_password}\n{secret_val}\n{secret_val}\n"
    proc = subprocess.run(cmd, input=input_text, text=True, capture_output=True)
    return proc.returncode == 0


def retrieve_secret(vault_path: Path, master_password: str, entry_title: str) -> Optional[str]:
    """Retrieves secret value programmatically without logging."""
    cli = find_keepassxc_cli()
    cmd = [cli, "show", "-s", "-a", "Password", "-q", str(vault_path), entry_title]
    proc = subprocess.run(cmd, input=f"{master_password}\n", text=True, capture_output=True)
    if proc.returncode == 0:
        return proc.stdout.strip()
    return None


def generate_local_env(
    api_secret: str,
    backup_enc_key: str,
    db_url: str = "sqlite:///./data/heart_disease.db",
    env_file: Path = ENV_PATH,
) -> None:
    """Generates the local .env file securely outside Git."""
    content = f"""# Local Environment Configuration (NEVER COMMIT)
APP_ENV=development
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
API_URL=http://127.0.0.1:8000
API_SECRET_KEY={api_secret}
DATABASE_URL={db_url}
BACKUP_ENCRYPTION_KEY={backup_enc_key}
KEEPASS_DB_PATH=./secrets/heart_disease_vault.kdbx
RCLONE_REMOTE_NAME=gdrive
DRIVE_BACKUP_FOLDER=HeartDiseasePrediction-Backups
"""
    env_file.write_text(content, encoding="utf-8")
    print(f"[+] Successfully generated local .env at: {env_file}")


def print_secret_inventory():
    """Prints compliance secret inventory table WITHOUT revealing secret values."""
    print("\n" + "=" * 80)
    print("ENTERPRISE SECRET INVENTORY AUDIT")
    print("=" * 80)
    for s in SECRET_INVENTORY:
        print(f"VARIABLE NAME          : {s['variable']}")
        print(f"PURPOSE                : {s['purpose']}")
        print(f"TARGET STORAGE         : {s['target_storage']}")
        print(f"ROTATION REQUIRED      : {s['rotation_required']}")
        print(f"STATUS                 : {s['status']}")
        print("-" * 80)


def auto_setup_vault(master_password: Optional[str] = None) -> bool:
    """Initializes vault, generates cryptographically strong keys, and writes .env."""
    if not master_password:
        master_password = os.getenv("KEEPASS_MASTER_PASSWORD")
    if not master_password:
        # Generate a high-entropy session key if not supplied
        master_password = secrets.token_urlsafe(32)
        print("[!] Note: Using generated master password for this session.")

    vault_path = VAULT_DEFAULT_PATH
    success = create_vault(vault_path, master_password)
    if not success:
        print("[!] Falling back to direct local .env generation.")
        api_secret = secrets.token_hex(32)
        backup_key = Fernet.generate_key().decode("utf-8")
        generate_local_env(api_secret, backup_key)
        return False

    api_secret = secrets.token_hex(32)
    backup_key = Fernet.generate_key().decode("utf-8")

    store_secret(vault_path, master_password, "API_SECRET_KEY", api_secret)
    store_secret(vault_path, master_password, "BACKUP_ENCRYPTION_KEY", backup_key)
    store_secret(vault_path, master_password, "DATABASE_URL", "sqlite:///./data/heart_disease.db")

    generate_local_env(api_secret, backup_key)
    print("[+] KeePassXC vault and local .env initialized securely.")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="KeePassXC Enterprise Secret Manager")
    parser.add_argument("action", choices=["setup", "inventory", "env"], default="inventory", nargs="?")
    parser.add_argument("--password", help="KeePassXC master password")
    args = parser.parse_args()

    if args.action == "inventory":
        print_secret_inventory()
    elif args.action == "setup":
        auto_setup_vault(args.password)
        print_secret_inventory()
    elif args.action == "env":
        api_secret = secrets.token_hex(32)
        backup_key = Fernet.generate_key().decode("utf-8")
        generate_local_env(api_secret, backup_key)


if __name__ == "__main__":
    main()
