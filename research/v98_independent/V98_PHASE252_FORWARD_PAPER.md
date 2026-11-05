# V98 Phase252 forward paper shadow

This is **paper only** and is intentionally quarantined from V98 model selection.

Run on a machine/network that is lawfully allowed to access the official Binance USD-M public API:

```bash
python research/v98_independent/v98_phase252_forward_paper.py
```

Run it at least once after each completed UTC hour; hourly scheduling is recommended.

The script refuses HTTP 403/418/451 and never switches host/provider. It writes:
- `research/v98_independent/paper_phase252_forward/state.json`
- `research/v98_independent/paper_phase252_forward/ledger.csv`

Do **not** use forward paper outcomes to tune the V98 research engine. They are observational evidence only.

GitHub-hosted runners currently receive HTTP 451 from the required USD-M REST endpoint, so this exact paper feed must run on an authorized network or a self-hosted runner with lawful access. Do not bypass access restrictions.
