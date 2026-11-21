# V13 original published ledger: read-only CI evidence (2026-11-21 11:47 BRT)

Source: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/44910642961 (commit bdd9ecf9). Job published-ledger-discrepancy-triage failed closed as designed; adversarial-classifier passed; published-ledger-provenance failed closed. This is **not** a failed synthetic test or a certified execution reconciliation.

The original paper-results ledger SHA-256 reported in the job is `bbd0b47a97699ede1b00423ff6e14ef3c468cc07ea537599bbabe24b0a02f86e`. The latest snapshot has **1,705** adjustments: **1,425** missing unrounded fields, **276** mismatches, **3** matching and **1** subcent simulated notional. This is **four more mismatches than the previously reported 1,701-row snapshot**; do not merge counts across snapshots. By symbol: BTCUSDT 681 missing, 138 mismatches, 1 match, 1 subcent; ETHUSDT 681 missing, 138 mismatches, 2 matches; SANDUSDT 28 missing; TRXUSDT 31 missing; XMRUSDT 4 missing. Largest observed absolute differences: BTCUSDT R$130.848460375646 and ETHUSDT R$188.888439346111. These are too large to explain as cent rounding.

Concrete rows: decision 681, ETHUSDT 2026-11-04T19:00Z, shown R$7.81 vs generated raw R$7.7148818969287944 (delta R$0.0951181030712056); decision 684 BTCUSDT 2026-11-05T01:00Z shown R$10,715.24 vs raw R$10,584.391539624354 (delta R$130.848460375646). Decision 681 BTCUSDT shown R$0.00 vs generated raw R$0.0022489215690293693 is consistent with subcent rounding, but is **not proof of an actual exchange fill**. Row-level SHA-256 is present in CI log. Artifact: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/44910642961/artifacts/14709074092 .

## Next blocking steps

1. Identify the paper-results commit SHA from artifact, compare previous immutable snapshots and isolate the four added mismatches. Inspect original ledger generator revision and currency conversion assumptions for a common scale factor; do not infer fill provenance from generated notional.
2. Obtain original exchange order/fill IDs, fill quantities/prices, native fee and settled funding records, conversion timestamp/source and rounding policy; independently reconcile each record before permitting the verifier to pass. If original receipts do not exist, mark provenance unavailable and retain fail-closed status.
3. Publish only research-only/stale dashboard information while the audit remains blocked. No historical trade edits, no Frozen changes, no holdout opening, no live orders, no model promotion.

**NO PROMOTION.** A successful paper refresh job is not independent verification of economic results.
