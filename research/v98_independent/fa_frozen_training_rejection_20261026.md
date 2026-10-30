# V98 Independent FA — immutable training rejection (2026-10-26)

**Precommitted before economic PnL** in `c95d34ab322d48d7a8a45daeeec28a1db5abd833`. FA is a complete seven-slot downside-adjusted breadth/breakout/relative-acceleration/dispersion portfolio. All source/price/funding reads restricted to authenticated Clean-4 December 2022 warmup and 2023–2024 training. No 2025 validation, 2026+, XRP, Phase083, external V14/V15/V99 benchmarks, Frozen, paper or live.

## Verified workflow
- Run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40273168944 (commit `beb66d7797041d0eb7ba6ff9866f24b5fc392938`).
- Source-only future-mutation PASS; activation epochs 2023: core 92, opportunity 15, RV 52, stress 26; 2024: core 91, opportunity 4, RV 48, stress 38. All preregistered >=4 gates PASS. Note 2024 Opportunity only just meets the minimum.
- All 30 physical USD10k cells survived; cross-OS 22.04/24.04 numerical reproducibility PASS; artifact-only audit errors []; full annual log growth gates PASS.
- Independent five-book every-settled-hour signed ledger oracle PASS: 105,258 settled hours and 13,152 funding event hours per book, total **526,290 hourly and 65,760 funding checks**. Ledger correctness is not alpha validation.

## Actual historical economics (carried-before-fill)
- Full base two-year CAGR **96.393882%**, severe **86.215417%**; ending NAV from USD10,000 **USD38,606.21 base**, **USD34,705.71 severe**.
- Full base annual net returns: 2023 **+180.517911%**, 2024 **+37.624764%**. Severe 2023 **+167.252154%**, 2024 **+29.861281%**.
- Max drawdown base **34.941371%**, severe **36.005013%**; base hourly PF **1.044446**, payoff **0.987006**, win rate **51.413750%**, positive UTC days **374** over two years.
- Full base turnover **USD622,099.89** > locked USD600,000 maximum; severe **USD574,036.52**. Base fees **USD311.05**, slippage **USD311.05**, native signed funding **-USD3,069.86**. Severe fees **USD1,148.07**, slippage **USD1,722.11**, funding **-USD2,832.42**.
- Core-only base ending NAV **USD38,011.85**, 2023 +170.829194%, 2024 +40.353588%, turnover USD562,344.25. Full ends USD594.36 higher overall, but grows less in 2024. Core-only severe NAV USD34,398.15.
- Locked annual marginal log-growth FAIL for **all three sleeves**. Carried-before-fill base 2024 full-minus-Opportunity **-0.0075852**, full-minus-RV **-0.0035712**, full-minus-Stress **-0.0168152**. Severe 2024 respectively **-0.0085008**, **-0.0040103**, **-0.0191409**. Negative results persist under new-after-fill ordering.
- High-growth and severe drawdown gates PASS; turnover and all three annual marginal gates FAIL. **FINAL: REJECT_FA_HISTORICAL_GROWTH_OR_MARGINAL** (no changes to thresholds, signs, windows or leverage).

FA cannot be promoted or used to justify V98 completion; preserve its artifacts and rejection. 2025 holdout remains untouched. No external benchmark, paper or live trading.
