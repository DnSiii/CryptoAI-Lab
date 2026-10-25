# V99 I1 — source-to-engine temporal synchronization repair (2026-10-25, 12:50 BRT)

**SOURCE_ONLY/HOLD — NO PROMOTION.** This repairs a source-readiness misclassification, not a profitable engine. No orders, paper changes, Frozen changes, validation, or holdout.

## Defect and fixed invariant

Previously the 91-Sunday archive intake and entry-book exporter counted any two valid strikes sharing asset/expiry as a source pair, even when their most recent exchange events or local arrivals were too far apart to be a contemporaneous two-leg quote. That raw two-strike count was not equivalent to an atomic entry opportunity.

The original raw count `two_strike_asset_weeks` is retained for provenance and comparison, but the intake now independently reports `synchronized_two_strike_asset_weeks` and five synchronized chronological folds. A pair qualifies for the **source synchronization prerequisite** only if both strikes have distinct strikes, the same asset and expiry, **both local-arrival and venue-event skews <=1,000,000 microseconds**, and all prior native-listing, source freshness, capture-order, tick, calendar and maturity checks pass. The exporter separately reconciles `synchronized_source_pairs` against the intake. Independent oracles reparse raw bytes and reject forged synchronized counts. Even a synchronized displayed book is NOT an authenticated atomic execution fill, quote-size unit, margin, fee tier, or profitable trade.

## Actual remote verification

- GitHub Actions [40208769934](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40208769934): **SUCCESS**, **15/15 tests** on synthetic 91-week fixture; original-byte independent five-fold oracle and negative controls.
- GitHub Actions [40208769862](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40208769862): **SUCCESS**, independent source-to-entry-book export and source corruption rejection.
- New adversarial fixture moves only the first BTC strike quote 2 seconds earlier, preserving positive bid/ask, source hashes, original capture order and 5-minute freshness. Raw two-strike coverage stays **182/182 artificial asset-weeks**, while synchronized coverage correctly falls to **181/182**. Independent exporter agrees and rejects a forged 182 synchronized-pair claim.
- This is a **synthetic correctness counterexample**, NOT real historical source coverage, a portfolio result, a five-fold alpha test, or an ROI. The partial original quote sample does not certify even one full entry-to-exit trade.

## Blocking critical path

Full entitled 2021-12-09 through 2023-09-30 BTC/ETH option BBO+displayed-size archive with venue and local timestamps, gap/completeness attestation and holding-period exit/settlement evidence is not available in this run. The authenticated Tardis entitlement needs an active `TARDIS_API_KEY` and vendor authorization or a legally equivalent complete vendor export. Also missing: dated native lot-unit interpretation, historical applicable account fee tier and settlement fees, margin/liquidation rules and conservative two-leg fill/slippage proof. Historical fee notices alone cannot establish account-specific tiers.

Once original bytes are acquired, run the now stricter source-to-engine gate and then the **preregistered integrated TRAIN economic ledger** with five chronological folds, severe/supersevere costs, tail and drawdown, and independent replay. Do not open validation [2023-10-01, 2024-01-18) before a brand-new candidate passes TRAIN and is frozen; final holdout >=2024-01-18 remains sealed. No recycling C1 or previously rejected candidates.
