# C5 Clean-4 independent local economic reproduction — exploratory, not a promotion

Date: 2026-11-17. Branch: research/v98-independent-zero. No holdout accessed; no 2026+ data used.

## Provenance
Downloaded GitHub Actions source artifacts 13444665313 (prices) and 13464271018 (native funding). The canonical SHA-256 hashes of BTCUSDT, ETHUSDT, BNBUSDT and SOLUSDT price and funding CSVs match their respective manifests. Price manifest SHA-256: `01e7bdeb8bcaf34ee898e322cf20f4479c0e25a9066b40f8cd2446286259f8a8`. Funding manifest SHA-256: `f33094dfc065aa862a529d46f36e15f8a418ab085780214a0423488d2ff49622`. 27,048 hourly bars, 2022-12-01 through 2025-12-31 inclusive.

## Method and limitations
Independent local reimplementation of the *current* C5 composed sleeves, 13-window volatility router, governor, per-asset 0.40/gross 0.75 caps, causal next-open replay, funding cashflows and 0.0006 turnover fee+slippage multiplied by 1x/2x/4x. 15 replays: full portfolio plus leave-one-sleeve-out for four sleeves across three cost regimes. Rolling-squared-return prefix-sum implementation of the router checked against direct computation at five timestamps (max absolute volatility deviation 4.3e-16). This is a **cross-check, not the official workflow replay**. The local script did not compute post-fill exposure audits, full ledgers, profit factor, daily win rates or chronological out-of-sample folds. Drawdowns below are provisional (local calculation excludes the final close mark from peak/drawdown update). Do not promote or infer live performance.

## Reproduced training-only results (USD starting from $10,000)
| Cost | Full equity | Full max drawdown (provisional) | Without growth | Without opportunity | Without relative value | Without stress/recovery |
|---|---:|---:|---:|---:|---:|---:|
| 1x | 15,541.77 | 15.76% | 13,582.77 | 15,267.26 | 14,703.81 | 15,555.82 |
| 2x | 14,563.36 | 16.13% | 13,015.78 | 13,915.55 | 13,255.32 | 14,311.15 |
| 4x | 13,274.26 | 17.82% | 11,119.58 | 12,934.40 | 11,437.59 | 13,349.76 |

Marginal equity = full minus without sleeve:
- Growth: +1,959.00 / +1,547.58 / +2,154.68 USD at 1x/2x/4x.
- Opportunity: +274.51 / +647.81 / +339.87 USD.
- Relative value: +837.96 / +1,308.04 / +1,836.67 USD.
- Stress/recovery: **-14.05 / +252.21 / -75.49 USD**.

## Decision
C5 **not eligible for promotion**: stress/recovery marginal contribution is not robustly positive across the preregistered severe/supersevere cost scenarios; its preregistration provenance was already unverified. No parameter rescue. This is a provisional economic rejection signal pending byte-for-byte official-run reconciliation. No champion is promoted. Preserve Phase243 holdout, all Frozen engines, V99 and paper unchanged.

## Next critical-path work
Run the actual C5 GitHub Actions workflow and retrieve its two JSON outputs plus 1x/2x/4x ledgers; reconcile the independent results, investigate any discrepancies, then pursue a genuinely distinct preregistered seven-slot composition and chronological independent validation. The GitHub connector currently exposes workflow artifact downloads and job inspection by ID but not workflow dispatch or a general run listing; lack of an identified C5 run ID prevents claiming an official execution.
