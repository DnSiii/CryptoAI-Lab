from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def run(*args: str) -> None:
    subprocess.run([sys.executable, *args], cwd=PROJECT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="v98_independent_phase050_data.json")
    parser.add_argument("--workers", type=int, default=40)
    args = parser.parse_args()
    if args.config != "v98_independent_phase050_data.json":
        raise SystemExit("V98 Phase050 rebuild accepts only the frozen training-only config")
    run("scripts/download_futures_archive.py", "--config", args.config, "--workers", str(args.workers))
    run("scripts/build_canonical.py", "--config", args.config)


if __name__ == "__main__":
    main()
