# V99 R106 — Phase140–143 zero-volume admissibility decision

Date: 2026-09-26

## Evidence harvested

Phase140 TRAIN workflow run `36239191380` reached the frozen contract successfully, then failed before any PnL/backtest was produced with:

`RuntimeError: BTC-USDT-SWAP: nonpositive/nonfinite quote volume`

The failure occurred inside source acquisition, before feature construction and before `run_targets`. Therefore no Phase140 PnL, temporal-fold result, holdout result, or selection information was observed.

The earlier Phase140 data-only gate admitted finite volumes using `volume >= 0`. That gate was sufficient for field/coverage/gap comparability, but not sufficient for the preregistered feature `log(OKX_notional_volume) - log(Binance_notional_volume)`, whose mathematical domain requires strictly positive inputs. Treating zero with epsilon, `log1p`, imputation, hour deletion, selective asset deletion, or a proxy would change the frozen feature after observing the failure and is prohibited.

## Decision

- **Phase140: DATA_INADMISSIBLE / PERMANENT REJECT.** No rescue, sign flip, parameter search, selective deletion, or proxy substitution.
- **Phase141: DATA_INADMISSIBLE / PERMANENT REJECT.** Its preregistration explicitly froze strict positivity before the successful Phase140 data-gate result and states that any zero/negative/non-finite consumed notional observation is inadmissible.
- **Phase142 and Phase143:** do not execute any formulation that consumes `log(notional_volume)` on this source/window unless their already-frozen contracts independently define a mathematically valid zero policy. No post-hoc epsilon/log1p/imputation is permitted.

## Integrity

V16 Frozen and V99 Frozen remain untouched. Holdout rows used for feature construction/selection remain 0/0. No PnL was computed from the failed Phase140 attempt. Causal t-1, chronological TRAIN-only selection, temporal-fold discipline, severe/supersevere downstream gates, regime matrix, benchmark envelope, reproducibility and anti-overfit rules remain unchanged.
