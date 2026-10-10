# V98 Independent Phase243 — preregistered XRP source triangulation (2026-10-09 22:45 BRT)

Status: PREREGISTERED BEFORE ORTHOGONAL SOURCE INSPECTION; DATA_ONLY, NO_ALPHA.

## Fixed question
The authenticated Binance USD-M XRPUSDT monthly 1h archive has one impossible
quote/base VWAP row at 2023-11-14 11:00 UTC: 62,032,915.1 XRP base,
51,332,637.23413 USDT quote, candle [0.6474, 0.6556].
Its implied VWAP is ~0.8275, >26% above the candle high. This is not rounding.

## Orthogonal evidence, fixed in advance
1. Fetch original Binance USD-M XRPUSDT *daily* 1h ZIP for 2023-11-14
   plus publisher .CHECKSUM. Validate the ZIP SHA256 and extract the exact
   11:00 UTC row; compare all 12 fields to the monthly 1h row.
2. Independently fetch the Binance USD-M XRPUSDT *daily* 1m ZIP for the
   same UTC date plus .CHECKSUM; validate 1440 consecutive minute bars,
   extract exactly the 60 minutes 11:00–11:59 UTC, and compute base and
   quote turnover sums, min low, max high, and OHLC.
3. Never use 2026+ or any holdout; no third-party engine/V99 data.
4. Keep all original hashes and discrepancy evidence. Distinguish
   identical publisher copies from independent granularity evidence.

## Decision policy
- If both 1h sources contain the same impossible row, that corroborates
  a provider-side 1h data-quality defect, not economic truth.
- If 1m aggregation is internally valid and disagrees, mark
  SOURCE_CONFLICT, not PASS; do not overwrite any original 1h row.
- If 1m and daily 1h independently match all OHLC/base/quote within
  preregistered numerical serialization tolerances, *and* the original
  monthly 1h row violates quote/base bounds, mark SOURCE_CONFLICT.
- Any transport/checksum/schema failure => INCONCLUSIVE.
- No skipping, replacing, clipping, relaxing VWAP checks, or opening
  holdout based on these results. Full 185-source acquisition remains
  FAIL_CLOSED until an explicitly reviewed provenance-preserving
  source policy is frozen *before* any Phase243 alpha PnL.

## Frozen research gates
Chronological folds, untouched holdout, realistic fees/funding, severe
and supersevere stress, regimes, concentration/tails, MDD, PF, payoff,
win rate, positive UTC days, deterministic replay, and anti-overfit
discipline remain mandatory. No champion promotion from source evidence.
