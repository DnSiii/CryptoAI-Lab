# V99 R106 Phase159 — Cross-Asset Funding Dispersion

## Status
PREREGISTERED BEFORE PnL. TRAIN-only. Phase158 cross-venue funding is closed as DATA-FAIL because historical OKX funding returned zero TRAIN rows while deterministic Binance Vision archives passed coverage. No gate is relaxed and no Phase158 alpha PnL is permitted.

## Scientific hypothesis
Perpetual funding is an orthogonal derivatives-positioning variable. When an asset's Binance funding is unusually rich/cheap relative to the contemporaneous cross-sectional median of the five frozen assets (BTC, ETH, SOL, XRP, DOGE), the extreme positioning may mean-revert in subsequent spot/perpetual returns. Test REVERSION only; no post-result sign flip.

## Frozen feature
At each native funding event t, use only funding observations timestamped <=t. For each asset i: d_i(t)=funding_i(t)-median_j(funding_j(t)). Standardize each asset's d using its own trailing 168 funding-event observations shifted by one event: z_i(t)=(d_i(t)-median_168[d_i(<t)])/(1.4826*MAD_168[d_i(<t)]). Signal available only after the funding timestamp; execution/return attribution starts at the next causal bar/event (t-1 discipline equivalent; never same-event lookahead). Direction = -sign(z). Magnitude follows the existing Phase136-compatible bounded allocator; portfolio L1 <= 1.

## Frozen data and universe
Binance Vision deterministic monthly fundingRate archives only, TRAIN 2021-12-01 inclusive to 2024-01-18 exclusive. Assets: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT. No holdout rows may be fetched or used for feature construction, selection, thresholds, normalization, or diagnostics. Required per-asset funding coverage >=95%; finite, strictly increasing, TRAIN-contained timestamps. Cross-sectional event requires >=4/5 assets within 60 minutes; event coverage >=90%.

## Validation discipline
Chronological TRAIN-only selection; four temporal folds; causal lag assertions; untouched holdout; severe and supersevere cost gates; regime matrix; tails/concentration audit; benchmark envelope; deterministic rerun/reproducibility. Full downstream gates run only if the base TRAIN gate passes. No threshold sweep, asset deletion, rescue, sign flip, or parameter tuning after PnL.

## Decision rule
FAIL any integrity/coverage/causality invariant => DATA/INTEGRITY REJECT, no alpha interpretation. FAIL base TRAIN gate => scientific REJECT and stop downstream gates. PASS => continue immediately through severe/supersevere, regimes, tails/concentration, benchmark envelope, and reproducibility before any promotion. V16 Frozen and V99 Frozen are immutable.