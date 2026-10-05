# V98 Independent Phase240 — decision/pathology audit protocol

Status: locked while the first Phase240 decision-grade run is pending. This file does not inspect Phase240 performance and must not be used to alter the frozen grid or direction.

## Independent checks after harvest
1. Verify the workflow firewall excludes every price/funding timestamp >= 2026-01-01 and that the two serialized runs are byte-identical.
2. Apply `phase240_validate.py` mechanically to all 8 preregistered specs and all 2023/2024/2025 folds. No rescue, sign flip, threshold search, regime filter, asset deletion, or holdout opening is permitted.
3. For any failure, attribute whether it exists already at base cost or appears only under severe/supersevere costs. Report annual return, max drawdown, PF, payoff, win rate, positive days and turnover.
4. Inspect bull/bear/sideways returns/PF/DD, asset PnL concentration, funding contribution and p01/p05/p95/p99 tails. Diagnostics explain failure; they cannot create a new Phase240 variant.
5. If every spec fails, close the family and preregister a scientifically distinct next family before implementation. If a spec passes, promotion is only training-survivor status; 2026+ remains untouched until the existing research protocol explicitly authorizes holdout opening.

## Causality invariants
- beta used for residual at hour u is lagged (`beta.shift(1)`).
- residual center and MAD scale are rolling statistics shifted one hour.
- position decision at open(t) reads standardized shock only at t-1.
- funding is timestamped point-in-time and charged against lagged held exposure.
- gross exposure is capped at 1.

## Frozen economics
Base round-trip/turnover cost coefficient 7 bp; severe 14 bp; supersevere 28 bp. Chronological folds are calendar 2023, 2024, 2025. The 2026+ holdout remains closed.
