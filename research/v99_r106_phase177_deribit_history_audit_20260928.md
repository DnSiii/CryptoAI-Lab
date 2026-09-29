# V99 R106 — Phase177 Deribit history audit

Date: 2026-09-28
Scope: DATA/PROVENANCE ONLY. No alpha, PnL, parameter selection, or holdout access.

## New first-party evidence

Deribit institutional documentation states that the exchange offers historical trade and instrument information since launch (2016) through dedicated `history.deribit.com` public endpoints. The documented historical database is updated approximately five seconds after a trade occurs. Relevant endpoints include `public/get_instruments` and `public/get_last_trades_by_*_and_time`, with `include_old=true` for expired instruments.

This materially improves Phase177 provenance: option instruments and option trades across the frozen TRAIN can be reconstructed from a first-party Deribit historical service rather than requiring a third-party replay archive.

Separately, Deribit first-party material establishes that DVOL began publication on 2021-03-31 and is a 30-day annualized implied-volatility index derived from the options IV smile. Therefore the economic family predates TRAIN start 2021-12-01.

## Important limitation

The newly documented history endpoints establish first-party historical option trades/instruments, but the inspected evidence does **not** yet prove a first-party endpoint returning historical option IV/Greeks or the historical DVOL index itself for every timestamp in `[2021-12-01, 2024-01-18)`.

Reconstructing an IV surface from historical trades would additionally require contemporaneous underlying/index inputs and a fully preregistered deterministic pricing convention. That is scientifically possible in principle but is **not** silently introduced here because doing so before a reconstruction specification and integrity gate would add researcher degrees of freedom.

## Causal implications

The documented ~5 second history-database update lag means trade observations have explicit publication latency. Any future admissible feature must use event timestamp plus a conservative availability lag and then the existing causal t-1 shift. No same-event execution is permitted.

## Decision

**PHASE177 remains DATA-GATE / NOT ADMITTED FOR PnL.**

Evidence upgraded:
- first-party historical option instruments/trades exist across the relevant era;
- service provenance is Deribit itself;
- explicit approximate publication latency is documented;
- DVOL existed before TRAIN.

Still required before alpha:
1. prove a deterministic first-party path to historical DVOL or IV, or preregister a no-choice IV reconstruction;
2. prove full TRAIN coverage and temporal-fold coverage;
3. build hashes/manifests, timestamp monotonicity, duplicates/gaps, expired-instrument handling;
4. enforce `[2021-12-01, 2024-01-18)` firewall and t-1;
5. only then preregister one fixed hypothesis before inspecting PnL.

No third-party backfill is substituted. TRAIN is not shortened. Holdout is untouched. V16 Frozen and V99 Frozen are untouched.
