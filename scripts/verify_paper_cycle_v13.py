from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((PROJECT / path).read_text())


def main() -> None:
    finalist = load("config/candidate_v13_circuit_breaker.json")
    state = load("state/paper_v13_state.json")
    snapshot = load("reports/paper_v13_snapshot.json")
    ledger = load("reports/paper_v13_ledger.json")
    sync = load("reports/paper_data_sync_v13.json")

    if finalist.get("real_orders") is not False:
        raise RuntimeError("a configuração congelada não proíbe ordens reais")
    if state != snapshot:
        raise RuntimeError("estado e snapshot paper divergiram")
    if state.get("mode") != "PAPER_ONLY":
        raise RuntimeError("runner saiu do modo PAPER_ONLY")
    if state.get("real_orders_enabled") is not False:
        raise RuntimeError("runner habilitou ordens reais")
    if ledger.get("mode") != "PAPER_ONLY" or ledger.get("schema_version") != 2:
        raise RuntimeError("ledger didático inválido ou fora do modo PAPER_ONLY")
    if ledger.get("paper_start_after_timestamp") != state.get("paper_start_after_timestamp"):
        raise RuntimeError("ledger e estado divergem no corte forward")
    if ledger.get("latest_data_timestamp") != state.get("latest_data_timestamp"):
        raise RuntimeError("ledger e estado divergem no último candle")
    if not {"BTCUSDT", "ETHUSDT"}.issubset(ledger.get("candles", {})):
        raise RuntimeError("ledger não contém candles BTC e ETH")
    if not {"BTCUSDT", "ETHUSDT"}.issubset(ledger.get("assets", {})):
        raise RuntimeError("ledger não contém atribuição por ativo")
    asset_net = sum(
        float(item["net_result_brl"]) for item in ledger["assets"].values()
    )
    if abs(asset_net - float(ledger["summary"]["net_result_brl"])) > 0.05:
        raise RuntimeError("resultado por ativo não reconcilia com o total")
    if sync.get("mode") != "PUBLIC_DATA_ONLY" or sync.get("private_api_used") is not False:
        raise RuntimeError("sincronização não está limitada a dados públicos")
    if sync.get("core_stale"):
        raise RuntimeError(f"dados centrais atrasados: {sync['core_stale']}")
    if sync.get("source_method") != "OFFICIAL_CHECKSUMMED_DAILY_ARCHIVES":
        raise RuntimeError("fonte incremental não usa os arquivos oficiais verificados")
    lag = int(sync.get("publication_lag_hours", -1))
    maximum_lag = int(sync.get("maximum_publication_lag_hours", -1))
    if lag < 0 or maximum_lag < 0 or lag > maximum_lag:
        raise RuntimeError(f"atraso de publicação inválido: {lag}h")

    expected = pd.Timestamp(sync["expected_latest_closed_hour"])
    latest = pd.Timestamp(state["latest_data_timestamp"])
    boundary = pd.Timestamp(state["paper_start_after_timestamp"])
    initialized = pd.Timestamp(state["initialized_at_utc"])
    if latest < expected:
        raise RuntimeError(f"snapshot atrasado: {latest} < {expected}")
    if boundary < initialized.floor("h"):
        raise RuntimeError("corte paper anterior à hora de inicialização")
    if state.get("status") != "tracking" or int(state.get("new_forward_hours", 0)) <= 0:
        raise RuntimeError("nenhuma hora forward posterior ao corte foi contabilizada")

    print(
        json.dumps(
            {
                "verified": True,
                "mode": state["mode"],
                "real_orders_enabled": state["real_orders_enabled"],
                "paper_start_after_timestamp": state["paper_start_after_timestamp"],
                "latest_data_timestamp": state["latest_data_timestamp"],
                "new_forward_hours": state["new_forward_hours"],
                "decision_events": ledger["summary"]["decision_events"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
