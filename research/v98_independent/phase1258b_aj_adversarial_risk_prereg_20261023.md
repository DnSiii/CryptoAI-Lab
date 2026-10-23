# V98 Independent Phase1258b — AJ governor deterministic adversarial property audit prereg (2026-10-23)

This is a **post-freeze, pre-result independent audit of the unchanged AJ1257 Risk Governor**, not a new alpha/parameter/threshold rescue. Do not modify the frozen AJ1255–1258 strategy regardless of results. The complete 180-cell structural run 40018258365 was already launched; audit must not influence that frozen result.

Generate 5,000 synthetic t-open scenarios with fixed numpy RNG seed 1258: cash $10k; four prices $100*exp(N(0,.03)), old signed units N(0,5), desired signed target N(0,5), prior quote/min quote uniformly between $1m and $100m, prior downside .45–.70, prior upside .80–1.20, funding bound .0005–.0015, fee modes base/severe/supersevere and both native funding timing orders. All opening price, old units, prior quote and risk values are known at decision time; no future market data.

For every scenario, call AJ1257 governor twice with identical inputs. Accepted orders must have bitwise identical units, nonnegative actual-open cash, no hidden borrow, order delta <=0.003*min(prior quote, prior min quote), exit capacity <=0.003*min quote/(2.2*opening*(1+up)), actual fee/funding reserve and conservative 24h stress collateral test PASS. Rejected scenarios must throw an explicit ValueError; do not label rejection as success. Record counts by category, accepted/rejected, max constraint residual, deterministic output digest and no historical PnL. **Any false feasible order or nondeterministic repeat fails the audit and blocks AJ promotion**; no strategy tuning after result.

Only V98 Independent namespaced files on research/v98-independent-zero. No 2025 validation, 2026+, XRP, Phase083 or V14/V15/V99; frozen V16/V99 untouched.
