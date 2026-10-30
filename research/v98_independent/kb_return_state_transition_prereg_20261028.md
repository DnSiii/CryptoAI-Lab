# V98 Independent KB — preregistered binary return-state transition architecture (2026-10-28)

**Immutable ex-ante seven-slot hypothesis.** Register BEFORE implementing KB source code or computing KB PnL. KA, JZ, JY and all earlier rejected systems remain terminally rejected. This is not an alteration, reweighting, or resurrection of any rejected sleeve. Unlike recent OI/5m/basis architectures, KB tests whether *conditional one-hour return-sign transition probabilities* contain investable cross-asset information not captured by unconditional momentum. No parameter grid or ex-post changes.

## Authenticated universe and causal protocol
Exact pinned Clean-4 BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT Binance USD-M 1h Dec2022–Dec2024, artifact 40064588623, publisher/native signed funding and mark. No OI, spot, 5m, XRP or external inputs. Hourly native funding-net log return = log(C[t]/C[t-1]) - signed funding rate[t] * funding event[t]. Only completed observations through t are used for t+1 real opening execution. 744-hour warmup, 168-hour rebalancing. 2025 is separately locked validation, 2026+ untouched holdout, Phase083 contaminated. Never inspect V14/V15/V99 internals, Frozen or paper.

## Seven fixed slots
1. Growth Core: top two assets by 672-hour funding-net log return / 336-hour downside semivol (floor .002), inverse-downside semivol weights. Common prospective long-growth control; not a recovered rejected sleeve.
2. Opportunity: compute Laplace-smoothed 672h two-state transition probabilities P(up|up) and P(up|down) using 671 observed transitions; P(up|last sign) and normalized binary conditional entropy. Long asset with highest positive `(P(up|last)-.5) * (1-entropy) * max(72h net return,0)`; if all zero, budget returns to Core. Budget .16.
3. Relative Value: long 50% of highest and short 50% of lowest conditional P(up|last), only if cross-sectional spread >.015; otherwise return capital to Core. Budget .12. This is a signed conditional-state probability spread, not a momentum or OI spread.
4. Stress/Recovery: STRESS long highest P(up|down), RECOVERY long highest P(up|down), NORMAL long highest `P(up|last)*(1-entropy)`. Budget .12.
5. Regime Router: STRESS if equal-weight last-72h funding-net return < -.025; else RECOVERY if last-24h > .012 and preceding 72h <0; else NORMAL.
6. Dynamic Allocator: deterministic 168h epochs, fixed eligible budgets Opportunity .16, RV .12, Stress .12, Core residual >= .60. Inactive/ablated budgets independently finance Core. No hidden leverage or post-PnL optimization.
7. Risk Governor: existing audited GL order-invariant shared-collateral 81-corner conservative governor, prior-only exit and tail bounds, next actual open, native mark/signed funding, 3 cost tiers, both funding orders. Gross multipliers NORMAL .88, STRESS .70, RECOVERY .82; gross <=1.

## Immutable source and economic gates
Before system PnL: exact pinned manifest, synthetic future-mutation invariance, all targets finite, gross/collateral conservation, and >=8 funded full-minus-optional L1 differences >.025 for each sleeve in EACH 2023/2024. Source gate failure terminally rejects KB before PnL.

If source passes, run five separately funded USD10k books (Core, Full, Full-minus-Opportunity, Full-minus-RV, Full-minus-Stress) x three base/severe/supersevere cost tiers x two funding orders on Ubuntu 22.04/24.04: 30 distinct physical cells / 60 original receipts, independent original-artifact-only cross-OS audit, independent each-hour signed funding and 81-corner settlement oracle. Complete Full must show base CAGR >50%, severe >30%, positive 2023 AND 2024 net log growth base/severe, severe DD <45%, turnover <=USD600k base/severe, and each optional Full-minus-ablated combined log-growth >.02 base/severe with each annual >=-.03. Include PF, payoff, win rate, positive days, tails, concentration, funding, fees and slippage. Any failure rejects KB permanently; no sign/window/threshold/gross/weight rescue. Only complete training pass can be internally frozen then tested separately on 2025. Only after that may external benchmarks be opened. No paper or live authorization.

## Interpretability and falsification
Hourly sign transitions may be close to memoryless; this is a high-risk economic hypothesis, not a claim of exploitable predictability. If empirical conditional edge fails to cover costs, reject without replacement tuning. 2023–24 has been repeatedly mined in other experiments; any positive training result is multiply selected and cannot establish out-of-sample success.
