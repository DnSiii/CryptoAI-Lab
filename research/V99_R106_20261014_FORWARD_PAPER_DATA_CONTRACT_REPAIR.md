# V99 R106 — paper/reference data-contract repair (2026-10-14)

**Decision: DATA_ONLY/HOLD; no promotion, no economic optimization, no publication of reconstructed PnL.** Five R106 paper variants, not V99 Frozen. V16 Frozen, V99 Frozen and final holdout stay unchanged. No historical paper row has been rewritten.

## The verified published baseline

Read-only GitHub evidence: `paper-results:reports/paper_v99_research_ledger.json` blob `97ce6ea8e9b58a9616892d915c86d96ae3c54225`, original paper boundary **2026-09-16 13:00 UTC**, latest approved paper row **2026-10-10 05:00 UTC**. All five curves have **569 points / 568 returns**, each starting with simulated BRL 10,000.

| Track | Published cumulative simulated ROI | Observed peak DD | Operations in ledger | Paper status |
| --- | ---: | ---: | ---: | --- |
| R98 | +3.8777% | −14.7626% | 276 | reference |
| R106 F1 | +12.3391% | −14.7844% | **1,500, capped** | research_rejected |
| R106 F3 | +16.4106% | −13.7608% | **1,500, capped** | research_rejected |
| R106 F7/F9 | +3.8777% | −14.7626% | 276 | research_leader historically |
| R106 F12 | +3.8777% | −14.7626% | 276 | research_rejected |

**Independence audit:** published paper equity rows **AND** operation rows are exactly identical for **R98 = F7/F9 = F12** across all 569 points. Thus the published five tracks contain only **three distinct forward traces**. This is not proof of three separate successful sources of alpha. F1 and F3 differ, but have truncated operation logs and invalidated provenance, so neither can be crowned a forward winner.

**Historical-reference contamination:** Each published `backtest_reference[*].curve` has **2,476 points**, of which **998 are on/after 2024-01-18 00:00 UTC**, the fixed R106 TRAIN end; **25** of those are also on/after the paper boundary. They therefore must not be represented as a certified TRAIN backtest curve. This is a timestamp-only source-boundary audit, not an inspection or optimization of the protected holdout.

**Forward tail diagnostic, purely descriptive:** worst UTC day 2026-10-05 was F1 −BRL 896.33, F3 −BRL 670.96, F7 −BRL 594.82. F1/F3 return correlation with F7 hourly paper returns was approximately 0.9096/0.9411 respectively, while R98/F7/F12 correlation was exactly 1.0. This does **not** establish a causal or reproducible forward advantage.

## Implemented on the isolated V99 research branch

1. `scripts/paper_once_v99_research_variants_v2.py`: historical `daily_backtest_curve` now stops strictly before the frozen `p1.TRAIN_END` (2024-01-18 UTC) and strictly before the paper boundary. Rejects timezone-naive sources and an invalid TRAIN-after-paper ordering. It must never include final holdout or forward rows as historical references.
2. `paper_operations`: removed the silent `operations[-1500:]` tail truncation. Full operation events now remain available to the *research candidate* in chronological order. Existing publication firewall **still blocks** 1,500+ legacy evidence gaps or rewritten rows; this code is **not** an authorization to replace the existing historical ledger.
3. New `research/tests/test_v99_r106_forward_generator_isolation.py`: tests full operations beyond 1,500, exact paper boundary exclusion, strict TRAIN limit, timezone rejection, chronological entries and zero unauthorized writes. New read-only CI `.github/workflows/v99-r106-forward-isolation.yml`.

**Official GitHub Actions run 38616105262 succeeded:** **17 new boundary/operations tests + 20 existing publication-firewall tests + 27 existing epoch-quarantine tests = 64 green** (Python 3.12). The earlier CI run 38616025608 failed because the test suite had not yet been updated for the stronger strict-TRAIN function signature; the corrected run passed. GitHub CI also previously passed the BJ and BM safety workflows after the generator change.

**Important residual restriction:** the main historical full-data `build_variants` generator still recalculates results over its full available market input, and the rejected F1/F3 streams would still disagree with published forward hours. The boundary-safe *reference export* is **not** proof that upstream signal construction was PIT-attested or never touched post-TRAIN data internally. No protected four-arm economic replay was performed and no new backtest/holdout metric is claimed.

## Public dashboard — evidence labeling, not economic promotion

The public V99 Research dashboard code now checks:
- whether the last snapshot is stale (more than 48 hours);
- whether any R106 operation history hits the legacy cap of 1,500;
- whether historical reference curves cross the fixed TRAIN end;
- whether paper curves and operation streams are exact duplicates.

It displays **“PAPER EXPERIMENTAL EM QUARENTENA”** and **“SIMULAÇÃO · NÃO VALIDADA”**, labels maxima as published snapshot figures rather than valid leaderboards, and preserves all underlying historical numbers and five motors. The dashboard work is code/UI only; not an economic data update. Changes are synchronized to `main`, `paper-results` and `gh-pages`.

## Explicit next gates

1. Preserve the immutable old published epoch and its blob SHA, including all imperfect metrics and missing operation events. No retroactive repair, merge, curve splicing, holdout peeking, or gate removal.
2. Produce an **independently acquired, immutable as-of source receipt stream**, with UTC request/response timing, raw payload hash, discovery timestamp, t−1 first eligible close, and source-authentication proof. Until then every new epoch remains **quarantined**, even if its rolling curve looks profitable.
3. Independently produce full gross/fees/funding/transfer/net hourly accounting and an **uncapped operation journal** on a new source-verified epoch, starting strictly after its authenticated boundary, no inherited ROI or old-period backfill.
4. Run preregistered TRAIN-only replay, severe/supersevere costs, temporal folds, regimes, benchmark envelope, tails/DD/concentration, reproducibility. Promote only if the frozen candidate objectively passes all relevant gates.

**Research leader is still R106 F7/F9 Core. F1/F3's larger numbers from the stale/capped paper do not supersede the recorded scientific rejections.**
