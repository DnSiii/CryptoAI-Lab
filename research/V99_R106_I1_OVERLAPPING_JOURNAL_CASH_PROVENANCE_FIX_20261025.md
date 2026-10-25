# V99 R106 I1 — modeled portfolio cash provenance correction (2026-10-25 19:50 BRT)

**SOURCE_ONLY/HOLD — NO PROMOTION.** This is an integrity repair in a synthetic USD-equivalent options accounting component, not an economic historical backtest, a native Deribit margin model, an authenticated quote/fill or a viable trading strategy.

## Defect and impact

The earlier `Portfolio.verify()` checked that reserved collateral equaled the sum of open spread widths, but it did **not** reconstruct cash from original modeled entry premiums and settlement debits. After all positions were settled, an arbitrary positive change to `cash_usd` could satisfy the reserve and free-cash checks, potentially fabricating a final profit while the test suite stayed green. Earlier cash-ledger CI success therefore did **not** independently establish end-to-end cash provenance.

## Repair and actual CI

- `research/tools/v99_r106_i1_overlapping_cash_portfolio.py` now keeps immutable chronological modeled `LedgerEvent` inputs and replays every open from the original `PutQuote` pair via `open_vertical`, and every expiry settlement via `Spread.expiry_nav`. It compares replayed cash, reserves, open/settled position IDs and event clock against the presented portfolio state, rejecting invented balances and nonchronological/duplicate events.
- `research/verification/independent_v99_r106_i1_overlapping_cash_portfolio.py` adds negative controls for invented open/final cash, missing settlement, changed delivery price across the put payoff kink, reversed/duplicated events and forged reserve.
- Implementation commit `727da2cbb7dad6d283e50af853b4b928e208a29b`, controls `e63d61388c93c8407c4e5e50582cf01e27e489b7`. The intermediate CI [40242036907](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40242036907) correctly failed because the adversarial settlement test changed ETH delivery from 1800 to 1900, which remained **inside the same max-loss plateau**. The test was corrected to 1950 in commit `50ef3c8d696e92d8bda0a936c5e402f59a01d76b`, crossing the payoff kink.
- **Final GitHub Actions [40242060289](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40242060289): SUCCESS**, independent modeled overlapping cash oracle 56 checks across two cost scenarios, plus 128 spread accounting checks and 28 modeled inverse-coin settlement cases. **All are synthetic**; no new historical economic ROI or trade evidence.

## Still blocking the complete engine

The shared-cash USD model is **not** a coin-native exchange margin or liquidation ledger. The original historical executable Deribit BTC+ETH 2021–2023 quote tape remains missing (both entry and 21–45d exit/mark lifecycle, original venue/local timestamps, BBO quantities and coverage attestations), as do dated fee-tier, expiry-fee, margin/liquidation and lot-unit execution terms. The GitHub `TARDIS_API_KEY` secret is not configured in the last authenticated probe. [Issue #19](https://github.com/DnSiii/CryptoAI-Lab/issues/19) records the required written entitlement and an alternative authorized vendor route.

**Real certified complete cycles: 0/182. No historical economic TRAIN, validation, final holdout, ROI, orders, promotion, paper/Frozen/champion mutation.** This repair prevents false cash evidence but cannot unblock the external original-market-data dependency.
