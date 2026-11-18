# V98 C12 — preregistered complete-system hypothesis (2026-11-18)

Status: **TRAINING EXPERIMENT ONLY; NOT FROZEN, NOT VALIDATED, NOT PAPER**.

The C11 seven-slot experiment was rejected; its marginal ablations are diagnostics, **not** an optimization target. C12 is a structurally distinct long-only seven-slot composition using volatility-adjusted trend persistence, compression-release opportunity, positive relative leadership, post-broad-stress re-entry, a causal per-asset router, deterministic constrained allocator, and the existing pre-open drawdown governor. No C11 sign/threshold/parameter rescue is permitted.

**Frozen before any C12 PnL inspection:** 1440h warmup, 480h slow horizon, 96h fast horizon, 24h rebalance; four budgets 0.36/0.14/0.12/0.10; gross cap 0.72, asset cap 0.36; 7-day recovery latch; router 1/.5/.25 and unchanged pre-open governor. No tuning of these constants based on C12 outcomes.

**Inputs:** only authenticated BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT Binance USD-M 1h Clean-4, Dec-2022 warmup to Dec-2025, native funding. XRP excluded; 2026+ and contaminated Phase083 holdout forbidden. V14/V15/V99 not inspected for selection.

**Required sequence:** (1) pinned manifest/hash and 27048h source gate; (2) complete t-1 next-open causal replay with native funding and 1x/2x/4x fees/slippage; (3) independent ledger reconciliation, year-by-year chronology, concentration, tails, max DD, profit factor, payoff, win rate, positive days, and regime slices; (4) predeclared seven-slot ablations measuring marginal contribution to the whole; (5) reject or internally freeze candidate **without** adjusting based on future holdout; (6) separate untouched chronological validation only after internal training gate, and external benchmarks only after internal freeze and validation.

**Economic gate:** prioritize sustained compounded net wealth rather than minimum volatility; reject if the severe-cost path depends on a single calendar year or has materially negative later-year growth without a robust predeclared structural explanation. Any pass must demonstrate independent reproducibility and no accounting, funding, or causal defects. No paper/live claims from this training run.

Implementation: `research/v98_independent/v98_composed_c12.py`; authenticated runner and dedicated C12 workflow. Results pending.