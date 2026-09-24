# V99 R106 — Phase134 rejection audit and Phase135 preregistration

## Phase134 decision

Phase134 Dollar-Volume Surprise Continuation is permanently rejected on the preregistered train-only severe gate. The persisted result has train ROI -0.3852898061, profit factor 0.7906858194, max drawdown 0.3859333490, robust mean excluding top 1% -3.9086455e-05, and 0/4 healthy temporal folds. All four folds are negative. No sign flip, horizon tuning, threshold tuning, or holdout inspection is permitted.

## Duplicate-family audit

The previously proposed "Amihud Illiquidity Shock Reversal" is NOT admitted as Phase135. Phase41 already tested the Amihud family (abs-return per traded quote-volume) at 24h, 72h and 168h under severe train-only evaluation and found 0/4 healthy folds for every family with negative robust means. Reusing Amihud with a 24h/168h transform would spend hypothesis budget on a previously rejected mechanism and is therefore cancelled before any Phase135 PnL is run.

## Phase135 preregistration — Return/Volume Coupling Continuation

Scientific question: does persistent covariance between signed hourly return and contemporaneous dollar-volume surprise identify cross-sectional accumulation/distribution pressure that predicts continuation after one full-hour lag?

This is distinct from Phase134 because dollar volume alone is not directional. It is distinct from Phase41 because it does not divide absolute return by liquidity. It is distinct from taker/aggressor-flow phases because it uses only OHLCV coupling and no aggressor labels.

Frozen specification, before PnL:

- Train end exclusive: 2024-01-18 00:00:00 UTC.
- Inputs: hourly close and volume from the canonical V15 replay; no holdout rows may enter feature construction.
- Hourly return: close.pct_change().
- Dollar volume: close * volume.
- Dollar-volume surprise: log(dollar_volume / trailing 168h median dollar_volume), with 168 observations required.
- Coupling state: rolling 72h mean of hourly_return * dollar_volume_surprise, with 72 observations required.
- Cross-sectional transform each hour: robust median/MAD z-score, requiring at least 8 assets.
- Direction: continuation exactly as signed coupling; score = tanh(robust_z).
- Causality: shift the complete score by exactly 1 hour before target construction.
- Portfolio normalization: L1 <= 1; alpha gross = 0.20.
- Selection cost: severe only.
- Evaluation: chronological train-only diagnostic and exactly four temporal folds using the existing Phase47 diagnostic contract, including robust mean excluding top 1%.
- Single hypothesis, no grid, no sign flip, no threshold search, no alternative 72/168 horizons after seeing PnL.
- Holdout must not be parsed or used for selection.
- V16 Frozen and V99 Frozen must remain byte-identical.

Gate: only stable_train PASS may freeze this exact specification for supersevere -> regime matrix -> tails/concentration -> benchmark envelope -> reproducibility -> untouched holdout. Any train-gate FAIL permanently rejects Phase135 without rescue tuning.
