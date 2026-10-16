# V99 R106 C1 — complete-engine TRAIN gate, independent journal oracle, PERMANENT REJECT

Date 2026-10-16 UTC. Original C1 parameters/spec frozen **before** historical C1 PnL: `research/V99_R106_C1_TRAIN_ISOLATION_NOTE_20261016.md`. Hypothesis integrated BTC+ETH growth, risk-scaled allocator, lagged 3x2 regime controller and drawdown/cash-lock governor. C1 is a distinct complete-system economic experiment, not a retune of previously rejected standalone signals.

## Actual official execution
- Original complete-engine strict TRAIN GitHub Actions run: [38915660133](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/38915660133), **SUCCESS as software execution**, 9/9 pre-economic software tests, two byte-identical economic evaluations, reproducible severe hourly journal.
- Independent source-open/position/fee/net/equity journal audit: [38916067167](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/38916067167), **SUCCESS**, 9/9 C1 software invariants + 5/5 independent accounting oracle adversarial tests. Verified all **16,055 hourly rows PER cost scenario** directly against original frozen TRAIN-only BTC/ETH opens. Both independent compound ROI values and modeled total fees reconciled to the frozen C1 report; original SHA256 hashes matched.
- No final holdout or sealed validation price values parsed; C1 economic TRAIN ends 2023-10-01 UTC exclusive. Final holdout 2024-01-18 UTC onward remains unopened. No Frozen engine, published paper ledger, original champion or real order changed.

## Historical preliminary TRAIN economics — NOT exchange-certified futures profitability

| Metric | Severe cost 0.0007/side | Supersevere cost 0.0014/side |
|---|---:|---:|
| Compounded ROI (assumed fees, pre-funding) | **−20.7856%** | **−3.4081%** |
| Positive chronological folds | **1/5** | **2/5** |
| Fold 1 | −2.4432% | +0.6760% |
| Fold 2 | +7.1502% | +33.7894% |
| Fold 3 | −11.4385% | −13.0236% |
| Fold 4 | −3.4282% | −5.2369% |
| Fold 5 | −11.3949% | −12.9934% |
| Maximum drawdown | Not reported here (refer to original artifact) | **−43.6620%** |

Seven pre-committed economic gates failed: both total ROI signs, severe >=4/5 folds, supersevere >=3/5 folds, profit factor >1 in both cases, remove-best-day robust positivity in both cases, and supersevere drawdown no worse than −35%.

**Counterintuitive cost observation:** increasing the cost per side produces a less negative total on this portfolio in the historical run. The engine has path-dependent drawdown locks and risk scaling based on its earlier simulated NAV, so higher transaction costs can trigger different exposure timing; consequently monotonicity of *whole-path* ROI across cost scenarios is not guaranteed. The independent oracle establishes accounting identity, not that different exposure schedules are a valid alpha edge or that actual costs are modeled correctly. Any forensic attribution must remain READ_ONLY; it may never justify choosing the more flattering cost regime.

## Decision

**C1 COMPLETE ENGINE IS PERMANENTLY REJECTED WITHOUT RETUNE.** Do not revise its 720h average, 168h momentum/volatility, gross caps, directional signs, regime thresholds, 168h lock, drawdown cutoffs, cost constants or TRAIN window to rescue it after observing its economics. No candidate is promoted, no valuation/paper published. The original C1 simulation remains preserved via immutable GitHub Actions artifacts, not presented as real forward trading.

The shortest credible next path is a *scientifically distinct pre-registered complete-engine economic mechanism*, protected from 2023-10-01→2024-01-18 sealed validation until it passes all TRAIN gates, and from final holdout until independently frozen. Native OKX fee-tier/funding-settlement/fills must be independently sourced and accounted for before declaring a deployable version. Building yet more isolated feature variants is not sufficient.

The V99 hourly research automation and prospective first-party receipt workflows continue separately. **Software test green ≠ profitable trading engine.**

## Independent paired-cost failure attribution — archived after original rejection

- Actual GitHub Actions [38916545664](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/38916545664) **SUCCESS**: 9 C1 invariants + 5 original-price journal accounting oracle adversarial tests + 4 no-retune scenario-tail forensic tests, all passed, with the original frozen strategy unchanged.
- **16,055 exactly aligned hourly observations per scenario**, not reconstructed history.
- **392 hours differ in actual BTC/ETH exposure between severe and supersevere runs**, despite identical signals/parameters; **501 governor cash-lock hours in each**. The different exposure timing helps explain why a larger modeled per-turnover cost can coincidentally produce a less negative compounded result. It does NOT vindicate the higher-cost strategy and must never be used to optimize the governor.
- Hash-grounded forensic output and both hourly journals remain archived in the GitHub Actions artifact. No new C1 economic hypothesis, no final holdout, no validation data, no new champion.
- Architecture-level lesson, not a rescue: any future independently preregistered integrated system must explicitly report **both fixed-target counterfactual costs and causal path-dependent live risk controls** to avoid misleading cost robustness comparisons. The cost-path divergence evidence is descriptive ONLY; it cannot justify retuning C1, backtesting a family of ad hoc fixes, or claiming net real-market returns.
