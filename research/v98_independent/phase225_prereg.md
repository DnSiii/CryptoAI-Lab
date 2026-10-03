# V98 Independent — Phase225 preregistration

Status: **PREREGISTERED_ONLY — DO NOT EXECUTE BEFORE PHASE224 DATA BLOCK IS DISPOSED**
Holdout: 2026+ CLOSED.

## Scientific question
Does short-horizon **cross-sectional intraday reversal after an abnormal volume shock** contain a robust, cost-surviving crypto-perpetual effect independent of funding-dislocation and residual-momentum families?

This is preregistered now only to preserve continuity while Phase224 is blocked on realized-funding provenance. It must receive a historical-family independence audit before implementation/execution.

## Frozen universe / folds
Assets: BTC, ETH, BNB, SOL, XRP perpetuals.
Training folds: calendar 2023, 2024, 2025 independently.
No 2026+ access for development, selection, diagnostics, or rescue.

## Causal feature construction
At decision bar t, use only information through completed bar t-1.
For each asset at t-1:
- `r6`: trailing 6h close-to-close return ending t-1.
- `vol_ratio`: volume(t-1) / median hourly volume over the preceding 168 completed hours, excluding t-1 from the baseline.
- Cross-sectional return residual: `r6_i - median_j(r6_j)` over the five assets at the same t-1.

Entry at open(t). Direction is contrarian to the residual return, only when the asset had an abnormal volume shock.

## Exactly 8 frozen specs
Cartesian product:
- volume threshold V in {2.0, 3.0};
- absolute residual-return threshold R in {0.015, 0.025};
- holding horizon H in {4h, 8h}.

Names: `v{V}_r{R}_h{H}`. No other thresholds/horizons may be tried for this family.

## Portfolio / overlap
At each decision time, eligible assets satisfy `vol_ratio >= V` and `abs(residual_r6) >= R`.
Position sign = `-sign(residual_r6)`.
If multiple assets qualify, equal-weight active entries subject to gross exposure <= 1.0.
No overlapping position in the same asset; a new signal for an already-active asset is ignored until exit.
Exit after exactly H hourly bars using causal open-to-open accounting (entry open(t), exit open(t+H)).

## Costs and funding
Round-trip trading cost stresses are frozen at:
- base: 7 bp;
- severe: 14 bp;
- supersevere: 28 bp.

Realized funding cashflows, if charged by the shared V98 accounting engine, must be point-in-time and causally known at settlement. Absence of a validated realized-funding series must not be silently replaced by forecast/premium data; if funding cannot be charged consistently, execution is blocked rather than approximated post hoc.

## Required metrics
For every spec and every cost stress, report at minimum:
- return;
- max drawdown;
- Profit Factor;
- payoff ratio;
- win rate;
- positive-day rate;
- trade count;
- regime breakdown;
- asset contribution/concentration;
- closed-trade tails/quantiles;
- reproducibility SHA/invariants.

## Mechanical training gate
A spec is training-coherent only if, at BASE cost, **each** of 2023, 2024, and 2025 independently has:
- return > 0;
- Profit Factor > 1.0;
- positive-day rate > 0.50;
- trade count >= 30.

Additionally:
- severe and supersevere results must deteriorate monotonically versus base in aggregate net return;
- no single asset may contribute >70% of aggregate positive PnL without an explicit concentration failure flag;
- invariant/reproducibility checks must pass.

Passing the training gate is not permission to open 2026+. A separate frozen holdout protocol is required after a candidate survives full training diagnostics.

## No-rescue rule
If 0/8 specs pass, close Phase225 as `REJECT_FAMILY_NO_RESCUE`. Do not alter V/R/H, add filters, remove bad years/assets, or reinterpret the gate using observed results. A failure moves research to a scientifically distinct preregistered family.
