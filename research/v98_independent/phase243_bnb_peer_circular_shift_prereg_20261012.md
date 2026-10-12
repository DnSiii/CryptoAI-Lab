# V98 Independent — BNB zero-rate peer-control alignment audit (preregistered)
Date: 2026-10-12 19:53 BRT. DATA ONLY; not alpha, source adjudication, or strategy selection.

Inputs: five V98-only Phase206 canonical funding CSVs; 2023-01-01 through 2025-12-31 UTC. Do not access 2026+ holdout or V16/V99.

Question: is BNB zero-funding association with absolute contemporaneous BTC/ETH/XRP/SOL funding due to calendar-month prevalence and persistence?

Frozen statistic: within each month with both BNB zero/nonzero settlements, mean absolute peer funding in basis points at zero minus nonzero BNB settlements, averaged equally across 36 eligible months. Also report unconditional contrast.

Frozen reference: 5000 deterministic monthwise circular rotations of BNB zero-state path; xorshift32 seed 0x98A12026; preserve monthly zero counts and circular run structure, peer path, and 8-hour alignment. Two-sided plus-one tail frequency and 2.5/97.5% null interval are descriptive, NOT IID market p-values. Rotations break month-boundary runs. No data imputation, source edits, trading-rule selection, or champion promotion.

This diagnostic cannot authenticate Binance funding or resolve the XRP source conflict. Preserve chronological folds, holdout, cost and stress gates.
