# V98 C24 independent local training diagnostic — 2026-11-19

**Status: PROVISIONAL FAIL; NOT an authenticated GitHub Actions ledger audit, not validation, not promotion.** This report is an independent reimplementation of the preregistered C24 decision equations and next-open accounting against the pinned Clean-4 source ZIPs. It does not replace the official C24 replay, per-hour ledger, or independent ledger reconciliation.

Source artifacts: price 13444665313, native funding 13464271018. Verified SHA-256 of all four canonical price CSVs and all four funding CSVs against their respective manifests; 27,048 continuous hourly bars per asset, 3,381 native funding events per asset, Dec-2022 through Dec-2025. No 2026+ data or holdout accessed.

| Scenario | Final equity from $10,000 | Maximum drawdown | 2023 | 2024 | 2025 | Post-fill cap violations |
|---|---:|---:|---:|---:|---:|---:|
| 1x | $16,105.44 | 26.341% | +59.1791% | +3.5887% | -2.3271% | 0 |
| 2x | $12,267.24 | 28.254% | +35.3579% | -6.0997% | -3.4847% | 0 |
| 4x | $7,629.64 | 36.937% | +1.0425% | -15.7222% | -10.4044% | 0 |

At 4x, total equity declines ~23.70%; 2024 and 2025 both violate the preregistered annual-positive gate. This is an **independent local negative diagnostic**, not a substitute for the workflow's canonical C24 artifact and audit. Do not change C24 parameters or promote C24 based on this report. Keep C24 frozen, recover its authenticated workflow result and reconcile any numerical differences before final disposition.

The local replay computes all four sleeves and the regime router from historical closes available before the next open, charges the preregistered 0.0006 x cost scale per traded weight and native funding on pre-fill exposure, applies the drawdown governor and hourly gross/asset cap projection. Source files were read only. External engines, XRP and holdout were not accessed.
