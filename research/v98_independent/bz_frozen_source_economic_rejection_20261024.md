# V98 Independent BZ — frozen pre-result source economic rejection (2026-10-24)

**Decision: REJECT_BZ_SOURCE_NO_RESCUE.** The immutable original BZ preregistration was committed at `a9490519ac7d646334be84dd7ea1e9c58296fb3b` **before** the BZ source implementation or any BZ economic result. Official original two-OS source and independent signal/cashflow audit: [run 40104238699](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40104238699), source commit `0e58fe45a6478d393e90431e3103513118e85662`. Both Ubuntu 22.04 and 24.04 source JSON receipts are byte-identical (SHA256 `4567b25ad327506b2198442daa1b6a7fa6471e82e01b743a78207827ea097297`). Independent audit accepted all reconstructed signals, native funding events, price PnL, conservative intrahold lows, fees/slippage, causal prior-only capacity, annual aggregates, and decision. A separate locally written verifier operating directly on the SHA-pinned 2022–24 source ZIP reproduced the same annual results; it was not used to tune BZ.

## Original fixed source-only episode results (NOT portfolio PnL/CAGR)

| Entry year | Episodes | Sum of price PnL per USD episode | Native funding per USD episode | Severe roundtrip friction per USD episode | Severe net per USD episode | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2023 | 5 | +0.0922566310 | +0.0043484129 | 0.0504612832 | **+0.0461437607** | Source year pass |
| 2024 | 4 | −0.1692537275 | −0.0083790690 | 0.0391537314 | **−0.2167865279** | **Source year FAIL** |

The preregistered advancement rule requires >=4 episodes **and positive severe net episode sum in both years**. Therefore BZ fails and must not be transformed into a full seven-slot engine. Two 2024 BNB episodes produced severe per-entry-unit returns of approximately **−0.1474 and −0.1294**, respectively, but excluding BNB or changing thresholds now would be an invalid post-result rescue. Neither 2023's positive result nor the successful independent arithmetic audit changes the rejection.

## Physical-capacity and validation boundary

The median original prior-only maximum authorized notional per selected episode was approximately **USD291,472 (2023)** and **USD193,955 (2024)**, not evidence of actual fills or deployable portfolio PnL. 2025 remains sealed; 2026+, XRP, Phase083 and V14/V15/V99 internals were not read. All code/workflows were V98 Independent namespaced. V16 Frozen, V99 Frozen/research/workflows and paper remain untouched. No live trading authorized.

## Critical-path next step

BZ is **permanently rejected**, with no threshold/window/sign/asset rescue. Future work must target a distinct **composed seven-slot architecture** whose three satellite sleeves provide genuinely positive marginal portfolio growth after native funding and severe costs; prioritize realistic deployable capacity and independent chronology rather than reporting source-only edge as a completed engine. Physical scaling beyond current conservative limits still requires authenticated order-book depth and adverse/stressed execution impact evidence. No V98 fully approved.
