from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

import run_v99_r105_all_regime_structural_audit_fast2  # noqa: F401
import run_v99_r106_phase6_beta_neutralizer as phase6

if __name__ == "__main__":
    phase6.main()
