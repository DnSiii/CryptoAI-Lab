# V98 Independent Phase243 — BNB sign-bridge audit (2026-10-11)

**Scope:** branch `research/v98-independent-zero`, V98-only funding training data (2023-01-01 to 2025-12-31 UTC). Source: frozen Phase206 canonical BNBUSDT funding CSV, Git blob `6b46a2a911d85079f3ce4ec5bc8b1791febd397a`. This is **not** independent publisher-source authentication.

## Descriptive, equal-horizon 16-hour comparison

All endpoints have nonzero rates. The middle settlement is either zero or nonzero. The endpoint sign flips in **12/145** zero-middle windows (8.28%) versus **6/898** nonzero-middle windows (0.67%). Stratified by middle-settlement year: 2023 **4/60 vs 2/381**; 2024 **7/43 vs 4/370**; 2025 **1/42 vs 0/147**. This improves on comparing zero-spanning multiweek intervals to immediate adjacent settlements; it does **not** establish causality. Overlapping windows, conditioning, regime differences and retrospective analysis prohibit interpreting these as independent statistical trials.

The canonical series has 1,800 zero settlements among 3,288 training settlements; 367 bounded zero runs, 49 with opposite signs at their nonzero edges, and a longest run of 77. No other four V98 funding series has a zero at the same 1,800 timestamps. This pattern is consistent with, but does not prove, a zero-rate transition mechanism; source ZIPs and publisher checksums remain missing.

## Decision and next gate

**Phase240 rejected; Phase243 source gate blocked; champion none.** No holdout, no imputation, no new backtest, no change to cost assumptions, V16 or V99. Reacquire and verify the original BNB funding ZIPs (2022-12 through 2025-12) and original XRP daily 1h/1m archives, then reconcile against the frozen training canonical source. A new local audit implementation and adversarial tests are retained separately until safe publication.
