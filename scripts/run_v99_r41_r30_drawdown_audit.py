from __future__ import annotations
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from run_v99_r25_trisleeve_meta import cap
import run_v99_r37_crash_shield as r37
r37.r36.cap=cap
r36=r37.r36
REPORT=PROJECT/'reports'/'v99_r41_r30_drawdown_audit.json'

def episodes(eq,n=10):
    dd=eq/eq.cummax()-1;work=dd.copy();out=[]
    for _ in range(n):
        if len(work)==0 or float(work.min())>=0: break
        trough=work.idxmin();peak=eq.loc[:trough].idxmax();rec=eq.loc[trough:];rec=rec[rec>=eq.loc[peak]];recovery=rec.index[0] if len(rec) else eq.index[-1]
        out.append((peak,trough,recovery,float(dd.loc[trough])));work=work.drop(work.loc[peak:recovery].index,errors='ignore')
    return out

def main():
    cand,data,raw,ex,guard,gross,q,meta=r36.v15_setup();cost=float(ex['base_cost_per_side'])
    result,targets,hedge_active=r37.build_r30(data,raw,ex,guard,gross,cost);eq=result.equity.astype(float)
    pnl=(result.asset_gross-result.asset_fees-result.asset_funding).fillna(0.0)
    rows=[]
    for peak,trough,recovery,depth in episodes(eq):
        seg=pnl.loc[peak:trough];contrib=seg.sum().sort_values();pos=result.open_positions.loc[peak:trough];t=targets.loc[peak:trough];gross_series=t.abs().sum(axis=1);net=t.sum(axis=1);btc=data.close['BTCUSDT'].loc[peak:trough]
        r1=eq.pct_change(fill_method=None);r6=eq.pct_change(6,fill_method=None);r24=eq.pct_change(24,fill_method=None)
        daily=eq.loc[peak:trough].resample('1D').last().pct_change(fill_method=None).dropna()
        top=[]
        for sym,val in contrib.head(8).items():
            ps=pos[sym];ts=t[sym]
            top.append({'symbol':sym,'net_pnl_contribution':float(val),'mean_open_weight':float(ps.mean()),'mean_abs_open_weight':float(ps.abs().mean()),'max_abs_open_weight':float(ps.abs().max()),'mean_target_weight':float(ts.mean()),'max_abs_target_weight':float(ts.abs().max())})
        before_start=max(eq.index[0],peak-pd.Timedelta(hours=168));pre=t.loc[before_start:peak];pre_net=pre.sum(axis=1).abs();pre_gross=pre.abs().sum(axis=1);pre_btc=data.close['BTCUSDT'].loc[before_start:peak]
        rows.append({'peak':peak.isoformat(),'trough':trough.isoformat(),'recovery_or_end':recovery.isoformat(),'depth':depth,'hours_peak_to_trough':int((trough-peak)/pd.Timedelta(hours=1)),'hours_to_recovery_or_end':int((recovery-trough)/pd.Timedelta(hours=1)),'peak_equity':float(eq.loc[peak]),'trough_equity':float(eq.loc[trough]),'btc_return_peak_to_trough':float(btc.iloc[-1]/btc.iloc[0]-1) if len(btc)>1 else 0.0,'worst_hour':float(r1.loc[peak:trough].min()),'worst_6h':float(r6.loc[peak:trough].min()),'worst_24h':float(r24.loc[peak:trough].min()),'worst_day':float(daily.min()) if len(daily) else 0.0,'hedge_active_fraction':float(hedge_active.loc[peak:trough].mean()),'gross_mean':float(gross_series.mean()),'gross_max':float(gross_series.max()),'net_abs_mean':float(net.abs().mean()),'net_abs_max':float(net.abs().max()),'pre168_net_abs_mean':float(pre_net.mean()),'pre168_net_abs_max':float(pre_net.max()),'pre168_gross_mean':float(pre_gross.mean()),'pre168_btc_abs3_p90':float(pre_btc.pct_change(3,fill_method=None).abs().quantile(.90)),'top_loss_contributors':top})
    daily=eq.resample('1D').last().pct_change(fill_method=None).dropna();out={'study':'V99 R41 R30 drawdown episode audit','status':'DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION','r30_fixed_base':r37.R30_BASE,'r30_summary':r36.stats(eq),'episodes':rows,'worst_days':[{'date':str(d.date()),'return':float(v)} for d,v in daily.nsmallest(15).items()],'disclosure':'Diagnostic only. Uses exact causal R30 replay and modeled asset P&L attribution. No candidate is promoted from this report.','funding_quarantined_symbols':q,'v15_metadata':meta};REPORT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':main()
