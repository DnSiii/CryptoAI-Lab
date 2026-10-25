# V99 I1 — historical option tick-size provenance (preregistered 2026-10-25 01:xx BRT)

**SOURCE-ONLY / DATA_ONLY/HOLD / NO PROMOTION.** This closes a potential original-data-to-execution error, not an alpha search or economic backtest.

## Fixed hypothesis and historical evidence
Deribit's dated **6 July 2023** change notice says BTC/ETH on-screen option tick sizes were reduced; the API `tick_size` became the *new minimum*, and `tick_size_steps` describes the >0.005 coin threshold (0.0005 coin) versus <=0.005 (0.0001 coin). Official dated source: https://support.deribit.com/hc/en-us/articles/25944779257373-6-July-2023-TS . A **2026 archived-instrument API response for contracts expired in 2021–2023 is not a time-stamped 2021–2023 fee/lot/tick schedule**. Therefore treating today's `tick_size` on an expired contract as an as-of executable price grid is unsafe, even though the original response bytes and SHA-256 are authentic.

## Preregistered read-only test
Reuse **exactly** the original first-party Deribit BTC/ETH expired-instrument artifact from GitHub Actions **40148052668**, without recollection or future market prices. Independently verify original gzip bytes and report; partition *TRAIN-expiry puts only* by expiration strictly before **2023-07-06T00:00:00Z** versus at/after; for each asset and period report count, histogram of archived `tick_size`, presence of original `tick_size_steps`, and observed 0.0001/0.0005 fields. This is descriptive source metadata, **not proof of historical tick compliance**, and cannot determine historical account fees or native lot conversion. The exact effective hour on 6 July is not known from this notice; **exclude 6 July** from any certification claim.

An independent verifier must reparse raw gzipped venue bytes without using the primary aggregation, reconcile exact counts and SHA and reject a modified output. Preserve the original 5 TRAIN folds, sealed validation from 2023-10-01 and final holdout from 2024-01-18. Never touch Frozen V16/V99, paper, champion, dashboard performance or orders.

## Decision rule
If old expired contracts report present-day-style tick values or the as-of rule cannot be certified, **mark historical tick/fee/lot semantics UNVERIFIED and refuse any native fill certification**. Do not assert a historical change magnitude from the retrospective archive alone. Full 2021–2023 executable bid/ask+size lifecycle tape, dated historical terms and margin/fee schedule are still necessary before full severe/supersevere TRAIN and independent gates. No PnL, ROI or promotion from this metadata test.
