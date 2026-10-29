# V99 R106 I1 — exact held-position intraday fold source repair: completed, independently checked

Date: **2026-10-29 10:56 BRT**. Classification **SOURCE_ONLY/HOLD — NO PROMOTION / NO ECONOMIC TRAIN**. Ex-ante preregistration committed **before code** at [ea06000](https://github.com/DnSiii/CryptoAI-Lab/commit/ea06000d41266b0ae856561fb43c67ed8286f0af).

## Verified critical-path defect and code repair

The source-driven 661-day held-contract option event spine previously requested only 23:59:59 UTC daily BBO marks. The frozen five TRAIN folds have **four non-daily edges** (2022-04-20 04:00, 2022-08-30 09:00, 2023-01-09 14:00, 2023-05-21 19:00 UTC), while the native wallet `_fold_snapshot` demands an exact same-clock MARK for every position open at an edge. An otherwise fully available original option archive could therefore still fail exact-fold accounting for a position held across a fold edge.

Production `research/tools/v99_r106_i1_source_to_mark_event_spine.py` now requests literal **same short+long original pre-edge BBO/size/venue/arrival receipts** at each frozen edge for positions satisfying `open_ms <= edge_ms < expiry_ms`, in addition to all existing 661 daily marks. Original quote freshness, manifest hashes and missing-receipt fail-closed behavior remain mandatory. The source events are chronologically inserted in their original UTC day; no stale daily interpolation, synthetic replacement or strategy-rule change. New report counters distinguish daily vs exact-edge marks.

Separately implemented `research/verification/independent_v99_r106_i1_source_spine_journal_parity.py` pins the four clocks independently (not imported from the production source compiler), requires the complete union of held daily and intraday marks, and rejects omitted fold-edge marks before NAV. The focused synthetic negative control creates an **Apr 18–May 20 2022 held BTC vertical crossing the Apr 20 04:00 UTC edge**. It independently checks source-event scheduling, the full 661-day native wallet replay with all four exact fold NAV snapshots, rejection when the original edge receipt is missing, and rejection when the journal omits the edge MARK. This is an **internal integration test**, not real market evidence.

## Executed GitHub Actions

- [Actions 40886364551](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40886364551): **SUCCESS**, 12/12 synthetic source-spine/independent adversarial tests, including the new active-fold held-position controls. Real original 182-signal source attempt still fails at `ORIGINAL_661D_MANIFEST_NOT_DELIVERED`.
- [Actions 40886364552](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40886364552): **SUCCESS**, 7/7 source-CASH tests + 15/15 original-shaped 661-day integration controls + 4/4 focused fold-edge source/native wallet controls. Archived original **182/182 causal signals**, **180/180 fixed intents**, **132 positive** were actually restored, but the real source-to-numeric runner correctly rejected the missing 661-day licensed archive before NAV. GitHub CI success **does not** mean an economic gate passed.

## Binding outcome and next actual critical path

**0/180 original I1 option lifecycles economically certified; NO ROI / NO FREEZE / NO PROMOTION / NO ORDERS / NO PAPER / NO VALIDATION / NO HOLDOUT.** The **658 of 661 missing original Deribit BTC/ETH options days** still require a dated written legal entitlement, full original bid/ask/size/venue+arrival clock coverage and vendor gap/contract proof. Start with one authorized nonsample 24h day (2022-06-15 preselected); alternative: independently licensed equivalent provider with the same source coverage. Historical underlying and **exact fold-edge index** receipts, expiry delivery fixings, native lot/multiplier, account fee tier, margin/liquidation, and conservative size-aware hypothetical execution remain separate prerequisites. Never invent historical fills for unplaced orders.

C1/D1/D2/D3/E1/H1 and other previously rejected architectures remain rejected, with no retuning. Immutable V16/V99 Frozen, legacy champion, paper/results, sealed validation [2023-10-01,2024-01-18), final holdout >=2024-01-18, and orders untouched. **The V99 engine is not delivered or validated.**
