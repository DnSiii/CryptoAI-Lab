# V98 Independent Phase243 — source contract audit (2026-10-09 15:43 BRT)

Decision: **DATA_ONLY / NO_CHAMPION / HOLDOUT_UNOPENED**.

The branch `research/v98-independent-zero` was audited at commit `e608904c35e68b3ff3c68e7aa6746692336ee352`. The 185 original USD-M Binance 1h ZIP archives for the frozen five assets, 2022-12 through 2025-12, are still absent from the branch. Existing native V98 Phase206 funding files are present. No Phase243 historical integrated backtest has been verified.

## Newly detected cross-stage mismatch

The locally prepared acquisition workflow called `phase243_price_source_integrity.py` with its default 336-hour warmup, but the frozen `phase243_cross_stage_source_lock.py` contract requires 744 hours and 27,048 observations per asset. A workflow could pass the independent price gate yet fail later cross-stage reconciliation. The next source workflow must explicitly set `--warmup-hours 744` and independently reconcile every acquisition/provenance/canonical/price/funding manifest against the original file bytes. An independent gate must fail closed on 336-hour warmup, duplicate/missing archive IDs, checksum or source-byte mutation, altered canonical prices, changed native funding, or a holdout-access claim.

## Independent Phase240 economic falsification (no retuning)

The remote frozen `phase240_results.json` contains 8 preregistered specifications × 3 chronological years × 3 cost tiers = 72 annual cases. All 72 returns are negative; 0/216 regime slices have nonnegative returns; 72/72 have a more negative 1% tail than the positive 99% tail. Base: best return -95.762569%, maximum Profit Factor 0.68999, maximum positive-day fraction 20.4918%. Severe: best -99.853220%, maximum PF 0.47260. Supersevere: best -99.9998097%, maximum PF 0.24416. Every specification/year is monotonically worse as costs increase. This is **negative evidence**, not a basis for rescuing Phase240 through regime filtering, sign flipping or asset selection.

## Publication/validation separation

Local, uncommitted acquisition code and synthetic tests do not constitute real source authentication or historical alpha. Provider SHA256 sidecars are integrity checks, not publisher digital signatures. The next gate is acquisition of all authentic training ZIPs with sidecars, independent replay, deterministic SHA256 evidence, and strict exclusion of 2026+ observations. Only then may a frozen seven-slot V98 engine proceed to chronological training, realistic signed funding, severe/supersevere costs, tail/concentration/regime and drawdown/profit-factor/payoff/win-rate/positive-day checks. No V16/V99 files, workflows, branches or paper state may be modified.
