from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
ALLOWED_CONFIGS = {
    "v98_independent_phase050_data.json",
    "config/v98_independent_phase082_validation_data.json",
}


def run(*args: str) -> None:
    subprocess.run([sys.executable, *args], cwd=PROJECT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="v98_independent_phase050_data.json")
    parser.add_argument("--workers", type=int, default=40)
    args = parser.parse_args()
    config = args.config
    if config == "v98_independent_phase082_validation_data.json":
        config = "config/v98_independent_phase082_validation_data.json"
    if config not in ALLOWED_CONFIGS:
        raise SystemExit("V98 rebuild accepts only frozen Phase050 training or Phase082 validation-only configs")
    run("scripts/download_futures_archive.py", "--config", config, "--workers", str(args.workers))
    run("scripts/build_canonical.py", "--config", config)


if __name__ == "__main__":
    main()
