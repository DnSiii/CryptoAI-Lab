# V98 Independent DC — post-rejection artifact-only native price/funding/cost attribution (2026-10-25)

**No new strategy PnL, no parameter retuning or rescue.** From the pinned 20-cell historical receipts of permanently rejected DC, compute for each complete/ablation path the exact cash-ledger identity:

`price_PnL = final_NAV - initial_NAV - signed_native_funding + fees + slippage`

Then compute full-minus-counterfactual path differences. The identity was independently asserted to USD 0.000001 precision; this is a path-level counterfactual, **not** standalone per-sleeve alpha or event-level proof. Audit: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40159917171 . Original native historical run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40159679454 .

## Full-minus-ablation cumulative USD, initial $10,000, carried-before-fill
| Comparison | Cost | Total final NAV difference | Price PnL difference | Signed funding difference | Extra fees+slippage |
| --- | --- | ---: | ---: | ---: | ---: |
| Full minus core only | Base | -$3,238.80 | -$3,979.73 | +$579.28 | -$161.66 |
| Full minus core only | Severe | -$2,072.77 | -$3,301.84 | +$557.32 | -$671.75 |
| Full minus no RV | Base | **-$6,580.92** | **-$7,481.90** | +$625.71 | -$275.27 |
| Full minus no RV | Severe | **-$6,548.26** | **-$8,694.42** | +$601.47 | -$1,544.69 |
| Full minus no Stress | Base | -$3,415.82 | -$3,223.02 | -$171.86 | +$20.94 |
| Full minus no Stress | Severe | -$3,052.17 | -$2,787.02 | -$152.20 | +$112.95 |
| Full minus no Opportunity | Base | +$801.33 | +$814.58 | -$26.27 | -$13.01 |
| Full minus no Opportunity | Severe | +$1,087.58 | +$1,011.12 | +$3.38 | -$73.08 |

**Mechanism:** Unconditional cross-sectional native funding spread RV did collect a favorable relative funding difference, but its negative counterfactual price/interaction difference was an order of magnitude larger. The RV problem is not a missing funding feed or an execution-fee typo; it is economically harmful exposure/interaction in this training regime. Opportunity helped the final NAV in both cost scenarios, but failed the preregistered annual/funding-order robustness gates, so no sleeve or architecture is promoted. Stress also harmed final NAV.

**Next research direction (not an approved design):** before another complete engine, preregister a genuinely different conditional RV exposure whose expected *price leg* and funding are economically aligned; independently audit event-level position attribution and physical core displacement. Do not select its sign/window from DC results, reuse rejected DC signals, or access the sealed 2025 holdout. Frozen and paper untouched.
