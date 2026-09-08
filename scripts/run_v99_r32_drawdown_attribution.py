from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'src'));sys.path.insert(0,str(PROJECT/'scripts'))
from paper_once_v15 import build_v15

REPORT=PROJECT/'reports'/'v99_r32_drawdown_attribution.json'

def episode_rows(result,data,top_n=10):
    eq=result.equity.astype(float)
    peak=eq.cummax();dd=eq/peak-1
    troughs=[]
    work=dd.copy()
    for _ in range(8):
        if len(work)==0 or work.min()>=0: break
        trough=work.idxmin();pidx=eq.loc[:trough].idxmax();after=eq.loc[trough:];recovery=after[after>=eq.loc[pidx]]
        ridx=recovery.index[0] if len(recovery) else eq.index[-1]
        troughs.append((pidx,trough,ridx,float(dd.loc[trough])))
        work=work.drop(work.loc[pidx:ridx].index,errors='ignore')
    pnl=(result.asset_gross-result.asset_fees-result.asset_funding).fillna(0.0)
    out=[]
    for pidx,trough,ridx,depth in troughs:
        seg=pnl.loc[pidx:trough]
        contrib=seg.sum().sort_values()
        openpos=result.open_positions.loc[pidx:trough]
        gross=result.gross_exposure.loc[pidx:trough]
        net=openpos.sum(axis=1)
        btc=data.close['BTCUSDT'].loc[pidx:trough]
        btc_ret=float(btc.iloc[-1]/btc.iloc[0]-1) if len(btc)>1 else 0.0
        losses=[]
        for sym,val in contrib.head(top_n).items():
            pos=openpos[sym]
            long_frac=float((pos>1e-12).mean());short_frac=float((pos<-1e-12).mean())
            losses.append({'symbol':sym,'net_pnl_contribution':float(val),'long_fraction':long_frac,'short_fraction':short_frac,'mean_abs_weight':float(pos.abs().mean()),'max_abs_weight':float(pos.abs().max())})
        gains=[]
        for sym,val in contrib.tail(min(top_n,len(contrib))).sort_values(ascending=False).items():
            gains.append({'symbol':sym,'net_pnl_contribution':float(val),'mean_abs_weight':float(openpos[sym].abs().mean())})
        out.append({'peak':str(pidx),'trough':str(trough),'recovery_or_end':str(ridx),'drawdown':depth,'hours_peak_to_trough':int((trough-pidx)/pd.Timedelta(hours=1)),'equity_peak':float(eq.loc[pidx]),'equity_trough':float(eq.loc[trough]),'gross_mean':float(gross.mean()),'gross_max':float(gross.max()),'net_exposure_mean':float(net.mean()),'net_exposure_min':float(net.min()),'net_exposure_max':float(net.max()),'btc_return_peak_to_trough':btc_ret,'turnover_sum':float(result.turnover.loc[pidx:trough].sum()),'fees_sum':float(result.fees.loc[pidx:trough].sum()),'funding_sum':float(result.funding.loc[pidx:trough].sum()),'top_loss_contributors':losses,'top_gain_contributors':gains})
    return out

def worst_days(result,data,n=15):
    eq=result.equity.astype(float);daily=eq.resample('1D').last();dr=daily.pct_change(fill_method=None).dropna();pnl=(result.asset_gross-result.asset_fees-result.asset_funding).fillna(0.0)
    out=[]
    for day,ret in dr.nsmallest(n).items():
        start=day;end=day+pd.Timedelta(days=1)-pd.Timedelta(nanoseconds=1);seg=pnl.loc[start:end];c=seg.sum().sort_values();pos=result.open_positions.loc[start:end];btc=data.close['BTCUSDT'].loc[start:end]
        out.append({'date':str(day.date()),'return':float(ret),'btc_return':float(btc.iloc[-1]/btc.iloc[0]-1) if len(btc)>1 else 0.0,'gross_mean':float(result.gross_exposure.loc[start:end].mean()),'net_exposure_mean':float(pos.sum(axis=1).mean()),'turnover':float(result.turnover.loc[start:end].sum()),'fees':float(result.fees.loc[start:end].sum()),'funding':float(result.funding.loc[start:end].sum()),'top_loss_contributors':[{'symbol':s,'net_pnl_contribution':float(v),'side_mean_weight':float(pos[s].mean())} for s,v in c.head(8).items()]})
    return out

def concentration(result):
    pos=result.open_positions.abs();gross=pos.sum(axis=1).replace(0,np.nan);share=pos.div(gross,axis=0).fillna(0);top1=share.max(axis=1);top3=np.sort(share.to_numpy(),axis=1)[:,-3:].sum(axis=1) if share.shape[1]>=3 else share.sum(axis=1).to_numpy();eq=result.equity;dd=eq/eq.cummax()-1;stress=dd<=-.10
    return {'overall':{'top1_mean':float(top1.mean()),'top1_p95':float(top1.quantile(.95)),'top3_mean':float(pd.Series(top3,index=share.index).mean())},'dd_below_10pct':{'hours':int(stress.sum()),'top1_mean':float(top1.loc[stress].mean()) if stress.any() else 0.0,'top3_mean':float(pd.Series(top3,index=share.index).loc[stress].mean()) if stress.any() else 0.0,'gross_mean':float(result.gross_exposure.loc[stress].mean()) if stress.any() else 0.0,'net_exposure_mean':float(result.open_positions.sum(axis=1).loc[stress].mean()) if stress.any() else 0.0}}

def main():
    cand,data,targets,result,regime,q,meta=build_v15();eq=result.equity.astype(float);dd=eq/eq.cummax()-1;daily=eq.resample('1D').last().pct_change(fill_method=None).dropna()
    out={'study':'V99 R32 V15 drawdown attribution','status':'DIAGNOSTIC_ONLY_NO_CANDIDATE_PROMOTION','v15_summary':{'return':float(eq.iloc[-1]/eq.iloc[0]-1),'max_drawdown':float(dd.min()),'worst_day':float(daily.min()),'best_day':float(daily.max()),'positive_days':float((daily>0).mean())},'drawdown_episodes':episode_rows(result,data),'worst_days':worst_days(result,data),'concentration':concentration(result),'quarantined_symbols':q,'metadata':meta,'disclosure':'Diagnostic attribution from the same causal exact V15 replay. Asset contribution is modeled gross PnL minus modeled fee and funding components; use it to design prospective causal rules, not to edit historical losses after the fact.'}
    REPORT.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':main()
