# I1 original TRAIN fold uncertainty — preregistered post-screen diagnostic (2026-10-24)

**Scope:** one read-only, post-screen diagnostic of the *already published* I1 original 30 BTC/ETH observations in GitHub Actions 40087572354. This is NOT a new alpha trial, trading engine, cost backtest, options PnL, statistical proof of profitability, or permission to open validation/holdout. No thresholds, window dates, folds or assets may be optimized.

**Question:** Does the observed 4/5 positive gross variance-premium fold pattern provide convincing evidence of a stable positive underlying variance spread before paying for historical executable options quotes?

**Frozen calculations before implementation:** For each of BTC and ETH, and the equal-weight paired *nonportfolio* observation, calculate five chronological fold arithmetic means (three 30-day nonoverlapping windows per asset per fold). Compute:
1. Exact one-sided sign-test tail `sum(comb(5,k),k=s..5)/2**5` for `s` strictly positive fold means, treating zero as nonpositive. This is a descriptive sign-test under an idealized independent symmetric-fold null; temporal folds and assets are not proven independent, so do not call it an exact real-world p-value or combine BTC and ETH p-values.
2. Equal-fold grand mean, five leave-one-fold-out means, their minimum, and fraction of total *positive* fold-mean sum from the largest positive fold. Do not reweight observations or use the most flattering exclusion as the reported outcome.
3. Fixed observed gross variance multiplier 1.00 only, no new shock grid; report the 1.25x and 1.50x sensitivities only by referencing the existing independently verified Actions 40091478772, not recalculating or treating them as execution costs.
4. Verify exact 30 rows, 15 paired decision timestamps, 3 observations per asset/fold, no duplicate asset/timestamp, finite implied and realized variance, `premium = implied - realized`, frozen TRAIN [2021-12-09,2023-10-01), and all no-promotion/no-future flags. Fail closed on corruption. Independent Decimal implementation must recompute from original rows and reject an intentionally tampered metric.

**Interpretation policy:** 4/5 positive folds yields sign tail 6/32 = 0.1875. Even 5/5 (1/32) would not demonstrate tradable profits; executable option quotes, sizes, margin, hedge costs and native fee-tier evidence are mandatory. No paid data purchase is authorized; a provider with BTC-only history does not solve missing ETH historical quotes. Original I1 structural PASS is not rescinded or promoted by this descriptive diagnostic.

**Sources and safety:** read only original I1 screen artifact 40087572354; no price data beyond its original source-verified TRAIN report, no market-data requests, no orders, no writes to paper-results, V16/V99 Frozen, champion, dashboard, validation [2023-10-01,2024-01-18), or final holdout >=2024-01-18. Always output DATA_ONLY/HOLD — NO PROMOTION.
