# V98 Independent A1 — authenticated replay disposition (2026-11-08)

Status: **REJECTED for promotion**, not a validated engine. This is an evidence disposition, not a new hypothesis or parameter adjustment. A1 code and preregistration remain frozen. No benchmark engines or future holdout accessed.

## Provenance
- GitHub Actions run: 42496553802, completed success (technical execution only); artifact 13623334663, sha256 feaecb49d295fe5633f71ee675f904d9a61d84856aa78269bde8ffda01798e52.
- Price artifact 13444665313; funding artifact 13464271018. Price manifest sha256 01e7bdeb8bcaf34ee898e322cf20f4479c0e25a9066b40f8cd2446286259f8a8; funding manifest sha256 f33094dfc065aa862a529d46f36e15f8a418ab085780214a0423488d2ff49622.
- 27,048 hourly observations; 108,192 slot decisions; causal previous-hour decision/next-open execution; BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT; no 2026+ or contaminated holdout.

## Full-sample results (starting USD 10,000)
| Cost multiple | Final equity USD | CAGR | Max drawdown | Hourly profit factor | Positive days |
|---|---:|---:|---:|---:|---:|
| 1x | 19,948.34 | 25.08% | -25.71% | 1.0386 | 431/1127 |
| 2x | 12,815.40 | 8.37% | -35.98% | 1.0174 | 416/1127 |
| 4x | 5,287.87 | -18.66% | -60.67% | 0.9763 | 385/1127 |

At normal costs, annual calendar returns: 2023 +72.33%; 2024 +17.50%; 2025 -1.46%. Under 2x costs, 2025 -14.74%; under 4x, 2024 -26.63%, 2025 -36.18%. These are descriptive calendar slices, not independent chronological train/validation.

## Decision
The preregistered stress gate explicitly forbids promotion if severe/supersevere stress collapses. A1 loses 47.12% of initial capital under 4x costs, with -60.67% drawdown and PF <1; 2025 is negative even under normal costs. **Reject A1 for robustness/promotion.** Positive normal-cost CAGR is not independent validation, and successful CI is not strategy approval. The Relative-Value slot remains only a momentum proxy, another architectural incompleteness. No tuning of A1 after this observation; next candidate must be genuinely distinct, preregistered before economic outcomes, and assessed with separate chronological validation and marginal sleeve contributions. Preserve holdout, Frozen and paper state.
