# V98 Independent Phase891 — K realized-volume execution audit (source-only)

Date: 2026-10-21. Branch: `research/v98-independent-zero` only.

Frozen K paths, Clean-4 Dec-2022 warmup / 2023–2024 analysis, no 2025+, XRP, holdout or external engines. Ten fixed-NAV cases (five paths × $1m/$10m). Target and quote volume from t-1 determine t fill; quote volume at t is used **only after the fill** to audit realized hourly participation. This is not a backtest or realized PnL.

**K_full $10m:** 2023: 1,473 of 8,612 filled asset-hours (17.1%) exceed 5% of the contemporaneous hour's reported quote volume; excess relative to that cap is $319.4m. 2024: 721 of 7,146 (10.1%), excess $204.7m. **K_full $1m:** 83/7,188 (1.2%) in 2023 and 33/6,452 (0.5%) in 2024. Across all ten cases: 10,460 asset-hour cap overruns. These are not actual trading losses or executable PnL.

**Interpretation:** a fill sized at 5% of *prior* hour volume can materially exceed 5% of the *realized* current hour volume. Current-hour volume is unknown at open; using it for order sizing would introduce lookahead. This ex-post diagnostic does not prove fills are impossible, but the prior-volume assumption is optimistic and cannot by itself certify execution. No parameter, sign, window, target or frozen path changed. K and J remain economically unapproved; next gate is fresh official funding/mark and all 90 historical economic cells, followed by independent validation.
