# V98 Independent Phase1032 — pre-economic P execution-safety freeze amendment

**Timing:** after Phase1031 source-only freeze, before any P historical PnL. This is a discovered implementation-contract correction, NOT a post-result strategy rescue. No P alpha, signal, window, gross target, fee tier, funding assumption, canonical target hash, holdout, 2025 data or external benchmark changed.

Phase1023 preregistered all 16 current-hour OHLC corners as **ex-post hard rejection**, but the initial Phase1027 ledger delegated to a six-corner shortcut validated by a prior 3,000-state long-only oracle. The revised ledger now explicitly enumerates all **16 actual current-hour high/low corners** after native funding debit and rejects any violation of the 10% stressed-equity floor, gross cap or per-asset cap. Current high/low are used only after execution and never for position sizing. The existing six-corner infrastructure check remains as a redundant assertion.

Updated immutable economic-code blob pins, effective **before the first P economic call**:
- `phase1027_p_funded_ledger_hourly.py`: `ba9c8346f68996f3d9d103cd21968269a9eb81bb` (supersedes Phase1031 ledger pin).
- `phase1029_p_training_gate.py`: `1a991877cb777cf9a108671d1cc492717b60061e` (supersedes Phase1031 gate pin).
- Phase1031 `phase1024`, `phase1025`, `phase1026` code blobs and all five canonical target SHA256 remain **unchanged**.

Local full-fold flat-cash synthetic conservation rerun: 3/3 tests passed; the updated 16-corner ex-post path is exercised across 17,544 2023/2024 hours. Official preflight must be rerun against these exact updated code bytes before P economic execution. Any future economic failure REJECTS P; no rescue via code, signs, costs, thresholds or leverage.
