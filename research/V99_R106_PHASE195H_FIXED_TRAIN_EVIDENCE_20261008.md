# V99 Phase195-H fixed TRAIN structural evidence — 2026-10-08

Scope: DATA_ONLY, zero economic trials, holdout untouched. GitHub Actions run 37820366172, commit 3c3b0c5203d44cbd13bcefa1c31d88c9e3e46892.

Eight synthetic/adversarial tests passed. At preregistered Ethereum block 17,000,000, publicnode and drpc agreed on fixed header fields and hash 0x96cfa0fb5e50b0a3f6cc76f3299cfbf48f17e8b41798d1394474e67ec8a97e9f. The drpc response contained 102 transactions and 102 receipts with matching indexes, block links, cumulative gas and 237 total logs. Native USDC Mint/Burn events observed in those receipts: 0/0. Deterministic transaction-index SHA256 be90afaf75fa2265667b218a95cc12fd245c92112265cc19c676d61eb73b27c3. The header's receiptsRoot is a provider claim only, NOT recomputed.

Both drpc eth_getLogs calls failed HTTP 400 during H, although the earlier Phase195-G transport run reported empty HTTP-200 arrays for the same fixed range. The provider response inconsistency remains unresolved. **HOLD_LOG_TRANSPORT_UNVERIFIED**; no receiptsRoot proof, consensus anchor, provider independence, historical t-1 latency, or complete TRAIN coverage. No backtest/holdout or candidate promotion permitted. Frozen engines, existing dashboard champions, forward-paper history, temporal folds, costs, regimes and benchmarks unchanged.

Next: test exact blockHash-scoped versus range-scoped eth_getLogs transport at this same preregistered height without changing any gate; independently reconstruct the full receiptsRoot before considering source integrity certification.
