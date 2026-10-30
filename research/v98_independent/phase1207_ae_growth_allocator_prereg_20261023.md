# V98 Independent Phase1207 — AE causal shrinkage log-growth allocator prereg (2026-10-23)

AE slot 6, independently preregistered before executable code or economic PnL. No AD multiplicative wealth posterior, no AC coordinate optimizer, no historical PnL, no 2025, no external benchmarks.

**Inputs at completed t:** completed close-to-close 4-asset returns and native signed funding at t, event mask at t, four new AE sleeve intents [growth, opportunity, relative-value, stress] produced at completed close t for **t+1 open**, and AE one-hot regime [off,transition,on] at t. Only previous virtual sleeve holdings contribute to realized t sleeve returns. Virtual turnover from the prior intent change is charged at conservative 0.0012 before new intent can influence t+1. All four sleeve net return histories retain at most 336 completed observations.

**Capital-growth allocator:** fixed prior budget [0.65,0.12,0.10,0.13]. After 336 observations, compute per-sleeve prior net mean and population variance. Fractional Kelly shrinkage score = clip(0.5 * mean/(variance+0.0004), -1, 2); strength = clip(1+score, 0.25, 3). Before 336, strength=1. Regime multipliers (off,transition,on) by sleeve:
- off: [0.60,0.60,1.10,1.50]
- transition: [1,1,1,1]
- on: [1.30,1.25,0.90,0.60].

Normalize positive budget weights to sum 1, then take weighted sum of next-open signed sleeve intents. No direct gross expansion, hidden leverage, risk metric optimization or post-result tuning. Actual cash/NAV, governor, fills and real costs are separate future gates; virtual forecast is **not** proof of realized profitability.

**Structural gate:** prior-only return attribution, native funding sign, turnover charge, deterministic fixed 336 window, future intent nonleakage, exact 3-regime routing, finite and valid signed intents, independent two-OS tests. Failed gate must be rejected or fixed only for implementation bugs without changing preregistered economic constants.
