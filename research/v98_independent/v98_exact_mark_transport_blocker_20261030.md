# V98 exact historical event markPrice — source blocker, 2026-10-30

**State: BLOCKED EXTERNALLY FOR EXACT SETTLEMENT; conservative research remains runnable.** This is NOT a trading-engine pass, nor a reason to stop V98 research.

Official Binance USD-M historical endpoint `GET /fapi/v1/fundingRate` documents `symbol,fundingTime,fundingRate,markPrice` and defines `markPrice` as associated with a particular funding fee charge: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History

Existing [source probe 41135154402](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41135154402) tested original official `fapi.binance.com`, `fapi1.binance.com` and a third-party mirror for a 2023-only BTC sample: HTTP451, HTTP202 empty and timeout respectively.

New [source probe 41146481165](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41146481165) tested candidate official transports `fapi2.binance.com`, `fapi3.binance.com`, `fapi4.binance.com`, **2023-only BTC sample**. All three returned **HTTP 202 with empty body**, SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; JSON unavailable, zero attested exact event marks. The initial diagnostic job completed its *probe*, but did NOT pass source integrity. Fail-closed correction at commit `9f742fdfa2476ede7e3514821d26a455c106fb2f` makes the repeated [source check 41146568058](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41146568058) **fail as expected** rather than report misleading CI success.

**Exact evidence still required:** four authenticated files, one each for BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, with **2,286 rows per asset** covering Dec-2022 through Dec-2024, **9,144 unique 8h events** total; columns `symbol,fundingTime,fundingRate,markPrice`. Required: original transport/source attestation, hash per file, UTC ordering, no duplicate/missing event, positive finite mark, funding-rate reconciliation to SHA-pinned native Clean-4 funding source. Do not substitute hourly candle open/close for exact event mark.

**Practical alternatives:** fetch official endpoint from an authorized network/jurisdiction with accessible Binance USD-M historical API, preserve raw response bodies and hashes, then import through existing V98 strict event contract. An independently licensed historical dataset with verifiable exchange event provenance and matching rates/times may also be evaluated *before* use. If neither is available, continue only with SHA-pinned official hourly mark high/low signed worst-side conservative envelope and explicitly label PnL approximate/conservative, **not exact native funding**.

**Why it matters:** exact mark is needed to independently attest signed funding cashflow at each settlement; without it exact native-funding gate cannot pass. This does not explain or reverse NW/NX economic rejections. No 2025+ source accessed, no Frozen/V99/paper changes, no live authorization.
