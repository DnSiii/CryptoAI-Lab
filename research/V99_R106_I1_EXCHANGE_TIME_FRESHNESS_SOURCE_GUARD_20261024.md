# V99 I1 — preregistered exchange-time freshness and fail-closed book validity (2026-10-24 17:xx BRT)

**Source-integrity correction only — DATA_ONLY/HOLD, NO PROMOTION.** No alpha, returns, cost parameter, portfolio or fold thresholds are being optimized. The historical executable quote archive is still missing.

## Failure mode discovered before implementation

The existing 91-Sunday intake bounds `local_timestamp` to the final 300 seconds before a Monday decision, but does **not** bound the underlying `timestamp` (venue exchange event time) to that interval. A quote first received in the final minute could therefore be hours old at the exchange and still count toward a two-strike book. An independent oracle duplicated this weakness. This can falsely certify a stale, non-executable book.

## Fixed rule before CI

For each quote, require **both** the original venue exchange timestamp and local arrival timestamp to be within the closed-open interval `[decision - 300 seconds, decision)`, with `exchange <= arrival`. Rows received before the interval cannot supply a valid current book. For rows arriving inside the interval with stale exchange timestamps, retain their latest-arrival supersession ordering but mark them invalid: an incoming stale update must **not** resurrect a prior valid book. Recompute the original-byte independent oracle separately. Two put strikes must still share the same eligible expiry; the original five folds, 91 maturity-eligible weeks, 182 asset-weeks and all sealed boundaries remain unchanged.

Negative controls must include a delayed stale exchange event with a recent local arrival and a newer stale update overriding a valid earlier quote. Only the source contract changes; no economic TRAIN, synthetic PnL or promotion claim. No live orders, Frozen/paper/legacy or validation/holdout modifications.

## Dependency unchanged

Obtain authorized BTC+ETH original historical bid/ask and sizes with exchange/local timestamps, full gap/completeness attestations and dated native fees, coin collateral, margin, settlement and liquidation rules. The existing 4,000-row two-day sample does not cover the 91 decisions. The new guard cannot supply missing records.
