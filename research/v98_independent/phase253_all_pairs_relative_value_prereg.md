# V98 Independent Phase253 — All-Pairs Relative-Value Mean Reversion Sleeve

Status: PREREGISTERED BEFORE PHASE253 PNL.

## Architecture role

Phase253 fills the **Relative-Value Sleeve** slot on top of the frozen partial V98 architecture:

1. Growth Core primitive: structural Clean-4 beta, +0.25 each.
2. Frozen Opportunity Sleeve candidate: Phase252 carry-subsidized +0.0625 each when mean trailing 168h funding <= 0.
3. New Phase253 Relative-Value Sleeve: market-neutral redistribution driven only by pairwise relative-price dislocations.

Phase252 parameters remain frozen and unchanged.

## Novelty / anti-selection

A repository-wide V98 namespace search before Phase253 PnL found no prior V98 implementation or preregistration for:
- cointegration,
- pairs trading,
- pair spread,
- log-price ratio mean reversion,
- all-pairs relative-price z-score.

To avoid pair-selection multiplicity, Phase253 uses **all six unordered Clean-4 pairs**. No pair is selected or excluded from historical performance.

## Frozen signal

Pairs, fixed lexicographically from the Clean-4 universe:
- BTCUSDT / ETHUSDT
- BTCUSDT / BNBUSDT
- BTCUSDT / SOLUSDT
- ETHUSDT / BNBUSDT
- ETHUSDT / SOLUSDT
- BNBUSDT / SOLUSDT

For each pair A/B:

1. Hourly relative-price series = log(close_A / close_B).
2. At each 23:00 UTC decision after close(t), compute:
   - reference mean over the previous **720 hours / 30 days**, excluding the current observation;
   - reference standard deviation over the same prior 720h window;
   - z(t) = [logratio(t) - prior_mean] / prior_std.
3. Pair state is persistent and belongs to {-1, 0, +1}:
   - flat -> +1 (long A / short B) if z <= -2.0;
   - flat -> -1 (short A / long B) if z >= +2.0;
   - +1 -> -1 on z >= +2.0; otherwise exit to 0 when z >= -0.5;
   - -1 -> +1 on z <= -2.0; otherwise exit to 0 when z <= +0.5;
   - otherwise preserve state.
4. Sum the six pair states into raw asset overlay exposures.
5. Because every pair contributes equal and opposite legs, raw overlay net exposure must equal zero.
6. If the raw overlay is nonzero, normalize it to exactly **0.50 gross** (= 0.25 long + 0.25 short). If zero, sleeve is flat.
7. Add this net-zero overlay to the frozen Phase252 target.
8. The resulting integrated target must remain non-negative for every asset and preserve the Phase252 total net/gross target:
   - gross/net 1.00 when Phase252 opportunity is OFF;
   - gross/net 1.25 when Phase252 opportunity is ON.
9. Decision after 23:00 close(t) executes next 00:00 open and persists until the next daily decision.

## Frozen constants

- pair reference window: 720h
- entry |z|: 2.0
- exit |z| boundary: 0.5
- RV sleeve gross: 0.50
- decision hour: 23:00 UTC
- all six pairs mandatory
- no hedge-ratio fitting, cointegration selection, beta fit, pair subset, window grid, threshold grid, sleeve-size search, regime filter, stop, or post-result rescue

This is a fixed relative-price dislocation hypothesis, not a claim that each pair is statistically cointegrated.

## Data / execution

Authenticated Phase243 Clean-4 only:
BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT.
December 2022 warmup; training 2023-2025 only.
Native V98 funding.
XRP quarantined.
No 2026+, validation, holdout, V14, V15 or V99.

Existing V98 BASE/SEVERE/SUPERSEVERE cost and funding multipliers unchanged.
Integrated open-gross cap = 1.25.

## Frozen comparator

Exact frozen Phase252 partial architecture under identical data, execution, costs and funding.

## Relative-Value promotion gate

Phase253 becomes **RELATIVE_VALUE_SLEEVE_CANDIDATE** only if all are true:

1. BASE integrated return > Phase252 BASE return by at least 3% relative.
2. BASE integrated CAGR > Phase252 CAGR.
3. BASE daily PF >= Phase252 PF.
4. BASE max DD is not worse than Phase252 by more than 3 percentage points.
5. BASE worst day >= -20%.
6. Marginal calendar return versus Phase252 positive in at least 2/3 folds.
7. No calendar fold underperforms Phase252 by more than 5 percentage points.
8. SEVERE integrated return > Phase252 SEVERE return.
9. SUPERSEVERE integrated return > Phase252 SUPERSEVERE return.
10. No ruin.
11. Max open gross <= 1.250000001.
12. RV overlay net exposure <= 1e-12 at all times.
13. RV overlay gross <= 0.500000001.
14. Max absolute asset PnL contribution share <=70%.
15. Top-10 absolute daily-return concentration <=45%.

Failure => REJECT_RELATIVE_VALUE_NO_RESCUE for this exact all-pairs 30d z2/0.5 / gross0.50 sleeve. No validation/holdout.
