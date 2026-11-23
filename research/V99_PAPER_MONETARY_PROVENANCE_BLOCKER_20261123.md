# V99 paper monetary provenance blocker — 2026-11-23 (read-only evidence)

Status: **BLOCKED / NO PROMOTION**. This note does not modify any published ledger, frozen model, paper result, or holdout.

## Reproducible evidence
- GitHub Actions forensic job: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/45062794010 (job 137332226630), 2026-11-22. Adversarial classification tests passed; published-ledger classification failed closed with exit code 2: **300 inconsistent positive raw/display records, 1 legitimate subcent** in this run. These counts must not be conflated with the separate later audit of 302 discrepancies.
- Exact source row, decision 831 / adjustment 0, BTCUSDT: `order_value_brl=11.38`, `order_value_brl_unrounded=9.36145660110325`, previous weight `-0.13843008`, new weight `-0.13936623`, execution price `60826.5`. Rounded raw = 9.36, not 11.38. This is **not** subcent rounding.
- Decision 830 / adjustment 0, BTCUSDT: displayed `112.84`, raw `93.050951639602`; decision 830 / adjustment 1, ETHUSDT: displayed `261.57`, raw `215.69961038127255`. Both require source-level reconciliation; no replacement values are authorized.
- The published paper workflow https://github.com/DnSiii/CryptoAI-Lab/actions/runs/45096295832 passed its 24 principal steps, including historical preservation. Passing publication does **not** certify the separately failing monetary provenance audit.

## Required resolution before certification
1. Recover immutable original input snapshots and generation commit for each affected decision. Record timestamps, ledger SHA, original capital/equity basis, target/previous weights, fee basis, rounding implementation, and exact original calculation formula. Compare display and raw calculations independently at the same timestamp; determine whether different capital bases, position scaling, or another cause explains the mismatch. **Do not assume a cause from ratios alone.**
2. Generate a separate append-only reconciliation manifest keyed by ledger hash + decision index + adjustment index, with observed original fields, independently recomputed amount, formula provenance, and verdict. No edits to historical trade rows or backfilled trades.
3. Preserve the strict V13 verifier: finite positive raw; displayed value equals rounded raw when present; zero display only for strictly positive raw < 0.005; missing raw must remain explicitly unverified. Test adversarial mismatches, NaN/Inf, negative, absent raw, duplicated rows, and subcent boundaries.
4. Run independent forensic and paper CI on the original artifacts and attach machine-readable evidence. Do not promote the paper's monetary certification or any V99 economic claim until every discrepancy is explained and checks pass.

Separate engine gate: D1 remains rejected; I1 requires licensed, complete original Deribit options history (658/661 days missing), explicit procurement authorization, and independent economic validation. No orders, no holdout opening, no performance claim.
