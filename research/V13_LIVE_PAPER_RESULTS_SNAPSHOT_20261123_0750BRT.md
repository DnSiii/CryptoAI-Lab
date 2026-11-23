# V13 live paper-results snapshot — 2026-11-23 07:50 BRT

Read-only source: `paper-results:reports/paper_v13_ledger.json`, GitHub blob SHA `b1a51c528f20e374ac761a18eb91bbb6c4cd5532`, branch head `e4405392619746a913151f3601a0efcd0072e50d`. The JSON reports `latest_data_timestamp=2026-11-23T09:00:00+00:00` and 838 decisions.

Independent enumeration over every `decisions[*].adjustments[*]` (1,739 adjustments): 1,425 rows missing raw notional; 310 rows with raw/display disagreement at two-decimal rounding; 3 matching positive rows; 1 legitimate positive raw subcent displayed zero. The 310 figure is specific to this exact blob and must not be conflated with 272/300/302 from older snapshots. Example decision 681 ETHUSDT: display 7.81, raw 7.7148818969287944; latest decision 837 BTCUSDT: display 4.72, raw 3.901731892434479. Neither is a rounding issue.

This is a **research-only provenance finding, NOT certification**. The ledger's latest-data timestamp does not prove exchange fills or paper realized PnL. Recover original source snapshots, original generating commit, original capital conversion and per-decision inputs, then produce append-only reconciliation manifest and rerun fail-closed CI. No mutation of published paper, V16/V99 Frozen, holdout or trade history. No orders. NO PROMOTION.
