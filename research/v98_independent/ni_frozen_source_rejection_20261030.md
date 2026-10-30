# V98 NI — immutable original source rejection (2026-10-30)

**REJECT_SOURCE_ONLY. PERMANENT.** NI was preregistered at commit `70b380ad8f15ea55e02886ad86ffdcde95fe0d89`, before source/PnL. Original source-only run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41083930592 (strategy SHA `094175de01a53ce49ae73d241868f24f9353b32c`).

Independent 17,544-hour source replay found zero hourly weight/activity mismatches, zero silent changes, 53/53 forced biweekly core refreshes, 9,144 native signed funding events and synthetic causal future-mutation PASS. **Opportunity activity failed the immutable >=8/year gate**: 2023=6, 2024=7. RV 2023=17/2024=13 and Stress 2023=6/2024=7 passed their own activity minima. Exact failures: `NI_MINIMUM_2023_Opportunity`, `NI_MINIMUM_2024_Opportunity`.

The original workflow correctly stopped **before all 30 PnL cells**; therefore no NI CAGR, PF, drawdown, or trading return exists. The independent PnL/fill/arithmetic steps were skipped logically due to missing receipts (their GitHub step success is not a validation pass). **No parameter/window/threshold adjustment or re-run is permitted to rescue NI.**

Official native signed rates and conservative mark-envelope source contract remain unchanged; exact funding-tick markPrice remains externally unproven. No 2025 validation, 2026+, Phase083, XRP or external V14/V15/V99 benchmark data accessed. Only V98 Independent files were added. Frozen, V99 and paper untouched.
