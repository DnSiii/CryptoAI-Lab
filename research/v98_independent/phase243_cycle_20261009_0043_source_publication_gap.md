# V98 Independent — Phase243 source/publication gap (2026-10-09 00:43 BRT)

Decision: **DATA_ONLY / NO_CHAMPION / NO_HOLDOUT**.

## Independently verified branch state
- Branch: `research/v98-independent-zero`; head at inspection: `b639bf34869b7a7d8a1f58e0b1c34ac059574818`.
- Existing Phase243 source-integrity gate and preregistration are on branch, but the full verified archive ingestion, checksum fetch, transactional publication, seven-slot architecture preflight and integrated historical evaluation are not.
- The most recent V98 workflow run observed (`37827605449`) completed successfully but is the older V98 Independent Research workflow, **not** a Phase243 historical price/funding portfolio backtest.
- Existing Phase240 evidence remains REJECT_FAMILY_NO_RESCUE; no rejected family is eligible for rescue.
- The training source contract is Binance USD-M perpetual 1h, five assets BTCUSDT/ETHUSDT/BNBUSDT/XRPUSDT/SOLUSDT, 2022-12 warmup and 2023-01 through 2025-12 training; 2026+ is excluded.

## Local reproducibility and limitations
The previously prepared, V98-only Phase243 archive/ledger/eligibility modules were assembled locally from the prior cycle's archived evidence. `python -m unittest discover -s research/v98_independent -p 'test_phase243_*.py' -q` passed **291/291** tests. These are synthetic/unit validations, **not historical market performance**. No new Binance archives were downloaded in this check; no historical Phase243 integrated PnL was calculated.

## Unresolved blockers to economic evaluation
1. Publish V98-only source acquisition, source-integrity, portfolio-ledger and eligibility code on this branch with verified source provenance.
2. Acquire and checksum all **185** monthly 1h Binance ZIPs (37 months × 5 assets) with the exact 2022-12..2025-12 training-only contract. Reject missing/duplicated, off-hour, non-monotonic, malformed, unit-inconsistent or future bars; reject inconsistent funding schedules.
3. Freeze complete seven-slot architecture **before** any integrated system-level training PnL; no slot may be filled by rejected/opened-holdout research.
4. Run deterministic chronological training folds with realistic base/severe/supersevere costs and verified funding. Audit drawdown, PF, payoff, win rate, positive days, regimes, concentration/tails, terminal liquidation and economic accounting.
5. Validation and untouched holdout stay closed until preregistered gates permit advancement.

This document records a source-readiness decision only. It is not an alpha claim, a strategy promotion, a workflow dispatch, or a claim of remote code deployment. V16/V99 files and paper state are out of scope.
