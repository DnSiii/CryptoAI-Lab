# V98 Independent Phase076 — Phase075 validation pre-registration

## Frozen candidate
Phase075 21-day cross-sectional downside-risk asymmetry passed its complete training gate before this validation was opened. Training evidence: +110.42% aggregate return, daily PF 1.2107, max drawdown -26.52%; 2023 +28.14%/PF 1.2169, 2024 +21.00%/PF 1.1553, 2025 +35.19%/PF 1.2503; severe +73.58%; supersevere +29.05%; no ruin.

The candidate is frozen exactly as Phase075: universe BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT/XRPUSDT; 504-hour lagged downside/upside semivariance share; long minimum downside share, short maximum; daily 00:00 UTC rebalance; gross 0.75; existing exact V98 cost/funding model. No parameter, direction, threshold, universe, exposure or timing changes are allowed.

Frozen Phase075 reproducibility anchors: positions SHA256 `33286707f5ae63d13b8758ee1a93b2fc786ce434fb4d3e8884df0ad3d84d0880`; Phase075 preregistration SHA256 `dfa7300edf9631e979db01eabb103a17383f3c7c75f7453857d7926d6cbbfbb7`.

## Validation boundary
Validation only: 2026-01-01 through 2026-07-31, using a separately rebuilt V98 validation dataset capped at 2026-07. Final holdout begins 2026-08-01 and MUST remain absent/unread/untouched.

## Frozen validation diagnostics and gate
Report validation return, max drawdown, daily Profit Factor, payoff, win rate, positive days; monthly diagnostics Jan-Jul; BASE/severe/supersevere; regimes; concentration/tails; asset contribution; activation/exposure; reproducibility hash.

PASS requires: validation return > 0; daily PF > 1.02; max drawdown >= -35%; severe return > 0; supersevere return > 0; no ruin. Any failure => **REJECT_VALIDATION_NO_RESCUE** and final holdout stays closed. Complete PASS permits a later, separately frozen one-shot final holdout gate; it does not itself authorize holdout inspection.

## Anti-overfit declaration
Validation is confirmatory only. No rescue, retuning, direction flip, threshold search, or selection using validation is permitted. V99 and V16 evidence are prohibited. Final holdout remains untouched.