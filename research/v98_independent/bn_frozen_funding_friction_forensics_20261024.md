# V98 Independent BN — frozen post-rejection funding and friction forensics (2026-10-24)

**No refit.** This report only attributes original BN historical training positions; BN remains rejected. Executed post-rejection diagnostic: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40076101663 . Frozen original economic training: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40075856289 . Independent native event replay: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40075859107 .

## Native signed funding attribution, USD $10k, 2023–24

| Frozen path / friction | BTC | ETH | BNB | SOL | Total funding | Fees | Slippage |
|---|---:|---:|---:|---:|---:|---:|---:|
| BN full, base | -601.6520 | -585.6108 | +1.9332 | -13.0918 | **-1198.4213** | 347.9932 | 347.9932 |
| BN full, severe | -510.0131 | -494.6037 | +0.8977 | -10.9729 | **-1014.6919** | 1226.8940 | 1840.3409 |
| BN core-only, base | -1060.5812 | -1133.5095 | 0 | 0 | **-2194.0907** | 22.6615 | 22.6615 |
| BN core-only, severe | -1051.0423 | -1123.1422 | 0 | 0 | **-2174.1845** | 90.0390 | 135.0585 |

These are path-dependent cashflows, not additive standalone alpha or isolated causal module contributions: full and core-only have different inventory, wealth and risk ratchets.

**Measured structural obstacle:** under base friction, the complete engine reduced absolute funding outflow by approximately $995.67 versus core-only, but paid ~$650.66 additional execution friction. Under severe friction, the full engine paid ~$2,842.14 more fees+slippage than core-only while its funding outflow was ~$1,159.49 lower. Thus severe incremental execution friction overwhelms the observed funding improvement, before considering differences in directional PnL and inventory. A high-turnover funding hedge is not a durable wealth-compounding solution.

**Cross-check:** the post-rejection diagnostic independently recomputed per-asset signed funding, execution costs, turnover and mark-to-market contributions for original frozen full/core-only base/severe paths and reconciled aggregated funding/fees/slippage/turnover against the original settlement receipts. It does not certify future returns.

**Critical-path next hypothesis, not a modification of BN:** investigate a genuinely new seven-slot system with sparse, multi-week funding-aware inventory *and an ex-ante cost budget for each module* rather than attempting to recover funding through frequent trades. Pre-register all new choices before looking at new economic outputs. Continue 90-cell physical/independent gates; do not use 2025 holdout until training candidate is frozen and passes its own gates. No 2026+ data, XRP, contaminated Phase083 or external V14/V15/V99.

**Decision:** BN permanently rejected; no current V98 fully validated or live-authorized.
