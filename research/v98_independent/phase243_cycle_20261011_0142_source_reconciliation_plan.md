# V98 Independent Phase243 — source reconciliation (2026-10-11)

Scope: 2023-11-14 XRPUSDT 11:00 UTC, original monthly 1h, daily 1h, daily 1m. Training only; holdout untouched; no alpha or champion promotion.

The last source-acquisition GitHub Actions run (38053620316) failed at the exact quote/base VWAP geometry check for monthly XRPUSDT 2023-11 row 323: base 62,032,915.1; quote 51,332,637.23413; high 0.6556; quote above base*high by 10,663,806.89457 USDT. The failure is a real data-quality gate, not a transient transport outage. Its original ZIP and checksum were preserved as a rejected-source artifact.

Next scientific step: compare provider checksum-verified daily 1h and daily 1m sources for the same UTC date, preserving all originals and testing all 24 hourly aggregates, including taker-buy and implied sell-side conservation. If any source disagrees, mark SOURCE_CONFLICT; never silently patch or skip a bar. Do not execute Phase243 alpha until source policy is independently reviewed and frozen.

Chronological folds, holdout, realistic fees/funding, severe/supersevere costs, regimes, tails, concentration, drawdown, PF, payoff, win rate, positive days and reproducibility remain mandatory.
