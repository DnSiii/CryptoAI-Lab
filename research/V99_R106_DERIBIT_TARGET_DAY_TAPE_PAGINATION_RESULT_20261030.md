# V99 R106 — original Deribit 2022-01-23 target-day trade-tape pagination result (2026-10-30 02:53 BRT)

**FIRST-PARTY TARGET-DAY TRADE TAPE PAGINATED; NOT EXECUTABLE OPTIONS QUOTES; I1 SOURCE HOLD; NO PROMOTION.** This is a real original-data CI run and independently checked source result, **not** a strategy backtest, a quote archive or evidence of a profitable I1 engine.

## Reproducible sequence and original data

1. Fixed scope committed **before** the first network call: [preregistration](V99_R106_DERIBIT_TARGET_DAY_TAPE_PAGINATION_PREREG_20261030.md) at `db7d7201c06969303f4007a0c9f3a3d7b8472e14`; GitHub CI verified this commit is an ancestor.
2. Primary [bounded first-party page collector](tools/v99_r106_deribit_target_day_tape.py), separate [original-byte independent oracle](verification/independent_v99_r106_deribit_target_day_tape_oracle.py) and [source-only workflow](../.github/workflows/v99-r106-deribit-target-day-tape.yml) committed on the designated research branch.
3. [GitHub Actions 41010715504](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41010715504) **SUCCESS**. Original Deribit history host `history.deribit.com`, exact 2022-01-23 UTC TRAIN target, `kind=option`, `include_old=true`, ascending 1,000-trade pages with inclusive timestamp overlap and original trade-ID deduplication. No API key, no sealed data, no orders.
4. Independent oracle **PASS**, re-parsing every original page byte stream, page SHA256, original trade IDs, cursor continuity, timestamps, option contracts, positive trades, aggregates and strict no-promotion flags. Raw trade bytes deleted before artifact upload; only aggregate metadata and per-page hashes retained.

| Original first-party target-day evidence | BTC options | ETH options |
| --- | ---: | ---: |
| API pages to `has_more=false` | **6** | **7** |
| Unique original trades after overlap deduplication | **5,849** | **6,416** |
| Distinct 28–35d expiry PUT instruments with >=1 trade print | **10** | **20** |
| Independent original-page replay | **PASS** | **PASS** |

**Total: 12,265 distinct original option trade prints, 30 distinct 28–35d put instruments across BTC/ETH.** This proves only that those dated put instruments traded on the fixed historical day. `has_more=false` establishes completion of the returned API pagination, **not** exchange-certified full-market completeness, continuously available quotes, contemporaneous two-strike spreads, hourly 24/24 market depth or any trade execution. No original trade row is published in the artifact.

## Decision and exact delivery blocker

**PUBLIC_TRADE_DAY_PAGINATION_COMPLETE_NOT_QUOTES — SOURCE HOLD / NO PROMOTION.** The free first-party trade tape is now a verified independent activity/contract chronology cross-check that can help reject a paid quote sample with implausible instruments. It **cannot** satisfy the I1 source gate or certify even one economic lifecycle. The fixed I1 one-day source feasibility still requires original authorized 2022-01-23 24-hour BTC+ETH *two-sided options quotes with sizes and timestamps*, including contemporaneous 28–35d same-expiry two-strike put books, original SHA256, and written license/retention entitlement. For the complete 661-day original TRAIN quote/depth/marks/settlement archive, **658 quote days remain missing** and **0/180 option lifecycles are economically certified**. Historical native fee tier, contract/margin/delivery rules, actual execution/fill provenance and independent five-fold severe/supersevere accounting also remain unverified.

**Next actual critical step:** procure or lawfully obtain an equivalent **single original quote/depth day** with written rights and independent hash, then run the already built source-feasibility gate against those original bytes; if valid, obtain complete TRAIN coverage and verify original fees/settlement before any economic claim. The alternative is a genuinely distinct system with a complete first-party dataset and ex-ante economics, not resurrecting rejected C1/S1/S2/S3 or tuning the final holdout.

**No strategy ROI or paper PnL was computed.** Frozen V16/V99, legacy champion, paper/results, validation [2023-10-01,2024-01-18), final holdout >=2024-01-18 and order interfaces remain untouched. CI success means source/oracle checks passed, **not** that the V99 is validated.
