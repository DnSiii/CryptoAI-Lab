from pathlib import Path
import json
import sys
import argparse

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from cryptoai_v13.data import build_canonical


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="research.json")
    args = parser.parse_args()
    print(json.dumps(build_canonical(PROJECT, args.config), indent=2))
