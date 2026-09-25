# V99 R106 Phase137 — OKX/Binance Cross-Venue Dislocation Reversion

Status: PREREGISTERED / TRAIN-ONLY / ONE HYPOTHESIS / NO GRID

## Why this is admissible

Phase136 established a genuinely independent second-venue source: OKX 1H USDT perpetual candles for BTC, ETH, SOL, XRP and DOGE have 100% coverage over the frozen V99 training window, no gaps/unfinished candles, and identical full-row hashes across two independent acquisitions.

This hypothesis is frozen before any OKX-vs-Binance return relation or PnL is inspected.

## Economic mechanism

Major perpetual venues should remain tightly linked by arbitrage. A venue-specific price dislocation relative to its own recent cross-venue baseline is therefore hypothesized to mean-revert. The test intentionally removes the common cross-venue level and trades only relative dislocations across the frozen five-asset basket.

## Frozen feature

For each asset:
1. Binance USD-M 1H close from the canonical V99 replay.
2. OKX USDT-SWAP 1H close from the Phase136-admitted public source.
3. raw venue spread = log(Binance close / OKX close).
4. trailing baseline = rolling 168h median of the spread.
5. trailing scale = 1.4826 * rolling 168h MAD of the spread.
6. standardized dislocation = (spread - baseline) / scale.
7. raw reversion score = -tanh(standardized dislocation).
8. cross-sectionally demean the five raw scores each hour to remove common venue premium.
9. shift the complete score by exactly 1 hour.
10. L1 normalize across the frozen five assets.

No alternate lookback, sign, threshold, venue, symbol subset or cadence is authorized.

## Frozen universe

Mapping:
- BTCUSDT <-> BTC-USDT-SWAP
- ETHUSDT <-> ETH-USDT-SWAP
- SOLUSDT <-> SOL-USDT-SWAP
- XRPUSDT <-> XRP-USDT-SWAP
- DOGEUSDT <-> DOGE-USDT-SWAP

No symbol substitution after result.

## Portfolio / cost contract

- alpha gross cap: 0.20
- hourly causal targets
- selection cost: existing V99 severe per-side cost
- canonical execution/funding/guard machinery unchanged
- no parameter search
- no sign flip
- no rescue tuning
- no V16/V99 Frozen write
- train end exclusive: 2024-01-18T00:00:00Z
- four existing temporal folds

## Data integrity invariant

The OKX acquisition used for Phase137 must reproduce the exact Phase136 normalized full-row SHA-256 for every frozen instrument before PnL is allowed to run. Any mismatch aborts the experiment before PnL.

## Train gate

Use the existing V99 train diagnostic contract. PASS only if the aggregate severe-cost training result is positive/healthy and temporal stability gates pass. FAIL is permanent for this exact cross-venue dislocation-reversion hypothesis.

## Next gate

PASS freezes the exact specification for supersevere costs, regimes, tails/concentration, benchmark envelope and reproducibility before any untouched-holdout evaluation.

FAIL means no sign flip to continuation and no lookback rescue. The next research direction must be independently justified.
