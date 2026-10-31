# V98 Independent — causal native Open Interest window-mask source feasibility result (2026-10-31)

**SOURCE-ONLY PASS; NOT A TRADING OR PnL GATE.** Preregistered before any mask outcome in commit `a191672507a64d90ba80540e7845a9659151bc80`. Implementation committed `d7346a92abe6ebc83715ed6719b7dfc1cf82dd7a`. Full GitHub Actions run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41170405516 (PASS). No 2025/2026+, no XRP, no external benchmarks, no strategy PnL, no paper or live changes.

**Authenticated source:** pinned original native OI v2 2022-12..2024-12 vendor-checksummed archive artifact from run 40477513000. The unchanged independent source auditor verified 3,011/3,048 complete asset-days (72,264 native hourly asset observations); 37 asset-days (888 hourly asset slots) remain quarantined. Missing data are never imputed or forward-filled. Source CSV SHA256 `68ecdb3827b1540f94fb50ee053adf4af356a27260fd930853fadf0d942c7c6e`.

**Measured strict four-asset causal eligibility at completed-hour t, requiring every hour in the lookback:**

| Clock | 168h lookback | 336h lookback | 672h lookback |
| --- | --- | --- | --- |
| Optional (105 decisions) | **95 eligible / 10 blocked** | **89 / 16** | **77 / 28** |
| Core (27 decisions) | **24 eligible / 3 blocked** | **22 / 5** | **19 / 8** |

The manifest-day oracle and observed-hour mask matched for **396/396** decision/lookback combinations. No cross-asset fill, future timestamp or quarantine leak. Decision receipt SHA256 `36d359480f1a829a8dc6af53538bd64d4bb32c1fe7fd9189a0d273b05a6e1787`. GitHub Actions artifact ID `13030428361`, ZIP digest `sha256:b82ab5bd75c7b3421cf32d57774716a85b6fbfd3371e441c3df238912ba42117` (time-limited retention).

**Decision:** OI is *technically feasible with a strict mask* for a future **economically distinct** V98 seven-slot architecture: 95/105 optional decisions have fully authenticated four-asset 168h OI coverage. Missing-window decisions must disable OI-dependent sleeves, not silently trade imputed observations; all allocation, attribution and economic gates must be preregistered before PnL. This does not imply that OI improves wealth, that 2025 is an independent validation period, or that funding exact event marks have been obtained. Original OC economic rejection remains permanent; it is not eligible for OI-based rescue.

**Unresolved separate dependency:** exact native funding settlement requires authenticated `symbol,fundingTime,fundingRate,markPrice` per event for four assets, 2,286 each, 9,144 total, with source/transport attestation. The official Binance historical funding API documents this field, but egress from GitHub has not yielded historical tick marks. Official signed 1h worst-side mark envelope remains primary, 1m envelope sensitivity only. 2026+ holdout, V16/V99 Frozen, V99 paper and live untouched.
