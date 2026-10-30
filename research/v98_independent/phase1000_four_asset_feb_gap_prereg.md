# V98 Independent Phase1000 — preregistered four-asset February 2023 vendor gap policy

Locked **before** Phase1000 reconstruction and before any economic result. Official Phase999 100-month inventory run 39920594672 checked 100/100 vendor-checksummed Clean-4 mark archives: 96/100 pass unchanged Phase797; exactly four February-2023 archives (BTC, ETH, BNB, SOL) have precisely 648 of 672 hours, each missing 2023-02-24 00:00..23:00 UTC, with no extra/duplicate/malformed rows. No other months fail. Phase997 single-BTC exception policy is insufficient and remains rejected, unchanged.

Vendor SHA256 pins for affected monthly ZIPs:
- BTCUSDT: f15d23370f252082d8741819800b82f62ac8bbc9001b53ab6abb5d65ccb3ed3d
- ETHUSDT: 47b99057e2ea8bda8a6d266a34066b8c23954c4b1fb2a21d29f3697b2f69358d
- BNBUSDT: 8e34d717980fd6e541ecb201961d8c2a4f55b3808a669282125b2e31afa72ccc
- SOLUSDT: 2bb2d49cac17d9b397811c17e5a23a6ee79b30c7c666a997eee340828b999845

New strict source-only hypothesis: for exactly these four asset-months, re-fetch monthly ZIP/CHECKSUM and all 28 corresponding daily ZIP/CHECKSUM archives per asset, demand 672 valid daily hours, exact equality across all 12 fields for the 648 overlapping hours, exactly 24 missing hours on Feb 24, no other anomalies, and require unchanged Phase797 parse_zip to validate the deterministic derivative 672-hour ZIP. For all other 96 monthly mark archives, require unchanged Phase797 parser. Freshly verify all 100 official funding ZIPs against pinned native funding and 9144 conservative settlement bounds. No other exception, API-source inference, source substitution without receipt, or threshold adjustment. API HTTP 451 remains unavailable; vendor monthly/daily are not independent feeds.

Emit new Phase1000-only CSV and full checksum/source-manifest receipt. Do NOT modify Phase797, Phase997, frozen N, any V16/V99 artifact, or 2025+ data. Phase1000 never runs PnL. Only after its full pass may a separately preregistered Phase1001 complete-engine 90-cell training source-policy adapter be executed. All failures fail closed; no return-driven source selection.
