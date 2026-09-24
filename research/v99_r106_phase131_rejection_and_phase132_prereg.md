# V99 R106 Phase131 rejection + Phase132 preregistration

## Phase131 decision
Phase131 — Idiosyncratic Volatility Shock Continuation is permanently rejected at the preregistered train-only severe gate. Evidence: ROI -70.3311%, PF 0.5303, max DD 70.3386%, robust mean ex-top1% -7.7086e-05/h, 0/4 healthy temporal folds. All four folds were negative. Causality invariants passed, holdout was not parsed, and V16/V99 Frozen remained untouched. No sign flip, window retuning, threshold search, or repair is permitted.

## Failure-mechanism audit
The failure is broad rather than tail-dependent: every chronological fold is negative and robust mean after removing the top 1% hours remains negative. Phase126-131 also show that direct hourly cross-sectional continuation/reversal transforms built from price/volatility alone are repeatedly overwhelmed under severe friction. The next hypothesis therefore changes the economic object rather than tuning another return window.

## Phase132 preregistration — Cross-sectional Volatility-of-Volatility Reversal
Scientific hypothesis: unusually unstable realized volatility relative to an asset's recent volatility-of-volatility baseline represents transient dislocation/exhaustion. Assets with the largest positive volatility-instability shock should receive negative cross-sectional score and unusually stable assets positive score. This is a reversal of volatility instability, not a sign flip of Phase131's RV-level shock.

Frozen specification before any Phase132 PnL:
- Input: hourly close log returns only.
- RV state: rolling 24h RMS return.
- Volatility-of-volatility: rolling 72h standard deviation of log(RV24 + 1e-12).
- Cross-sectional feature: current vol-of-vol divided by its own trailing 168h rolling median (plus 1e-12), then log transform.
- Cross-sectional normalization each hour: median removal and 1.4826*MAD scale; require >=8 valid assets.
- Direction: reversal of instability (`score = -tanh(robust_z)`).
- Causality: entire score shifted exactly one hour (`t-1`) before portfolio construction.
- Portfolio: cross-sectional L1 normalization; Phase132 sleeve gross allocation fixed at 0.20.
- Selection: chronological train only, ending exclusively at 2024-01-18T00:00:00Z.
- Costs: severe first; exact frozen spec may proceed only on PASS to supersevere, temporal/regime matrix, tails/concentration, benchmark envelope and reproducibility.
- Holdout: prohibited from parsing/inspection until the exact candidate has passed every upstream gate and is formally frozen.
- Single hypothesis, no parameter grid, no sign flip, no threshold search, no post-result window changes.

Decision rule: use the existing canonical train diagnostic and four temporal folds. PASS freezes this exact specification for downstream stress validation. FAIL permanently rejects Phase132 and forbids repair/tuning of this hypothesis.