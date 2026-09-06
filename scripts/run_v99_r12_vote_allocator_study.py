from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
sys.path.insert(0, str(PROJECT / "scripts"))

from cryptoai_v13.allocator import multihorizon_two_sleeve_targets
from cryptoai_v13.backtest import exact_fast, screen
from cryptoai_v13.v99 import V99AsymmetricSpec, _cap_gross
from cryptoai_v13.v99_r4 import V99R4ControlSpec, _sparse_side_shock
from cryptoai_v13.v99_r5 import asymmetric_v99_targets_r5
from paper_once_v99 import load_execution
from paper_once_v16 import build_v16
from run_candidate_v99 import calendar_year_summaries, horizon_summary, rolling_robustness, summary, tail_and_capture

CONFIG_PATH = PROJECT / "config" / "candidate_v99_asymmetric.json"
REPORT_PATH = PROJECT / "reports" / "candidate_v99_r12_vote_allocator_study.json"
WINDOWS = (45, 60, 90, 120, 180, 240)
FAST_POLICY = {"threshold": 0.058, "multiplier": 0.55, "cooldown": 6}


def replay(data, targets, execution, gross_cap, cost):
    return exact_fast(
        data, targets,
        cost_per_side=cost,
        maintenance_equity_fraction=execution["maintenance_equity_fraction"],
        gross_guard_cap=gross_cap,
        drawdown_guard_threshold=FAST_POLICY["threshold"],
        drawdown_guard_multiplier=FAST_POLICY["multiplier"],
        drawdown_guard_cooldown_hours=FAST_POLICY["cooldown"],
    )


def eval_all(equity, parent_equity, required, anti):
    full = summary(equity); pfull = summary(parent_equity)
    req = {str(d): {"v99": horizon_summary(equity,d), "parent": horizon_summary(parent_equity,d)} for d in required}
    ah = {str(d): {"v99": horizon_summary(equity,d), "parent": horizon_summary(parent_equity,d)} for d in anti}
    roll = {str(d): rolling_robustness(parent_equity,equity,d) for d in anti}
    years=calendar_year_summaries(equity); py=calendar_year_summaries(parent_equity); common=sorted(set(years)&set(py))
    return {
        "full":full,
        "full_wealth_ratio_to_parent":(1+full["return"])/(1+pfull["return"]),
        "full_drawdown_improvement_fraction":1-abs(full["max_drawdown"])/abs(pfull["max_drawdown"]),
        "requested":req,"anti_overfit":ah,
        "anti_overfit_beat_fraction":sum(ah[str(d)]["v99"]["return"]>ah[str(d)]["parent"]["return"] for d in anti)/len(anti),
        "rolling":roll,
        "rolling_average_parent_beat_fraction":sum(v["candidate_beats_parent_fraction"] for v in roll.values())/len(roll),
        "calendar_years":years,
        "calendar_year_beat_fraction":sum(years[y]["return"]>py[y]["return"] for y in common)/max(1,len(common)),
        "tail":tail_and_capture(parent_equity,equity),
    }


def main():
    c=json.loads(CONFIG_PATH.read_text()); p=json.loads((PROJECT/'config'/c['parent_candidate_config']).read_text())
    if c.get('mode')!='PAPER_ONLY' or c.get('real_orders'): raise RuntimeError('R12 paper only')
    data,parent_targets,parent_result,_,quarantined=build_v16(p); execution=load_execution(p)
    spec=V99AsymmetricSpec(**c['asymmetric_overlay']); ctrl=V99R4ControlSpec(**c['r4_control'])
    proxy=screen(data,parent_targets,execution['base_cost_per_side']).equity
    r5,diag=asymmetric_v99_targets_r5(data,parent_targets,proxy,spec,ctrl)
    routine=r5.shift(4).fillna(0.0)
    sl,ss,_=_sparse_side_shock(data.close,parent_targets,ctrl)
    lf=pd.concat([diag['long_risk_factor'].astype(float),sl],axis=1).min(axis=1)
    sf=pd.concat([diag['short_risk_factor'].astype(float),ss],axis=1).min(axis=1)
    persistent=_cap_gross(routine.clip(lower=0).mul(lf,axis=0)+routine.clip(upper=0).mul(sf,axis=0),spec.maximum_gross)

    base_cost=execution['base_cost_per_side']
    pr=screen(data,parent_targets,base_cost).equity.pct_change(fill_method=None).fillna(0.0)
    rr=screen(data,persistent,base_cost).equity.pct_change(fill_method=None).fillna(0.0)
    # Pure vote: each horizon gives 100% of its vote to the sleeve with the
    # better trailing mean/std score. Averaging six votes creates weights in
    # sixths; there are no hand-tuned leading/lagging weight bands.
    mixed=multihorizon_two_sleeve_targets(parent_targets,persistent,pr,rr,windows_days=WINDOWS,funding_weight_when_leading=1.0,funding_weight_when_lagging=0.0,rebalance_hours=24)
    mixed=_cap_gross(mixed,spec.maximum_gross)
    gross_cap=float(c['circuit_breaker']['gross_drift_guard_cap'])
    base=replay(data,mixed,execution,gross_cap,base_cost); severe=replay(data,mixed,execution,gross_cap,execution['severe_cost_per_side'])
    required=[int(v) for v in c['research_gate']['required_horizons_days']]; anti=[int(v) for v in c['research_gate']['anti_overfit_horizons_days']]
    r=eval_all(base.equity,parent_result.equity,required,anti)
    pg=p['circuit_breaker']; ps=exact_fast(data,parent_targets,cost_per_side=execution['severe_cost_per_side'],maintenance_equity_fraction=execution['maintenance_equity_fraction'],gross_guard_cap=gross_cap,drawdown_guard_threshold=pg['drawdown_threshold'],drawdown_guard_multiplier=pg['exposure_multiplier'],drawdown_guard_cooldown_hours=pg['cooldown_hours'])
    r['severe_cost']=summary(severe.equity); r['parent_severe']=summary(ps.equity); r['severe_wealth_ratio_to_parent']=(1+r['severe_cost']['return'])/(1+r['parent_severe']['return'])
    r['turnover_total']=float(base.turnover.sum()); r['no_ruin']=not(base.ruin or severe.ruin)
    report={"study":"V99 R12 parameter-light multi-horizon vote allocator","allocator_windows_days":list(WINDOWS),"vote_rule":"1 vote per horizon to higher trailing mean/std sleeve; daily rebalance; final weight is vote fraction","parent":summary(parent_result.equity),"result":r,"funding_quarantined_symbols":quarantined}
    REPORT_PATH.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))

if __name__=='__main__': main()
