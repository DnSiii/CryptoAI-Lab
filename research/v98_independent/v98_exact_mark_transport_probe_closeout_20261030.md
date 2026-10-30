# V98 native funding markPrice historical transport probe — verified 2026-10-30

**Source-only; no PnL, no 2025, no 2026+ training or holdout.** [GitHub Actions run 41135154402](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41135154402), source-only receipt artifact `13016655448`, SHA256 ZIP `9c74ee26497b866b2dc31f4a5df2a33cb53df91c72f664b8e73bc5ac99888818`. Probe requested only BTCUSDT 2023-01-01 to 2023-01-02 historical funding, never current/future data.

**Measured transports:**
- Official `https://fapi.binance.com/fapi/v1/fundingRate`: **HTTP 451**.
- Alternate `https://fapi1.binance.com/fapi/v1/fundingRate`: **HTTP 202 with empty response body** (SHA256 of empty body `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`), not valid JSON or historical marks.
- Unverified third-party passthrough `https://api-dev.pipai.org/fapi/v1/fundingRate`: **read timeout**. No markPrice data obtained.

**Precisely missing for exact native settlement:** four per-asset authenticated official or equivalent `symbol,fundingTime,fundingRate,markPrice` files, 2,286 rows each (9,144 total), SHA256 and immutable source/transport attestation, 2022-12 through 2024-12 only. The strict V98-only importer already rejects wrong rates, timestamps, missing/duplicate events, out-of-envelope marks and unauthenticated manifests. Official Binance USD-M API documentation confirms that funding history response includes markPrice; it does **not** establish availability through these blocked transports. A source export from an authorized network with independently verifiable raw responses is the direct alternative. Third-party mirrors alone cannot be relabeled as official.

**Economic interpretation:** conservative signed native rates + official worst-side 1h mark envelope remain a proxy. They cannot establish exact-tick funding PnL or convert rejected NT/NU engines into approved engines. No V16 Frozen, V99 research/workflows/Frozen/paper, V98 paper or future holdout changed.
