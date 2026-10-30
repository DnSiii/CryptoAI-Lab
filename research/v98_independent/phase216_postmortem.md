# V98 Independent — Phase216 post-mortem

## Decision
**REJECT_FAMILY_NO_RESCUE.** The preregistered mechanical training gate has zero coherent specs across calendar 2023, 2024, and 2025. Validation/final holdout remains unopened. No inversion, regime rescue, threshold expansion, or V99 information is permitted.

## Reproducibility / integrity
GitHub Actions run 37042974292 completed successfully. Training-only rebuild and `<2026-01-01` firewall passed. Two deterministic executions produced the same report SHA256 `a536fa50f6034a0a065bb03fa28d1ade4d5ca6e2891636f80d9286f4ffc0632d`. Mechanical gate returned `training-fold coherent specs: []`.

## Failure mechanism audit
Representative frozen spec `idio_z2.0_q50_hold3` is already decisively negative in base conditions:
- 2023: return -61.22%, PF 0.7614, MDD -61.22%, payoff 1.2288, positive days 17.26%, 273 trades. All bull/bear/sideways regime returns are negative; SOL and BNB are especially weak. Severe falls to -72.42% and supersevere to -86.06%.
- 2024: return -10.87%, PF 0.9990, MDD -41.99%, 521 trades. Sideways alone is positive (+21.55%, PF 1.1628), while bull and bear are negative; this is not eligible for post-hoc regime filtering. Severe falls to -50.82% and supersevere to -85.05%.
- 2025: return -65.22%, PF 0.8394, MDD -66.98%, 552 trades, with ETH attribution -56.62% and max asset concentration 74.08%. Bull, bear and sideways are all negative.

The family therefore fails before any holdout consideration. The payoff above 1 in several cells does not rescue the very low realized win rate / positive-day frequency, adverse tails and cost sensitivity. The instability across assets and regimes argues against a stable idiosyncratic mean-reversion edge rather than merely a poor single threshold.

## Data-quality note
The evaluator emitted pandas `pct_change` FutureWarnings because the default fill behavior will change in a future pandas release. Current deterministic SHA equality shows no run-to-run ambiguity, but subsequent evaluators should explicitly use `fill_method=None` so missing observations cannot be silently forward-filled by a library default.

## Anti-overfit conclusion
Do not tune Phase216. Do not invert it. Do not select its 2024 sideways pocket. Proceed only to a scientifically distinct preregistered family using training data and the same untouched holdout discipline.
