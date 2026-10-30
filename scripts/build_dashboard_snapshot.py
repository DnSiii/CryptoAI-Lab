from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
REPORTS = PROJECT / "reports"
DASHBOARD = PROJECT / "dashboard"


def pct(value: float) -> float:
    return round(value * 100.0, 4)


def rolling_window(equity: pd.Series, hours: int) -> dict[str, float]:
    values = equity.div(equity.shift(hours)).sub(1.0).dropna()
    return {
        "medianPct": pct(float(values.median())),
        "maxPct": pct(float(values.max())),
        "positivePct": pct(float((values > 0.0).mean())),
        "p10Pct": pct(float(values.quantile(0.10))),
    }


def longest_underwater_days(equity: pd.Series) -> float:
    underwater = equity < equity.cummax()
    groups = underwater.ne(underwater.shift()).cumsum()
    longest = int(underwater.groupby(groups).sum().max()) if len(underwater) else 0
    return round(longest / 24.0, 1)


def compact_candles(
    prices: pd.DataFrame, entry: pd.Timestamp, exit_: pd.Timestamp
) -> list[dict[str, object]]:
    window = prices.loc[entry - pd.Timedelta(hours=12) : exit_ + pd.Timedelta(hours=12)]
    stride = max(1, math.ceil(len(window) / 96))
    sampled = window.iloc[::stride].copy()
    for timestamp in (entry, exit_):
        if timestamp in window.index and timestamp not in sampled.index:
            sampled.loc[timestamp] = window.loc[timestamp]
    sampled = sampled.sort_index()
    return [
        {
            "time": timestamp.isoformat(),
            "open": round(float(row.open), 8),
            "high": round(float(row.high), 8),
            "low": round(float(row.low), 8),
            "close": round(float(row.close), 8),
        }
        for timestamp, row in sampled.iterrows()
    ]


def operation_record(
    trade: dict[str, object], prices: pd.DataFrame, label: str
) -> dict[str, object]:
    entry = pd.Timestamp(str(trade["entry"]))
    exit_ = pd.Timestamp(str(trade["exit"]))
    entry_price = float(prices.loc[entry, "open"])
    exit_price = float(prices.loc[exit_, "open"])
    operation_id = f"tst-{entry.strftime('%Y%m%d%H')}"
    return {
        "id": operation_id,
        "symbol": "TSTUSDT",
        "label": label,
        "entry": entry.isoformat(),
        "exit": exit_.isoformat(),
        "direction": trade["direction"],
        "hours": int(trade["hours"]),
        "portfolioReturnPct": pct(float(trade["equity_return"])),
        "entryPrice": round(entry_price, 8),
        "exitPrice": round(exit_price, 8),
        "maxPortfolioWeightPct": pct(float(trade["maximum_absolute_weight"])),
        "candles": compact_candles(prices, entry, exit_),
    }


def main() -> None:
    finalist = json.loads(
        (REPORTS / "candidate_v13_circuit_breaker_validation.json").read_text()
    )
    tst = json.loads((REPORTS / "tst_impulse_capture.json").read_text())
    equity_frame = pd.read_csv(
        REPORTS / "candidate_v13_circuit_breaker_equity.csv",
        index_col="timestamp",
        parse_dates=True,
    )
    equity = equity_frame["equity"]
    equity.index = pd.to_datetime(equity.index, utc=True)
    equity = equity.loc["2021-01-01":]
    prices = pd.read_csv(
        PROJECT / "data" / "canonical" / "TSTUSDT_1h.csv",
        index_col="timestamp",
        parse_dates=True,
    )
    prices.index = pd.to_datetime(prices.index, utc=True)

    by_scenario = finalist["scenarios"]
    candidate = by_scenario["base"]

    trades = tst["base"]["trades"]
    latest = sorted(trades, key=lambda item: item["entry"], reverse=True)[:10]
    best = max(trades, key=lambda item: item["equity_return"])
    worst = min(trades, key=lambda item: item["equity_return"])
    selected: list[tuple[dict[str, object], str]] = [(trade, "recent") for trade in latest]
    for trade, label in ((best, "highlight-win"), (worst, "highlight-loss")):
        if trade not in [item[0] for item in selected]:
            selected.append((trade, label))

    operations = [operation_record(trade, prices, label) for trade, label in selected]
    monthly = equity.resample("ME").last().pct_change(fill_method=None).dropna()
    recent_months = [
        {"month": timestamp.strftime("%Y-%m"), "returnPct": pct(float(value))}
        for timestamp, value in list(monthly.items())[-12:]
    ]

    scenario_labels = {
        "base": "Finalista · custos-base",
        "severe_cost": "Custos severos",
        "delay_3h": "Atraso de 3h",
        "adverse_funding": "Funding adverso",
        "severe_cost_and_adverse_funding": "Custos + funding adverso",
    }
    validation = []
    for scenario in (
        "base",
        "severe_cost",
        "delay_3h",
        "adverse_funding",
        "severe_cost_and_adverse_funding",
    ):
        metric = by_scenario.get(scenario)
        validation.append(
            {
                "scenario": scenario_labels[scenario],
                "status": "complete" if metric else "pending",
                "cagrPct": pct(metric["cagr"]) if metric else None,
                "drawdownPct": pct(metric["max_drawdown"]) if metric else None,
                "median30dPct": None,
                "positive30dPct": pct(metric["positive_month_ratio"]) if metric else None,
            }
        )
    validation.append(
        {
            "scenario": "Bootstrap dinâmico · 180 mil",
            "status": "complete",
            "cagrPct": None,
            "drawdownPct": None,
            "median30dPct": None,
            "positive30dPct": None,
        }
    )

    output = {
        "generatedAt": pd.Timestamp.now(tz="UTC").isoformat(),
        "mode": "research",
        "liveOrders": False,
        "candidate": {
            "name": "V13 · Carry-Core + disjuntor de 14 dias",
            "status": "Finalista histórico — pronto para iniciar paper trading",
            "oneDay": rolling_window(equity, 24),
            "sevenDay": rolling_window(equity, 24 * 7),
            "thirtyDay": rolling_window(equity, 24 * 30),
            "drawdownPct": pct(candidate["max_drawdown"]),
            "longestRecoveryDays": longest_underwater_days(equity),
            "historicalCagrPct": pct(candidate["cagr"]),
            "bootstrapRuinPct": pct(
                finalist["bootstrap"]["worst_estimated_ruin_probability"]
            ),
        },
        "tstDiagnostic": {
            "status": "Reprovado nesta configuração: excesso de entradas com ruído",
            "trades": tst["base"]["trade_count"],
            "winRatePct": pct(tst["base"]["win_rate"]),
            "payoffRatio": round(tst["base"]["payoff_ratio"], 2),
            "bestTradePct": pct(tst["base"]["best_trade"]["equity_return"]),
            "worstTradePct": pct(tst["base"]["worst_trade"]["equity_return"]),
            "totalPct": pct(tst["base"]["metric"]["return"]),
        },
        "recentMonths": recent_months,
        "validation": validation,
        "operations": operations,
        "disclosures": [
            "Resultados são de replay histórico, não de capital real.",
            "Retorno da operação é o impacto estimado no patrimônio, já considerando o peso usado.",
            "TST é um diagnóstico isolado e não representa a seleção final entre todos os ativos.",
            "O finalista passou em custos, atraso, funding e bootstrap dinâmico, mas o histórico foi pesquisado iterativamente.",
            "Paper trading usa somente dados futuros e continua sem qualquer ordem ou dinheiro real.",
        ],
    }
    DASHBOARD.mkdir(exist_ok=True)
    (DASHBOARD / "dashboard_data.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
