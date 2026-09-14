from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

# Importing fast2 installs the validated vectorized trade ledger and fixed
# active-day regime grouping onto the shared R105 audit module before R106 uses it.
import run_v99_r105_all_regime_structural_audit_fast2  # noqa: F401
import run_v99_r106_native_all_regime_engine as r106


if __name__ == "__main__":
    r106.main()
