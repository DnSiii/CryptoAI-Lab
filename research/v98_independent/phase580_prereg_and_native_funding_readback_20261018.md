# V98 Independent — Phase580 source-only branch readback (2026-10-18)

## Immutable Phase460 prereg successfully published
- Branch: `research/v98-independent-zero` only.
- Path: `research/v98_independent/phase460_bipower_jump_diffusion_prereg.md`.
- Git commit: `725937a2990c34b9c5e25cd3d024b721153a8afd`.
- Git blob: `6d0e57235f03c3ee032feba7a3a3e790720626af`.
- Local immutable SHA256: `c8a57f38d1d91fc0806f506f19f556c86718771b9c3c0f05e284051e45a82aac`.
- GitHub connector independently read back the exact 5,593 UTF-8 bytes and blob SHA; local Git blob calculation agrees. The commit added only this V98-namespaced file.
- Publication removes the **remote-prereg absence** blocker only; it is NOT source attestation, market-data authorization, performance validation or strategy promotion.

## Phase580 native funding CSV integrity readback
The GitHub connector read the full bytes of the four V98 branch-native funding CSVs, computed SHA256 independently from the remote manifest, and checked the Dec-2022 through Dec-2025 settlement calendar. Results:

| Asset | Full-file SHA256 | Native full rows | Training rows | Training zero-rate rows |
|---|---|---:|---:|---:|
| BTCUSDT | `10839ac3f83a2d5dd92bb2bdf17a6de00ebad0def6f81358c9bd557a58342e47` | 4383 | 3381 | 0 |
| ETHUSDT | `29033fb7d429696172d964042d6cdf3be784d0e81c0d50c7cb914a9757eeea51` | 4383 | 3381 | 0 |
| BNBUSDT | `229c8eeaef1b0b0dd34d78aeb8584ea471b360344bc3c1e0f4158f3cf06f5484` | 4383 | 3381 | 1852 |
| SOLUSDT | `86430b3443ae1980e00a181c3d2f8dd47ddede05b8c4b4b86052696594626c06` | 4458 | 3381 | 0 |

All four full-file SHA256 values match the pinned Phase206 manifest. Each training calendar has 3,381 strictly increasing unique 8-hour settlement slots, no duplicates, no 2026+ rows. The BNB zero-rate share is 54.78%; the longest consecutive zero streak is **77 settlements** (2024-07-03 16:00 through 2024-07-29 00:00 UTC). This is a source anomaly requiring vendor provenance resolution, not an assumption of zero true funding.

## Research decision and boundaries
**PASS: remote branch-native CSV byte identity and exact Phase460 prereg publication.**
**BLOCKED: independent official Binance ZIP+CHECKSUM/API vendor-origin attestation; BNB zero-rate conflict.**
No XRP, external engine benchmarks, contaminated holdout, 2026+ training data, trading signals or historical PnL were used. No seven-slot champion is promoted. Phase252 remains a partial internal comparator. Only V98-namespaced branch files were written.
