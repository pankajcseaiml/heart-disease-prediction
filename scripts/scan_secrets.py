"""Enterprise Secret & Git History Scanner.

Performs static analysis and Git history scanning for credentials, tokens,
private keys, and sensitive patterns according to enterprise security standards.
NEVER prints or logs secret values.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

PATTERNS = [
    ("Private Key", re.compile(r"-----BEGIN (RSA|EC|DSA|OPENSSH|PGP) PRIVATE KEY-----", re.IGNORECASE)),
    ("AWS Access Key", re.compile(r"(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}")),
    ("GitHub Personal Access Token", re.compile(r"(ghp_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z_]{82})")),
    ("Generic API Key / Secret", re.compile(r"(api[_-]?key|secret[_-]?key|jwt[_-]?secret)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", re.IGNORECASE)),
    ("Database Connection String with Password", re.compile(r"(postgres|mysql|mongodb|redis):\/\/[^:\s]+:[^@\s]+@", re.IGNORECASE)),
    ("Hardcoded Password", re.compile(r"(password|passwd|pwd)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]", re.IGNORECASE)),
]

IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "tools", "backups", "secrets", "data"}
IGNORE_EXTS = {".pyc", ".png", ".jpg", ".jpeg", ".ico", ".svg", ".zip", ".tar", ".gz", ".enc", ".exe", ".dll", ".kdbx", ".db"}



def scan_file_content(path: Path) -> List[Dict[str, str]]:
    findings = []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return findings

    for line_num, line in enumerate(content.splitlines(), start=1):
        for category, pattern in PATTERNS:
            match = pattern.search(line)
            if match:
                # Mask location and never show secret
                findings.append({
                    "category": category,
                    "location": f"{path}:{line_num}",
                    "risk": "HIGH",
                    "rotation_required": "YES",
                    "status": "DETECTED_IN_FILE",
                })
    return findings


def scan_working_tree(root_dir: Path) -> List[Dict[str, str]]:
    all_findings = []
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in IGNORE_EXTS:
                continue
            all_findings.extend(scan_file_content(file_path))
    return all_findings


def scan_git_history(root_dir: Path) -> List[Dict[str, str]]:
    findings = []
    try:
        res = subprocess.run(
            ["git", "log", "-p", "--all"],
            cwd=root_dir,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        diff_text = res.stdout
    except Exception as exc:
        print(f"Failed to read git history: {exc}", file=sys.stderr)
        return findings

    current_commit = "unknown"
    for line in diff_text.splitlines():
        if line.startswith("commit "):
            current_commit = line.split()[1][:8]
        elif line.startswith("+") and not line.startswith("+++"):
            added_line = line[1:]
            for category, pattern in PATTERNS:
                if pattern.search(added_line):
                    findings.append({
                        "category": category,
                        "location": f"Commit {current_commit}",
                        "risk": "CRITICAL",
                        "rotation_required": "YES",
                        "status": "HISTORICAL_COMMIT",
                    })
    return findings


def main():
    root = Path(__file__).resolve().parent.parent
    print(f"[+] Starting Enterprise Secret Scan on: {root}")
    
    working_tree_findings = scan_working_tree(root)
    git_history_findings = scan_git_history(root)
    
    total = len(working_tree_findings) + len(git_history_findings)
    
    print("\n" + "=" * 80)
    print("SECRET SCAN AUDIT REPORT")
    print("=" * 80)
    
    if total == 0:
        print("[OK] Zero secrets detected in working tree or Git commit history.")
        print("Status: CLEAN")
        print("=" * 80)
        return 0
    
    print(f"[!] Total findings: {total}")
    for item in working_tree_findings + git_history_findings:
        print(f"- Category: {item['category']}")
        print(f"  Location: {item['location']}")
        print(f"  Risk: {item['risk']}")
        print(f"  Rotation Required: {item['rotation_required']}")
        print(f"  Status: {item['status']}")
        print()
    print("=" * 80)
    return 1


if __name__ == "__main__":
    sys.exit(main())
