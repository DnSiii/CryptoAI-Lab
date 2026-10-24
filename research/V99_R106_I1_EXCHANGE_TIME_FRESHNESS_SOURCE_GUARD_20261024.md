# V99 I1 — preregistered exchange-time freshness and fail-closed book validity (2026-10-24 17:xx BRT)

**Source-integrity correction only — DATA_ONLY/HOLD, NO PROMOTION.** No alpha, returns, cost parameter, portfolio or fold thresholds are being optimized. The historical executable quote archive is still missing.

## Failure mode discovered before implementation

The existing 91-Sunday intake bounds `local_timestamp` to the final 300 seconds before a Monday decision, but does **not** bound the underlying `timestamp` (venue exchange event time) to that interval. A quote first received in the final minute could therefore be hours old at the exchange and still count toward a two-strike book. An independent oracle duplicated this weakness. This can falsely certify a stale, non-executable book.

## Fixed rule before CI

For each quote, require **both** the original venue exchange timestamp and local arrival timestamp to be within the closed-open interval `[decision - 300 seconds, decision)`, with `exchange <= arrival`. Rows received before the interval cannot supply a valid current book. For rows arriving inside the interval with stale exchange timestamps, retain their latest-arrival supersession ordering but mark them invalid: an incoming stale update must **not** resurrect a prior valid book. Recompute the original-byte independent oracle separately. Two put strikes must still share the same eligible expiry; the original five folds, 91 maturity-eligible weeks, 182 asset-weeks and all sealed boundaries remain unchanged.

Negative controls must include a delayed stale exchange event with a recent local arrival and a newer stale update overriding a valid earlier quote. Only the source contract changes; no economic TRAIN, synthetic PnL or promotion claim. No live orders, Frozen/paper/legacy or validation/holdout modifications.

## Dependency unchanged

Obtain authorized BTC+ETH original historical bid/ask and sizes with exchange/local timestamps, full gap/completeness attestations and dated native fees, coin collateral, margin, settlement and liquidation rules. The existing 4,000-row two-day sample does not cover the 91 decisions. The new guard cannot supply missing records.

## Executed outcome — 2026-10-24 17:47 BRT

Implemented the venue-exchange-time bound in the production source-intake parser and **separately** in the raw-byte independent oracle; added two adversarial cases (a six-minute-old exchange event arriving recently, and a newer stale event overriding an older valid book). The original 91-Sunday synthetic fixture and all previous negative controls were retained.

[GitHub Actions 40131373614](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40131373614) **SUCCESS**, final code commit `e303bf5f5f7383e2e9a12927a104b039532df805`: 7/7 source-contract tests passed. The independent oracle reconstructed the baseline **182/182 synthetic** asset-weeks and **181/182 synthetic** when either delayed-source negative control is introduced; it also passed original-byte integrity checks. This demonstrates a repaired false-positive in **source eligibility**, not any historical profitability.

**Real original-source coverage remains 0/182** at the 91 maturity-eligible Monday decisions from the available two-day partial sample. No licensed full BTC+ETH quote tape, authenticated account fee tier or historical native margin/liquidation evidence was added; no economic TRAIN or independent portfolio validation was run. **DATA_ONLY/HOLD — NO PROMOTION.** Validation [2023-10-01, 2024-01-18), final holdout >=2024-01-18, immutable Frozen, legacy champion, paper/results and orders remain untouched.
