# V98 A3 — causal seven-slot architecture audit (2026-11-11)

Scope: read-only inspection of immutable A3 source `2b43253c485ef705cc7f4bcce50dad0a450cedbd`, `v98_sevenslot_preregistered_a3.py` and `v98_causal_compound_sizing.py`. No 2026+ observations, external benchmark, frozen-code mutation, or new PnL.

## Mechanistic findings

1. **Regime Router**: the code computes weekly realized volatility `sqrt(mean(log_return**2))` from 168 hourly closes and selects `0.5` only when volatility exceeds **0.035 per hour**; otherwise `1.0`. The authenticated replay's 108,192 slot rows all show `1.0`. Thus the router was **never activated** on the evaluated Clean-4 history. This is a fixed volatility attenuation threshold, not a multi-regime routing mechanism demonstrated by data. Do not describe it as an active adaptive router.
2. **Risk Governor**: `governor = 0.4` is hard-coded for every asset/hour; it is a static per-asset exposure ceiling. It is not a drawdown-, tail-, or regime-responsive risk governor. The 0.4 constant is not proof of a bug; it is proof that the implemented slot lacks the dynamic behavior implied by its name.
3. **Dynamic Allocator**: `min(1, 0.75/gross, 0.4/peak)` is a deterministic budget projection. It responds to gross requested weights and peak single-asset allocation, **not** to observed marginal sleeve performance or realized drawdown. A value of 1.0 in 95,424 of 108,192 rows means its constraints were nonbinding on ~88.2% of asset-hour rows; it does not prove a performance-sensitive allocator.
4. **Decision timing**: sleeve state is recomputed every 168 hours after the 720-hour warmup using completed close at index `i`. The execution integration must use the **next** bar open, as separately tested by the frozen workflow; this inspection does not independently rerun that integration.
5. **Sleeves**: Growth selects positive 720-hour momentum; Opportunity selects positive weekly return at a 168-hour closing high; Relative Value selects the single weekly laggard among positive 720-hour trends; Stress/Recovery selects 10–25% pullbacks below a 336-hour high with positive long trend. Fixed sleeve budgets 0.40/0.15/0.15/0.10, leaving unallocated cash. This is a genuine four-sleeve composition, but no marginal contribution on untouched future data is established.

## Decision and critical path

A3 remains **experimental and not promotable**. The verified 2023–2025 full-history replay and its annual accounting are retrospective; the chronological gate explicitly marks independent validation false. In particular, **do not rebrand any 2023–2025 subperiod as untouched holdout**. The next valid promotion path is an immutable A3 configuration evaluated exactly once on a genuinely unseen, independently sourced future period, with source provenance and access logs established *before* first evaluation; until then, no valid OOS performance exists. This future evaluation may inspect 2026+ data only **after** candidate freeze and with zero training/selection use, subject to explicit holdout governance. If that governance cannot be established, use prospective paper collection from the freeze timestamp instead. Preserve old contaminated Phase083 holdout quarantine.

For a distinct successor architecture, preregister router/governor/allocator **mechanisms** before any new economic replay; do not choose thresholds by observing A3's weak 2025 months, and do not reinterpret rejected A3 experiments as wins. Any successor must complete its own training/validation chronology and demonstrate robust portfolio-level marginal improvement and costs 1x/2x/4x, not simply pass a synthetic unit test.

**No new economic result or independent validation was produced by this audit.**
