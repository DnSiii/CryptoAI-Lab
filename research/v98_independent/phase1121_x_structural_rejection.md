# V98 Independent Phase1121 — X complete-portfolio structural rejection

2026-10-23. X is **REJECTED before historical PnL**, without sign/window/gross/cost rescue.

Evidence: source-only Phase1116-1118 CI https://github.com/DnSiii/CryptoAI-Lab/actions/runs/39978442261 passed 20 unit contracts (8 basket, 4 governor, 8 seven-slot) and 4,000 synthetic adversarial cases. This establishes component correctness, NOT survival/CAGR.

Official complete synthetic Phase1120 https://github.com/DnSiii/CryptoAI-Lab/actions/runs/39978811421 executed 3 fixed seeds (1120/1121/1122) x 5 ablation paths = **0/15 complete survival**. All 15 paths failed with `X_POST_BASKET_SURVIVAL` at hours 721–1144. This is synthetic data, not authenticated Binance historical PnL. No 2025, holdout or V14/V15/V99 data accessed.

Root cause: the X 256-state governor certifies static open/adverse/stop/partial scenarios at each 12h target update, while live signed holdings drift with market marks between updates. A long can appreciate without touching its partial-profit limit and cross the .45 asset cap, even when the target was feasible at t-1. Example from the seeded synthetic oracle: a .449068 BTC target reached approximately .450566 of post-fee equity with no stop; this violates the hard cap. Whole-basket stop protection solves hedge-removal but not continuous concentration drift. No realistic claim of guaranteed survival from static state enumeration is warranted.

**Decision: X_full STRUCTURALLY REJECTED.** Preserve X code, preregistration, CI and synthetic receipts unchanged. Do not loosen caps, tweak windows, change signs, raise leverage, choose a favorable seed or hide the failure. The next genuinely distinct architecture must include a causal, self-financing **continuous reduce-only concentration feedback controller**, with alpha target updates kept separate from safety interventions and full cash/capacity/mark accounting. Wealth/CAGR remains the objective, survival a constraint.
