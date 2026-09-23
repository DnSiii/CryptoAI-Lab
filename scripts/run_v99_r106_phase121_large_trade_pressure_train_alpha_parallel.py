# Infrastructure-only parallel executor for preregistered Phase121.
# Scientific feature/evaluation remain delegated to the frozen Phase121 implementation.
from __future__ import annotations
import concurrent.futures as cf
import json, os
import pandas as pd
import run_v99_r106_phase121_large_trade_pressure_train_alpha as p


def _one(args):
    s, dates, index = args
    series, count = p.build_symbol(s, dates, index)
    return s, series, count


def main():
    assert (p.PROJECT/'research'/'v99_r106_phase121_large_trade_pressure_prereg.md').exists()
    p120=json.loads((p.PROJECT/'reports'/'candidate_v99_r106_phase120_raw_taker_imbalance_train_alpha.json').read_text()); assert p120['status']=='TRAIN_ALPHA_REJECT'
    p119=json.loads((p.PROJECT/'reports'/'candidate_v99_r106_phase119_aggtrades_integrity_probe.json').read_text()); assert p119['status']=='INTEGRITY_PROBE_PASS' and p119['holdout_market_values_not_downloaded_or_parsed']
    av=json.loads((p.PROJECT/'reports'/'candidate_v99_r106_phase118_aggtrades_availability_audit.json').read_text()); assert av['status']=='AVAILABILITY_AUDIT_COMPLETE'
    selected=sorted(av['symbols'],key=lambda s:(int(av['symbols'][s]['listed_compressed_bytes']),s))[:p.N]
    cfg,data,raw,ex,guard,gross,quarantined,metadata=p.p1.r98.r36.v15_setup(); common=[s for s in selected if s in data.close.columns]
    if len(common)<p.MIN_ASSETS: raise RuntimeError(f'operational reject: only {len(common)} executable assets')
    jobs=[(s,p.jobs_for(s,av),data.close.index) for s in common]
    workers=min(4,len(jobs),os.cpu_count() or 2)
    print('parallel_workers',workers,'symbols',common,flush=True)
    x=pd.DataFrame(index=data.close.index,columns=common,dtype=float); counts={}; archives=0
    with cf.ProcessPoolExecutor(max_workers=workers) as pool:
        futs={pool.submit(_one,j):j[0] for j in jobs}
        for fut in cf.as_completed(futs):
            s,series,count=fut.result(); x[s]=series; counts[s]=count; archives+=len(p.jobs_for(s,av)); print('built',s,'trades',count,flush=True)
    z=p.rz(x); sig=p.np.tanh(z).shift(1); sig=sig.where(sig.notna().sum(axis=1)>=p.MIN_ASSETS,0).fillna(0)
    targets=pd.DataFrame(0.,index=data.close.index,columns=data.close.columns); targets.loc[:,common]=sig.div(sig.abs().sum(axis=1).replace(0,p.np.nan),axis=0).fillna(0)
    result=p.p1.run_targets(data,targets,ex,guard,float(ex['severe_cost_per_side']),p.GROSS); d=p.p47.diag(result,data.close.index,max(data.close.index[0],pd.Timestamp('2021-12-01',tz='UTC')),p.TRAIN_END); passed=bool(d['stable_train'])
    out={'study':'V99 R106 Phase121 — CAUSAL LARGE-TRADE PRESSURE TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_DOWNSTREAM' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase121_large_trade_pressure_prereg.md','source':'official Binance USD-M aggTrades + CHECKSUM','feature':'qty > strict-prior 30d exact q90; hourly aggressive large-trade qty imbalance; cross-sectional median/MAD z; tanh; entire alpha t-1; L1','quantile':'nearest-rank exact empirical q90','direction':'continuation','selected_symbols':selected,'executable_symbols':common,'min_assets':p.MIN_ASSETS,'alpha_gross':p.GROSS,'single_hypothesis_no_grid':True,'selection_train_only':True,'holdout_not_parsed':True,'missing_archives_not_filled':True},'train_end_exclusive':p.TRAIN_END.isoformat(),'archives_consumed_per_pass':archives,'two_pass_train_only':True,'parallel_infrastructure_only':True,'train_trade_counts':counts,'diagnostic':d,'selected_train_only':'large_trade_pressure' if passed else None,'next_gate':'PASS freezes exact spec for supersevere/regime/concentration/benchmark/reproducibility before untouched holdout; FAIL permanent, no retuning.','quarantined_symbols':quarantined}
    p.OUT.write_text(json.dumps(out,indent=2,default=p.audit.safe_float)+'\n'); print(json.dumps({'status':out['status'],'symbols':common,'archives_per_pass':archives,'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train']},indent=2,default=p.audit.safe_float))

if __name__=='__main__': main()
