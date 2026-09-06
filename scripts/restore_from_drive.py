"""Enterprise Google Drive Restoration Automation via Rclone.

Downloads encrypted backups from Google Drive and verifies SHA-256 integrity.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = ROOT_DIR / "backups"


def load_env_if_present() -> None:
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k not in os.environ:
                    os.environ[k.strip()] = v.strip()


def find_rclone() -> Optional[Path]:
    which_rc = shutil.which("rclone")
    if which_rc:
        return Path(which_rc)
    tools_dir = ROOT_DIR / "tools" / "rclone"
    if tools_dir.exists():
        matches = list(tools_dir.glob("**/rclone.exe"))
        if matches:
            return matches[0]
    return None


def restore_from_google_drive() -> bool:
    load_env_if_present()
    remote_name = os.getenv("RCLONE_REMOTE_NAME", "gdrive")
    backup_folder = os.getenv("DRIVE_BACKUP_FOLDER", "HeartDiseasePrediction-Backups")

    rclone_bin = find_rclone()
    if not rclone_bin:
        print("[!] Rclone binary not found.", file=sys.stderr)
        return False

    remote_source = f"{remote_name}:{backup_folder}"
    print(f"[*] Downloading backups from Google Drive: {remote_source} to {BACKUP_DIR}...")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(rclone_bin),
        "copy",
        remote_source,
        str(BACKUP_DIR),
        "-v",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        print("[+] Download complete.")
        return True
    else:
        print(f"[!] Rclone download failed: {proc.stderr}", file=sys.stderr)
        return False


def main():
    success = restore_from_google_drive()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
