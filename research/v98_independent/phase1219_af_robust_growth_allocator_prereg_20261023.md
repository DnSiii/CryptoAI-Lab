# V98 Independent Phase1219 — AF robust net log-growth deployment allocator prereg (2026-10-23)

AF slot 6, causal long-only growth allocation. This is **not** AD multiplicative wealth experts or AE fractional-Kelly posterior. Maximize credible net compounded growth while enforcing cash collateral and no hidden leverage; do not optimize minimum risk as objective.

At completed hour t, attribute each of three **previous** AF sleeve intents (Growth, Opportunity, RV) to completed 4-asset close-to-close returns and signed native funding event t. Subtract precommitted virtual 0.0012 of previous intent turnover per sleeve; use log1p of each net sleeve return, rejecting <=-100% or nonfinite. Retain 336 completed hours per sleeve. Before full history, fixed baseline sleeve budget [0.70,0.20,0.10].

After 336 hours, split each sleeve's prior log returns into **four contiguous 84h blocks**. Credible log-growth score = median(block means) - 0.5*population_std(block means); positive component only. Apply deterministic score multiplier 1+500*max(score,0) to fixed baseline budget, then regime factors: risk-off [0.60,0.50,0.70], transition [1,1,1], risk-on [1.30,1.20,1.00]. Normalize sleeve weights to 1. This is a growth-deployment budget, not a posterior probability or Kelly division by variance.

Compute weighted long-only 4-asset sleeve intent, then enforce **actual prefunded cash**: desired gross <=1-cash_reserve, with reserve exactly Phase1217's 0.10 or 0.55; if necessary scale all longs proportionally, leaving residual cash. No short or leverage. This is source-only: actual fills, funding, fees, 81-corner governor and realized NAV must be verified later. Decision at close t may execute only at next open t+1.

Tests: strict prior virtual holdings, turnover/funding sign, fixed 336h 4-block window, regime factors, reserve scaling, no short/gross, deterministic reproducibility. No historical PnL, 2025, XRP or external benchmarks.
