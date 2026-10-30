# V98 Independent — Phase676 chronological causality preregistration

Date: 2026-10-19. Branch: `research/v98-independent-zero`. Scope: `research/v98_independent/` only.

**Frozen hypothesis:** The complete seven-slot Phase646/E portfolio and all matched Phase647 ablations must be causal. Mutating prices at or after a chosen timestamp must never alter a target at any earlier timestamp. Frozen Phase252 funding-driven core remains immutable. This is a source-only anti-lookahead test, not a new alpha, economic backtest, promotion, or parameter search.

**Prespecified mutations:** 2023-07-01 00:00 UTC BTC 0.2x; 2024-03-15 12:00 UTC ETH 5x; 2024-12-31 23:00 UTC BNB 0.2x; 2025-01-01 00:00 UTC SOL 5x; 2025-06-01 00:00 UTC all four 0.2x; 2025-12-01 00:00 UTC all four 5x. For each, multiply all later close prices in the named column(s). These are artificial causal mutations, **not** trading data or return scenarios.

**Hard gates:** Verify all five frozen Phase647 target SHA256 digests first. For each mutation and each of the five paths, all targets before the mutation must remain bitwise equal; preserve the gross <=1.45 and per-asset <=0.70 target constraints, nonnegative/finite weights, and unmodified Phase252. No access to XRP, 2026+ training, Phase083 holdout, V14/V15/V99, or V16/V99 files. Do not compute PnL or treat this as vendor-origin funding attestation.

Any failure indicates a causal implementation defect, not permission to rescue a rejected architecture, change windows/thresholds, or tune from validation. Vendor-origin authentication and chronological net-economic validation remain mandatory before any promotion.
