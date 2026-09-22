# V98 Independent Phase097 — Relative DeFi TVL momentum preregistration

Status: **PREREGISTERED / TRAINING ONLY / PARAMETERS FROZEN BEFORE PNL**.

Phase096 passed data feasibility for both frozen DefiLlama historicalChainTvl series: Ethereum and BSC each supplied 1,096/1,096 training-era calendar days, zero duplicate days, zero invalid rows/values, full 2023-01-01..2025-12-31 coverage and raw SHA-256 evidence. Phase097 is the single authorized alpha test for this information class.

## Frozen causal signal

At UTC day t, use only TVL observations dated strictly before t. For each chain compute the 7-calendar-day TVL return from the latest available prior-day TVL versus its value 7 calendar days earlier. Compare Ethereum with BSC. If Ethereum's 7-day TVL return is strictly greater than BSC's, hold ETHUSDT long and BNBUSDT short. If BSC's is strictly greater, hold BNBUSDT long and ETHUSDT short. Exact ties or unavailable lagged inputs => cash. No absolute TVL level, crypto price, future TVL observation, stablecoin series, threshold, z-score, volatility transform, or second signal is used to form the decision.

## Frozen exposure and execution

Rebalance once per UTC day at the first canonical daily boundary after all required prior-day TVL observations are known. Active gross exposure is 0.75: +0.375 on the stronger-TVL chain token and -0.375 on the weaker-TVL chain token, therefore dollar-neutral by construction. No leverage scaling, volatility targeting, regime filter, threshold search, stop, take-profit, chain/symbol subset, alternate lookback, alternate source, rescue, or parameter sweep.

Funding is charged using canonical point-in-time funding data. Turnover costs are charged on every absolute weight change. BASE / severe / supersevere cost and funding conventions are frozen to the existing V98 Independent canonical evaluator and may not be relaxed after results.

## Training and mandatory gates

Selection interval is training-only through 2025-12-31 with chronological 2023, 2024 and 2025 folds. Validation remains closed. Phase083 and every 2026 observation are forbidden.

PASS_TRAINING requires all of: aggregate net return >0; daily Profit Factor >1.10; max drawdown >=-35%; every chronological fold net return >0; severe return >0 and PF >1.0; supersevere return >0 and PF >1.0; no single asset contributes >60% of absolute aggregate contribution; top-10 absolute daily-return share <=60%; plus standard V98 regime, concentration and tail diagnostics with no causal/integrity failure. Report CAGR, max drawdown, PF, payoff, win rate, positive days, folds, regimes, concentration/tails, turnover/cost/funding decomposition where exposed by the canonical evaluator, and reproducibility hashes for source payloads, targets and this preregistration.

Any failed mandatory gate => **REJECT_NO_RESCUE**. PASS_TRAINING only authorizes a separately frozen validation phase. It does not authorize final holdout.

## Isolation

No V99/V16 evidence. No Phase083 selection use. No 2026 tuning. No alternate TVL source, chain, symbol, direction, lookback, threshold, gross, regime, cadence, cost or funding rescue after PnL is observed. Phase060/061 stablecoin liquidity remains closed and cannot be reused or combined with Phase097.