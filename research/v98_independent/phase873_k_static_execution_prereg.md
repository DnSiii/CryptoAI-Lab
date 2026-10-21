# V98 Independent — Phase873 K static-capital shadow execution preregistration

Scope: research/v98-independent-zero, research/v98_independent/ only. Do not read/modify V16/V99 or 2025+ validation/holdout, XRP or benchmark engines.

Motivation: Phase867 first-order capacity proxies report 2,497 desired asset orders over 5% prior-hour quote volume at USD10m; this is not a filled execution ledger. Frozen K source-only targets from Phase871 must not be modified or reselected. We preregister a *distinct* inventory tracking test before computing its result.

Frozen K_full target SHA256: 2babec819c91a54cf2e3914724a63c2ae7ef5e289b4c173163c59daf9bd9a3a0. Compare K_core_only and three frozen sleeve-ablation targets without reweighting or optimization.

Algorithm: each hour t>=1, use target weights at closed t-1, prior fully closed quote volume at t-1, and fixed hypothetical NAV USD1m or USD10m. Represent asset inventory in *static notional units*, explicitly ignoring returns, mark-to-market, funding, and transaction costs. Calculate gap between new target notional and existing inventory, first execute sells up to 5% of prior-hour quote volume per asset, then buys under same per-asset capacity; any unfilled gap remains and is superseded by the next target. Do not fabricate fills when prior-hour volume is zero. Track gross, per-asset cap, tracking error, hours at capacity, 24h/168h continuous tracking deficits, and canceled/reversed desired inventory. All results are *source-only feasibility bounds*, not realized PnL or funded execution safety.

Controls: exact pinned Clean-4 OHLC SHA256 from Phase803 artifact; no use of price returns except signal generation already frozen; causal t-1; assert no exposure > frozen target gross/asset caps in static-notional model, and monotonicity under a uniformly scaled quote-volume budget. Include deterministic prefix and future-shock invariance tests. Report failures honestly; never use these diagnostics to cosmetically retune frozen K.

Interpretation: large tracking deficits at USD10m imply economic execution feasibility concerns; this test alone cannot promote or reject on PnL. Fresh same-run official OHLC + funding + conservative mark attestations remain prerequisites to any 90-cell historical economic evaluation.