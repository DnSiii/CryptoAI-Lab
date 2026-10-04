# V98 Independent Phase231 — post-mortem

Decision: **REJECT_FAMILY_NO_RESCUE**. Phase231 is not eligible for promotion or parameter rescue.

## Evidence harvested
Decision-grade workflow 37229687535 completed successfully, including training-only rebuild, firewall/frozen invariants, deterministic duplicate runs, independent validation/gate, and V98-only result commit. The committed payload SHA256 is `69b1f1935d9087e39725f3738a1e35c7aeaf3ced086b68bfebbb47eba30974fe`.

The family fails economically rather than by infrastructure. Representative preregistered spec `vol_disp_lb168_k1_h4` loses -71.76% in 2023 base with PF 0.902, payoff 0.920, max DD -74.19%, win rate 49.50%. Its bear/bull/sideways returns are all negative (-6.93%/-40.56%/-48.95%). Severe and supersevere worsen total return monotonically to -73.89% and -77.68%. Asset attribution is highly concentrated (max concentration 75.27%) with SOL contribution -1.403 in 2023 base, so the failure is not a hidden diversified edge erased only by aggregate accounting.

The same representative spec remains negative in 2024 base (-56.43%, PF 0.941, max DD -64.07%); bear/bull/sideways are again non-positive (-27.67%/-36.50%/-5.15%). This is inconsistent with a robust cross-sectional volatility-dispersion premium under realistic costs.

## Scientific interpretation
The proposed low-realized-vol long / high-realized-vol short relative-value relation does not survive chronological annual folds. Costs worsen an already negative gross structure; they are not the primary explanation. Regime decomposition does not reveal a broad omitted state in which a rescue would be scientifically justified. Concentration/tails reinforce rejection rather than motivate asset deletion, sign flip, regime filtering, or threshold tuning.

No Phase231 observation may be used to alter the already-frozen Phase232 grid. Holdout 2026+ remains unopened. Champion remains unchanged.