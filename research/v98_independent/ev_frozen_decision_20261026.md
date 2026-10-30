# V98 Independent EV — immutable rejected decision (2026-10-26)
Pre-registered before economic PnL at commit 878bf97c3b9e5bc496271d1809cc90a647d7c0ad. Authenticated Clean-4 2023–2024 training only; no 2025 holdout or external benchmarks.

- Source-only causal gate PASS: 2023 active epochs Opportunity 19, RV 21, Stress 7; 2024 Opportunity 11, RV 20, Stress 6. Future mutation invariance PASS.
- Native physical 30/30 cells survived; two OS numerical reproduction PASS, artifact audit no errors. Workflow: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40266223579
- Full base CAGR 81.7396%, severe 70.5543%; severe max drawdown 27.9061% (carried-before-fill).
- Full base turnover USD664,853.04, severe USD601,772.70, both above locked USD600,000 cap.
- Annual 2023 and 2024 full net growth positive under base/severe both funding orders, but ALL three sleeve annual marginal gates FAIL. Example base carried-before-fill annual full-minus-RV net log growth 2023 -0.0085173 and 2024 -0.0014119; full-minus-Opportunity 2023 -0.0041205; full-minus-Stress 2023 -0.0024478.
- Full vs core base carried-before-fill ending NAV -USD32.52; added USD12,502.35 turnover. Under severe new-after-fill ending NAV -USD625.96.
- Independent signed all-hour settlement oracle PASS five books, 526,290 settled hours and 65,760 funding-event hours. Workflow https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40266269727
- Frozen immutable native cost/marginal forensics: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40266415107

**FINAL: REJECT_EV_HISTORICAL_GROWTH_OR_MARGINAL.** No rescue, no holdout unlock, no benchmark comparison, no paper/live order authorization. Keep source and thresholds immutable for reproducibility.
