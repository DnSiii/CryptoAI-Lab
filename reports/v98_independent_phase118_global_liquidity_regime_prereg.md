# V98 Independent — Phase118 WALCL Global Liquidity Regime preregistration

Status: PREREGISTERED AFTER Phase117 PASS_DATA_ONLY AND BEFORE ANY WALCL VALUE/DISTRIBUTION/CRYPTO-JOIN/PNL INSPECTION.

## Scientific hypothesis
Weekly expansion of the Federal Reserve balance sheet is a coarse global-liquidity tailwind for crypto risk assets; weekly contraction is a headwind. Test this as a deliberately simple directional regime, not as a parameter search.

## Frozen information set and causality
Source is exactly the Phase117 WALCL/FRED source and frozen training window 2023-01-01 through 2025-12-31. Phase117 must equal PASS_DATA_ONLY.

For each WALCL observation date t, define the signal only from the sign of the change versus the immediately preceding WALCL observation. To avoid publication-timing/look-ahead ambiguity, the signal becomes tradable at 00:00 UTC on calendar day t+2 and remains fixed until the next signal activation. No same-day use, interpolation, source substitution, alternate release lag, smoothing, threshold, or lookback search is allowed.

## Frozen portfolio
Assets: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT. Gross cap: 0.75, equal weight.

- WALCL weekly change > 0: long basket.
- WALCL weekly change < 0: flat.
- WALCL weekly change = 0 or unavailable: flat.

No short sleeve is allowed in this hypothesis. This choice is economic/prior-driven: liquidity expansion is tested as a risk-on permission gate, while contraction simply removes risk rather than assuming symmetric short alpha.

## Evaluation and costs
Training only. Preserve frozen chronological folds from config/v98_independent.json. Evaluate BASE, severe, and supersevere transaction/funding assumptions through the existing V98 exact execution engine. Report total return, max drawdown, daily Profit Factor, payoff, win rate, positive days, worst day, regime metrics, tails, concentration, per-asset contribution proxy, maximum open gross, state counts, and an always-long 0.75-gross context benchmark.

## Frozen training gates
All must pass:
- aggregate total return > 0;
- aggregate daily Profit Factor > 1.10;
- max drawdown >= -35%;
- worst day >= -12%;
- every frozen chronological fold: return > 0 and daily PF > 1.02;
- severe and supersevere: return > 0 and daily PF > 1.00;
- no single asset >45% of absolute contribution proxy;
- top-10 absolute daily-return share <=60%;
- maximum open gross <=0.75;
- both expansion and non-expansion states must occur.

Any failure => REJECT_NO_RESCUE. No threshold/lag/gross/asset/window tuning after results.

## Isolation
Validation and final holdout remain untouched. Phase083 is not selection evidence. V16 and V99 are forbidden. No V99 workflow/report/state may be read for tuning or selection. No parameter search or rescue is allowed.
