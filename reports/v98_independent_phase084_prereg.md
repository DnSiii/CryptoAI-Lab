# V98 Independent — Phase084 preregistration

Status: PREREGISTERED BEFORE TRAINING PnL.

## Scientific boundary
Phase083 final holdout (2026-08-01 through 2026-09-15) has been opened and is permanently contaminated for model selection. Phase084 MUST NOT read, score, diagnose, tune, filter, select, or otherwise use Phase083 outcomes. Research decisions remain restricted to the original training sample and chronological folds. Any future final confirmation requires a new, later, genuinely untouched window.

## Independent hypothesis
Cross-sectional **daily sign-streak persistence** contains information not represented by return magnitude: among BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT and XRPUSDT, the contract with the strongest lagged consecutive positive daily-close streak will outperform the contract with the strongest lagged consecutive negative streak. The feature uses only completed UTC daily returns and ignores return magnitude.

## Frozen specification
- Universe: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT.
- Observation: completed UTC daily close-to-close return signs only.
- Maximum streak memory: 7 completed days. A streak score is +k for k consecutive positive completed daily returns, -k for k consecutive negative completed daily returns, capped at |7|; zero return resets the streak.
- Signal time: 00:00 UTC, using information available through 23:00 UTC of the prior day only.
- Portfolio: long highest streak score and short lowest streak score, deterministic symbol tie-break; no position when highest <= 0 or lowest >= 0.
- Gross exposure: 0.75 when active, split equally long/short; dollar neutral.
- Rebalance: daily 00:00 UTC; forward-fill until next rebalance.
- No parameter search, rescue tuning, sign inversion, overlays, or Phase083-informed modifications.

## Evaluation gate
Training only first. Report aggregate and chronological folds; BASE, severe and supersevere costs/funding; regimes; concentration/tails; max drawdown; daily Profit Factor, payoff, win rate and positive days; activation and reproducibility hashes.

Training PASS requires all: aggregate return > 0; PF > 1.05; max DD >= -35%; no ruin; each frozen chronological fold return > 0 and PF > 1.00; severe return > 0; supersevere return > 0. FAIL is REJECT_NO_RESCUE. PASS permits a separately preregistered confirmation stage, but the already-open Phase083 window is forbidden for that confirmation.

V99 and V16 are forbidden inputs/benchmarks for selection.
