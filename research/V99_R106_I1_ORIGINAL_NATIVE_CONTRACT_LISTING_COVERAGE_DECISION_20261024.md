# V99 I1 — original Deribit native contract registry and fixed listing coverage (2026-10-24 21:50 BRT)

**DATA_ONLY/HOLD — NO PROMOTION. This closes a first-party historical instrument-metadata collection step, not the executable option-quote or economic TRAIN gate.**

## Executed original-source collection
- Ex-ante metadata protocol at commit `1b74b48`; [Actions 40148052668](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40148052668) **SUCCESS** (artifact `v99-i1-firstparty-native-instruments-40148052668`, ID 12580249936).
- Downloaded full first-party archived Deribit expired option instrument responses, retaining compressed original bytes and SHA256. BTC **124,307** original instruments; ETH **126,424**. Filtered to original TRAIN expiry put contracts: **12,984 BTC + 12,954 ETH = 25,938 put contracts**. The nine preserved fields (name, creation/expiration, strike, put type, settlement currency, contract size, min amount and tick size) have **0 missing values** in the selected rows.
- Independent original-byte oracle reconstructed all 25,938 selected records and verified SHA, symbol/expiry/strike and field counts. Mutated-registry negative control was rejected. Archived metadata is a current historical registry, **not** proof that each contract was actually tradeable at a historical decision or that fees/margin terms are unchanged.

## Precommitted original TRAIN listing screen
- Frozen listing coverage protocol at commit `5663eef`, **before** reading listing results; [Actions 40148186739](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40148186739) **SUCCESS**. Independent oracle reread the original Deribit responses, reconstructed 91 Monday decisions × BTC/ETH, the original five folds, and rejected tampered result bytes.
- Necessary condition: native BTC/ETH-settled put contracts **created no later than the decision**, with at least two different strikes in the same 21–45 day expiry strictly within TRAIN. Result: **126/182 asset-weeks** had eligible *listed instrument pairs* (63/91 weeks for BTC and 63/91 for ETH). Fold listing coverage per asset: **[13/19, 13/19, 13/19, 12/18, 12/16]**.
- **56/182 asset-weeks do not have two eligible contracts in the recovered registry**, but this cannot be conflated with zero real trading or with zero returns. The historical registry may be incomplete; neither existence nor absence is independently certified as an as-of tradable order book. This is a source-universe feasibility constraint, not a strategy backtest.
- **Executable original two-sided quote coverage remains 0/182** from the previously verified partial Tardis sample; original listed contracts are not executable quotes. No option premium, PnL, five-fold economic return, native historical fee, historical liquidation, portfolio NAV or after-cost growth was computed.

## Remaining precise blockers and decision
1. **Licensed historical BTC+ETH Deribit option bid/ask+displayed sizes**, exchange and local arrival timestamps, complete gap manifest, and entry plus holding-period quote depth for [2021-12-09,2023-10-01), with vendor entitlement and archive integrity. Tardis non-sample requests previously HTTP 403; Amberdata is only an unverified alternative until contract/field/period coverage is proven.
2. **Historical native settlement/fee/margin/liquidation** terms, account-specific tier and instrument metadata valid at the trade time. The new first-party registry helps with contract identity, not retroactive fee or collateral certification. Conservative hypothetical fills are modeled, never historical account fills.
3. One precommitted **complete self-financing native-coin strategy** with independently verified five-fold severe/supersevere economics, 3x2 regimes, tails, DD and benchmark envelope. Only TRAIN pass + freeze may open sealed validation; final holdout stays closed.

**No promotion, no orders, no paper-results, Frozen V16/V99, champion or dashboard modification, no validation [2023-10-01,2024-01-18) or holdout >=2024-01-18 access.** No ROI claimed. Stop treating listing counts as an executable engine; resolve full quote and historical fee/margin provenance before further economic I1 claims.
