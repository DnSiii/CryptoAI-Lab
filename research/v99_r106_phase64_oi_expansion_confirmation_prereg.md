# V99 R106 Phase64 — open-interest expansion confirmation (pre-registration)

Decision time: after Phase63 completed the metrics coverage/schema audit and before any Phase64 return/PnL relation is computed.

## Evidence boundary
Phase63 found metrics data for all 48 PIT assets, 37,836 pre-holdout daily archives, 12 explicitly missing dates, 1 schema variant, and 1,263 deterministic monthly integrity samples passing the audit workflow. Missing dates must remain missing; no silent forward-fill across a missing archive is allowed.

## Single hypothesis
**Leverage-expansion confirmation:** a price move accompanied by expanding futures open interest reflects new directional risk entering rather than only position closing, and may have short-horizon continuation value cross-sectionally.

Fixed feature per asset: use the last native `sum_open_interest_value` observation available in each completed UTC hour. Compute `oi_chg24 = OI/OI.shift(24)-1` and canonical `ret24 = close/close.shift(24)-1`. Raw score is `sign(ret24) * max(oi_chg24, 0)`. Cross-sectionally winsorize raw scores at 5/95% each hour, then shift the complete score by one hour before target construction. Existing deterministic Phase31 cross-sectional weight mapper; alpha gross budget 0.20.

No alternate OI field, horizon, sign, winsor percentile, threshold, gross budget, or missing-data fill will be tested in Phase64. This is not a retune of Phase61/62 taker-flow hypotheses.

## Gates
- Native metrics downloads/parsing restricted to <= registered train_end. Holdout metrics and holdout returns remain untouched.
- SHA256/CRC verification on every archive actually consumed by Phase64.
- Causal t-1 complete feature.
- Existing severe-cost train gate and temporal-fold stability criteria. A reject cannot be rescued by sign/horizon retuning.
- Only a train pass may freeze the exact specification for a separate untouched-holdout gate; only after that may supersevere costs, regime matrix and benchmark envelope be evaluated.

V16 Frozen and V99 Frozen remain read-only.