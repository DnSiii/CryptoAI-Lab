# V98 Independent Phase696 — Architecture F preregistration (2026-10-19, 17:00 BRT)

## Immutable scope
Branch `research/v98-independent-zero`, files only under `research/v98_independent/`. Never touch V16/V99, V99 paper, external benchmarks, XRP, 2026+ bars or Phase083. Phase252 B and Phase646 E remain frozen and unchanged. F is a **genuinely distinct growth-first composed candidate**, not a cosmetic rescue of E; no PnL has been examined for F and no superiority is claimed.

## Seven slots (fixed before structural results)
1. **Growth Core**: frozen Phase252 Clean-4 target (0.25 or 0.3125 each), digest `f18fe648a9994de28a8e8f13eb85d7031d818baf629fe90d561d7cb5a31ea8a4`. Never alter its signals.
2. **Opportunity Sleeve**: **additive convex trend exposure**, not E's zero-sum monthly transfer. At each daily 23:00 UTC close, when routed to growth, require at least three positive 720h log returns, positive BTC 720h return, and strongest asset's 168h return > +0.05 and 24h return > 0. Allocate +0.15 to the 168h leader, held until next daily decision; otherwise zero.
3. **Relative-Value Sleeve**: when routed to mixed, on each Monday 23:00 UTC decision choose within the BTC/ETH or BNB/SOL pair with the largest positive 168h return spread, requiring spread >=0.08 and winner's 24h return >0. Transfer 0.05 from pair laggard to leader, holding that pair until next Monday decision; otherwise zero. This is trend dispersion, not E's monthly neutral mean reversion.
4. **Stress/Recovery Sleeve**: in stress, if BTC 168h log return <=-0.12, BTC 24h return >+0.03 and at least three assets have positive 24h return, add +0.10 to the 24h return leader for exactly 48 hourly decisions, then 72-hour cooldown. No hindsight episode boundaries.
5. **Regime Router**: daily 23:00 UTC. Growth if >=3 positive 720h returns and BTC 720h>0; else stress if BTC 168h<=-0.12; else mixed. Only one sleeve may contribute at once.
6. **Dynamic Allocator**: growth core plus exactly one active overlay; additive gross at most 1.40 (core <=1.25, opportunity +0.15), RV transfer conserves gross. Never silently scale down the core or retrospectively pick a favorable sleeve.
7. **Risk Governor**: hard gross <=1.45, per-asset <=0.70, long-only nonnegative, no trade at zero-volume open, t-1 close to next-hour open, exact chronological UTC hourly index, deterministic tie breaks in fixed asset order.

## Data isolation and acceptance
Structural execution tests use **only Dec-2022 warmup and Jan-2023 through Dec-2024 training** Clean-4 1h prices and the immutable Phase252 daily-decision replay bits. Do not read 2025 returns/metrics for design or selection. All seven slots must be present, exactly three sleeve ablations plus B, and future-mutated training inputs must not change prior targets. Preregister before implementation; no grids, no sign/window/threshold/size rescue. Evaluate structural validity, activation, turnover and feasibility **without any historical PnL**. Freeze code/digests if structural tests pass, otherwise reject F hypothesis. F cannot be promoted or benchmarked before fresh 148 official funding ZIP/CHECKSUM + 13,524 API mark attestation and separate chronological funded economic validation with 7/12/20bp and both funding orders. Do not use E results to tune F.

## Priority
Growth and net compounded wealth/CAGR are the eventual objective; caps, drawdown and tails are survival constraints, not the optimization target. No artificial upside ceiling.
