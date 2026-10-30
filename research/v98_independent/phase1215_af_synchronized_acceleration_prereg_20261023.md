# V98 Independent Phase1215 — AF synchronized 6h positive acceleration opportunity prereg (2026-10-23)

AF slot 2, source-only. Do not import AD funding-surprise or AE channel breakout signals, rejected performance, future holdout or external benchmarks. Clean-4 1h causal source validated by Phase1214, no historical system PnL.

At completed hour t compute each asset's 6h log return log(close[t]/close[t-6]). Its comparison distribution contains exactly **336 prior completed 6h returns ending t-1**. Compute median and MAD, robust sigma = 1.4826*max(MAD,0.001). Positive acceleration event if current 6h return > max(0, median+3*robust_sigma), and strictly prior 336h quote minimum >0. Require at least **two** simultaneous Clean-4 positive events, otherwise do not initiate a new opportunity position.

Upon confirmation, set an equal-weight **long-only** gross 0.20 opportunity sleeve among qualifying assets, with 12 completed-hour persistence from the last valid trigger; no short, leverage or free stop. Repeated genuine triggers may renew the 12h timer. All decisions at completed close t are eligible only at next open t+1. This is complementary growth convexity, not a standalone alpha search.

Gate: 342h strict baseline warmup, t-1 robust distribution, positive synchronized event, 12h expiry, no lookahead, no short/gross excess, deterministic synthetic reproducibility. No parameter rescue after economic results.
