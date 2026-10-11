# V98 Independent — BNB funding zero-rate cross-asset control (2026-10-11 10:49 BRT)

DATA ONLY; branch research/v98-independent-zero; training 2023–2025 exclusive of 2026; no alpha, holdout, V16 or V99.

Independent read of the five existing Phase206 funding CSVs on the V98 branch, aligned on exact recorded settlement timestamps:

- Each asset has 3,288 2023–2025 training settlements.
- BNB: 1,800 exactly zero (54.7445%), 725 positive, 763 negative. Annual zero counts: 2023=507, 2024=582, 2025=711.
- BTC/ETH/SOL/XRP: zero exactly-zero rates in the same 3,288 training events each.
- All 1,800 BNB zero timestamps have observations in each of the four comparators; none of those four comparator rates is zero at those same timestamps.
- Longest BNB zero run: 77 consecutive settlements, 2024-07-03 16:00 UTC through 2024-07-29 00:00:00.001 UTC. Other runs: 66 (2023-08-24 to 2023-09-15), 55 (2024-06-13 to 2024-07-01), 52 (2025-06-25 to 2025-07-12), 51 (2025-05-14 to 2025-05-31).

Frozen Git blobs: BNB 6b46a2a911d85079f3ce4ec5bc8b1791febd397a; BTC 50732b1fb26c748ffeea9fa97e71626eaef89544; ETH bde2ff02f21d7369cbfeecc339224594cc0b7591; SOL 3c1ef787ef7ae4ec731284962ee853b7fd882ebd; XRP c61589ead8f0f7a86c51a6202a476b765b537eb4.

Interpretation: asset-specific zeros rather than a five-asset-wide zero-filling artifact; this does **not** prove authenticity or a Binance-specific market mechanism. Preserve all original values and no imputation. Source-level adjudication requires independently checksum-verified original BNB monthly funding archives. Existing V98 promotion gate remains blocked by XRP 1h 2023-11-14 physical source contradiction; Phase240 rejected; champion none. No new backtest.
