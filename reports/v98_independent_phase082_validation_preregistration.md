# V98 Independent Phase082 — Phase081 validation pre-registration

## Frozen candidate
Phase081 28-day cross-sectional lagged channel-location spread passed its complete training gate before this validation was opened. Training evidence: +186.70% aggregate return, daily PF 1.2817, max drawdown -28.04%; 2023 +8.13%/PF 1.0861, 2024 +112.06%/PF 1.5750, 2025 +24.65%/PF 1.1875; severe +110.74%; supersevere +30.65%; no ruin.

The candidate is frozen exactly as Phase081: universe BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT/XRPUSDT; 672-hour lagged channel location; long highest channel location, short lowest; daily 00:00 UTC rebalance; gross 0.75; existing exact V98 cost/funding model. No parameter, direction, threshold, universe, exposure or timing changes are allowed.

Frozen Phase081 reproducibility anchors: positions SHA256 `eac49cb65271d67640a4e856c96eb9398bc25681b7d336228736228fce4a2357`; Phase081 preregistration SHA256 `9fc1866df50f26219458ef857e41c3928ea42e21c0fb313489b3283ce7d2c4bf`.

## Validation boundary
Validation only: 2026-01-01 through 2026-07-31, using a separately rebuilt V98 validation dataset capped at 2026-07. Final holdout begins 2026-08-01 and MUST remain absent/unread/untouched.

## Frozen validation diagnostics and gate
Report validation return, max drawdown, daily Profit Factor, payoff, win rate, positive days; monthly diagnostics Jan-Jul; BASE/severe/supersevere; regimes; concentration/tails; asset contribution; activation/exposure; reproducibility hash.

PASS requires: validation return > 0; daily PF > 1.02; max drawdown >= -35%; severe return > 0; supersevere return > 0; no ruin. Any failure => **REJECT_VALIDATION_NO_RESCUE** and final holdout stays closed. Complete PASS permits a later, separately frozen one-shot final holdout gate; it does not itself authorize holdout inspection.

## Anti-overfit declaration
Validation is confirmatory only. No rescue, retuning, direction flip, threshold search, or selection using validation is permitted. V99 and V16 evidence are prohibited. Final holdout remains untouched.
