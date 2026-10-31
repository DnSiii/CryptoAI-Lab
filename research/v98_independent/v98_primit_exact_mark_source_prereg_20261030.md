# V98 Independent — preregistered transparent historical funding mirror probe (2026-10-30)

**Purpose:** close the exact settlement-mark provenance dependency, not create a strategy or infer PnL. This probe is SOURCE-ONLY, training period 2023-01, BTCUSDT, never 2025/2026+. The independent third-party Primit API documents a transparent reverse proxy to Binance USD-M `/fapi/v1/fundingRate`, including `symbol,fundingTime,fundingRate,markPrice`. Documentation: https://docs.pipai.org/market-data/rest/funding-rate/ .

**Preregistered access:** `https://api-dev.pipai.org/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=1672531200000&endTime=1675209599999&limit=1000` (January 2023 only). The alternative documented Primit history path is a **fallback source-discovery probe only**, not an automatic substitute for the exact Binance shape.

**Fail closed:** only HTTP 200, nonempty JSON list, required four fields, strictly increasing unique fundingTime, timestamps inside requested training month, finite positive markPrice and finite fundingRate, with at least one event. SHA256 raw body, transport host, response code, timestamps, row count, and schema are recorded; no claim of official provenance from a URL alone. A reverse proxy is not equivalent to an authenticated first-party capture; the transport identity and exchange-rate reconciliation remain separate release gates. Empty body, HTTP 202/451/502, HTML or timeout => NO SOURCE. No backfilling or interpolation.

**If successful:** separately pre-register four-symbol 2022-12..2024-12 full acquisition, per-symbol native-rate reconciliation against pinned Clean-4, full 2,286 events per asset, SHA256 receipts, exact mark vs official hourly mark envelope, and independent transport provenance. No training PnL changes until these gates pass.

**If unsuccessful:** do not loop indefinitely or call the probe a source success; continue conservative signed two-sided hourly mark-envelope research and disclose exact settlement as unverified. Never alter V16/V99/Frozen/paper, XRP quarantine or future holdout.
