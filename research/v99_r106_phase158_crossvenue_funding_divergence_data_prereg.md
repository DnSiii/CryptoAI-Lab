# V99 R106 Phase158 — Cross-Venue Funding Divergence DATA preregistration

## Motivation
Phases149–157 tested cross-venue OHLC geometry and repeatedly failed TRAIN alpha gates. Phase158 deliberately leaves that exhausted family and inspects a genuinely orthogonal microstructure source: perpetual funding-rate disagreement between OKX and Binance.

## Scope
DATA-ONLY feasibility/integrity audit. No trading PnL, no parameter selection, no holdout inspection, and no modification of V16 Frozen or V99 Frozen.

## Frozen universe and interval
- Instruments: BTC, ETH, SOL, XRP, DOGE perpetual USDT pairs on OKX and Binance.
- Chronological TRAIN interval only: 2021-12-01 00:00 UTC inclusive through 2024-01-18 00:00 UTC exclusive.
- Native funding event timestamps are retained; no forward fill or interpolation.

## Precommitted integrity gates
For each asset/venue:
1. timestamps strictly increasing after deterministic de-duplication;
2. all rates finite;
3. no timestamp outside TRAIN;
4. at least 95% of expected 8-hour event count (expected count derived only from TRAIN interval length; this is a feasibility gate, not an alpha threshold);
5. cross-venue nearest timestamp alignment tolerance <= 60 minutes and aligned coverage >= 90% of the smaller venue event count.

## Scientific decision
PASS_DATA_ONLY means the source is eligible for a later separately preregistered causal alpha hypothesis. FAIL_DATA_ONLY permanently rejects this acquisition path unless the failure is proven to be a transport/API defect. No alpha direction, lookback, threshold, sign, rescue, or portfolio rule is selected in Phase158.

## Anti-contamination
Holdout rows used for feature construction = 0. Holdout rows used for selection = 0. No PnL is computed. V16 Frozen and V99 Frozen remain untouched.
