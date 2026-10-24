# V99 R106 I1 — source-to-engine entry-book bridge (2026-10-24, 18:48 BRT)

**DATA_ONLY/HOLD — NO PROMOTION.** This is usable source plumbing, not a complete options engine, not economic TRAIN, not certified fills or ROI.

## Implemented and actually run

- New `research/tools/v99_r106_i1_entry_book_export.py` consumes the existing 91-week original-archive intake and exports **all** final causally eligible last-known option bid/ask books (not selected trades), preserving exchange/local timestamps, native instrument IDs, strike, expiry, prices in coin, source-size units, weekly decision/fold, source file and SHA-256. Malformed or stale newer updates invalidate prior books. It reconciles two-strike asset-week counts with the original gate and refuses future partitions.
- New `research/verification/independent_v99_r106_i1_entry_book_export.py` replays every original CSV row independently and verifies exact exported books, timestamps, prices, source hashes and fold counts; mutation of original bytes after export is rejected.
- [GitHub Actions 40135792542](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40135792542) **SUCCESS**, with **364 independently reconstructed synthetic quote records** across **182/182 synthetic** asset-weeks. The deliberate original-file corruption check was rejected. These counts are fixture-only and **not real market coverage**.
- Three source/verification/workflow files added in commits `adb61a5`, `6621094`, `f070316`; independently compared against prior branch head `e8f90cf`. No Frozen, paper/results, champion, dashboard, order or holdout file modified.

## Actual status and decisive external dependency

**Real 2021–2023 executable quote coverage remains 0/182 eligible BTC/ETH asset-weeks** from the available 4,000-row partial Tardis sample. The bridge makes eligible quote books consumable by a future integrated engine but does not create them. Before a historical economic replay, acquire legally authorized full Deribit BTC+ETH quote tapes covering original 91 weekly entries **and holding-period exit/mark liquidity**, with venue/local timestamps, bid/ask and sizes, gap/completeness attestations and contract multiplier/lot specifications. Also obtain historically applicable account fee tiers, expiry delivery fees, coin collateral/margin/liquidation terms, and authenticated first-party settlement indices (the latter already separately recovered for 661 TRAIN dates). Historical hypothetical fills must be **modeled**, never labeled real account fills.

Next justified action is **source entitlement and a verified full lifecycle sample before any purchase**, then bind actual archived books to a *pre-registered* self-financing native-coin complete engine and independent five-fold severe/supersevere portfolio accounting. No validation [2023-10-01,2024-01-18) or final holdout >=2024-01-18 may be opened until legitimate TRAIN pass and formal freeze. No serial retuning of rejected strategies, no promotion and no orders.
