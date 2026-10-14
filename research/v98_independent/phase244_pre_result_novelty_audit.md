# V98 Independent Phase244 — pre-result novelty and risk-geometry audit

Status: PRE-RESULT / NO PNL INSPECTED.

## Novelty against prior V98 families

Repository-level V98 namespace review before Phase244 performance shows prior trend-like work concentrated in:
- residual/cross-sectional trend and momentum families (Phases019/020/026/029/065/069/072/074/078/080/192/195/197/207);
- short-horizon volatility-compression breakout families (Phases200/208/214);
- cross-sectional channel-location Phase081;
- macro risk-on overlays such as Phases138/144.

Phase244 is not a parameter rescue of those families. It is a persistent **per-asset time-series channel state machine**: an asset competes only with its own past 90d/30d price history, not with peers, residual beta, volatility-compression thresholds, macro series, or a cross-sectional rank.

A repository tree search found no prior V98 file named/time-series/Donchian/moving-average trend-following implementation. This audit is a family-distinction claim, not evidence of profitability.

## Frozen exposure geometry

- Universe: authenticated Clean-4 BTC/ETH/BNB/SOL.
- Each asset state is {-1,0,+1}.
- Each active state maps to exactly 0.25 absolute target weight.
- Target gross therefore belongs to {0,0.25,0.50,0.75,1.00}.
- Target net belongs to {-1.00,-0.75,...,+1.00}.
- No leverage scaling, pyramiding, averaging down, volatility targeting, or post-result gross tuning.
- Exact backtester clips open gross at 1.0; close gross may drift with returns and is reported separately.
- Funding is charged to the pre-trade position at the normalized scheduled 8h settlement.

## Interpretation policy

If Phase244 fails its preregistered Growth-Core gate, the exact 90d/30d rule is REJECT_GROWTH_CORE_NO_RESCUE. Changing 90d to 60d, 120d, changing 30d exit, per-asset weights, sign, or adding a regime filter after seeing the result is prohibited.

If it passes, it is only a candidate for the Growth Core slot. No validation or final holdout is opened until a complete V98 architecture is frozen under the North Star process.
