"""Dataset Manager & Restorer.

Ensures sample test datasets and verification fixtures are generated and restored.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scripts.generate_sample_data import generate_all_samples


def main():
    print("[*] Verifying / Restoring project datasets...")
    generate_all_samples()
    print("[+] All project datasets and fixtures are ready.")


if __name__ == "__main__":
    main()
