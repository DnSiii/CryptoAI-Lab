# V98 Independent — Phase215 audit

## Decision
REJECT_FAMILY_NO_RESCUE.

The preregistered cross-sectional alt relative-strength dispersion family produced 0/8 training-fold coherent specs under the mechanical gate (base return > 0 and PF > 1 in each of 2023, 2024, 2025). No post-hoc inversion, threshold rescue, regime filter, or holdout opening is permitted.

## Reproducibility / integrity
- GitHub Actions run 37029389208 completed successfully.
- Firewall `<2026-01-01` passed for canonical prices and PIT funding inputs.
- Two independent deterministic evaluations produced identical file SHA256: `9f6bca114a6f6e7536de82b06df067e5d8a3d3beca6c2dc3308a3a5ad6cf6f65`.
- Result payload reports deterministic payload SHA256 `7817cb97a2a4050c85703c3bfa6d19fa557461e65dd0793cc4a89726ae53a3e5`.

## Failure mechanism audit
Representative frozen spec `xs_L24_d150_hold3`, 2023 base:
- return: -11.81%
- PF: 0.9956
- max drawdown: -53.20%
- payoff: 1.2049
- win rate: 41.05%
- positive days: 41.92%
- trades: 2,555
- max asset concentration: 41.49%
- tails p01/p99: -2.157% / +2.763%

Asset attribution is not a clean diversified edge: SOL contributed +28.16%, while BNB -12.06%, ETH -4.20%, XRP -23.45%. Regime decomposition is similarly weak: bear -16.03% / PF 0.9105, bull +1.44% / PF 1.0112, sideways +3.53% / PF 1.0143. Selecting only the mildly positive regimes would be a post-hoc rescue and is prohibited.

Cost stress exposes insufficient gross edge. The same 2023 spec falls to -70.25% under severe costs; PF 0.9038 and MDD -80.72%. This is consistent with a high-turnover spread whose small pre-cost expectancy cannot absorb realistic friction.

## Scientific conclusion
Cross-sectional alt relative-strength dispersion, as preregistered, is rejected. The result argues against spending further multiplicity budget on nearby lookbacks/dispersion thresholds/holds. Next work must be a genuinely distinct causal mechanism and must be preregistered before observing its results. Validation/final holdout remains untouched.
