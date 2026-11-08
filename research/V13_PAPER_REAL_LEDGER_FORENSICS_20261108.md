# V13 paper movement: verified raw-ledger forensic finding (2026-11-08)

Evidence: GitHub Actions run 42511853033, job 128826423822, commit 6ac18ce4ef3bb04cdc8340b60ca2d1f7a84d1cc1, conclusion SUCCESS. The job fetched `reports/paper_v13_ledger.json` from the canonical `paper-results` branch without changing it and ran ten adversarial fixture tests plus the real ledger inspection.

Real-ledger finding: **1 legitimate subcent display, 0 inconsistent movements** according to `scripts/diagnose_v13_paper_movements_readonly.py`. Decision index 681, adjustment index 0, BTCUSDT `reduce_short`, side `buy`; prior weight -0.04735247, new weight -0.04735225; displayed order value R$0.00, unrounded order value R$0.0022489215690293693. The positive nonzero execution amount is strictly below R$0.005 and therefore rounds to R$0.00. The recorded R$2.14 gross result is scoped to the **whole asset-hour**, not profit on this subcent adjustment. This is not evidence of an invalid zero-execution trade.

Interpretation and limits:
- The observed record is consistent with the existing narrow subcent exception. Do **not** remove the verifier or widen its bounds; do **not** reconstruct trades or edit `paper-results`.
- This read-only forensic result is not a full replay of the original failing paper cycle, nor an exchange execution receipt. Paper continuity and dashboard market freshness require independent checks.
- GitHub Actions success is a technical gate, not an economically validated V99 engine. No promotion, live orders, or modification of Frozen/validation/holdout.
- Next critical path: confirm the most recent paper cycle's ledger verification and market timestamp, and ensure a prominent stale/research-only public banner if freshness is not demonstrated. Independently continue E2 TRAIN-only with complete native funding, fee, fill and OHLCV provenance before any economic conclusions.

Evidence links:
- https://github.com/DnSiii/CryptoAI-Lab/actions/runs/42511853033
- https://github.com/DnSiii/CryptoAI-Lab/actions/runs/42511853033/job/128826423822
