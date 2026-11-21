# V13 — causal provenance checkpoint (2026-11-21 20:44 BRT)

Status: BLOCKED / RESEARCH ONLY / NO PROMOTION. This document is read-only evidence and does not certify the paper ledger.

## Reproduced source inspection

- GitHub Actions run 44937575061, job 136947472239, checked out research branch at `4075c4baf420a942ff8906ef71a411879ef52c8e`, fetched `paper-results` as `FETCH_HEAD`, extracted `reports/paper_v13_ledger.json` using `git show`, and calculated `sha256sum` on the original extracted bytes. The triage step failed closed; the diagnostic artifact was uploaded. This is evidence of read-only extraction, not evidence of historical execution provenance.
- The current `scripts/paper_once_v13.py` computes both `order_value_brl` and `order_value_brl_unrounded` from `to_brl(abs(result.asset_order_notional.loc[timestamp, symbol]))`; `to_brl` uses `PAPER_CAPITAL_BRL * value / base_equity` with `PAPER_CAPITAL_BRL=10000`. Therefore current-code output should reconcile within display rounding **for newly generated rows**, provided the same source values are used.
- The current `scripts/verify_paper_cycle_v13.py` correctly fails closed when a positive raw amount does not round to the displayed two-decimal amount; zero display is allowed only for positive raw amounts strictly below 0.005 BRL. Keep these checks intact.
- Previous diagnostic run reported 1,425 records without original raw notional and 280 mismatches. These counts do not prove which historical generator revision or capital denominator was used. In particular, a discrepancy cannot be declared a rounding exception merely because the current generator is internally consistent.

## Next decisive, non-mutating experiment

1. Pin the exact `paper-results` commit and SHA-256 from the uploaded run artifact. Map every mismatch to timestamp/symbol, and retrieve the historical generating workflow run's commit SHA and original input snapshots.
2. Compare historical `order_value_brl` against recomputation from **that** revision's `asset_order_notional`, `base_equity`, and paper capital, keeping timestamps and execution prices fixed. Classify separately: genuine subcentavo, missing source precision, capital normalization drift, or unexplainable difference. Do not backfill absent raw precision by inference.
3. Only if first-party original inputs are recoverable, implement a narrowly scoped, independently tested **processing** correction on a new candidate branch and rerun GitHub Actions. Keep the published ledger and frozen results immutable. Continue visible stale/research-only warning until a passing provenance reconciliation and verified freshness.

Do not use these historical paper discrepancies as evidence of profitable V99 economics. I1 Deribit history is still unavailable/unlicensed; D1 and C1 remain rejected. Validation and final holdout remain sealed.
