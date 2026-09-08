from __future__ import annotations

import itertools,json,sys
from pathlib import Path
import numpy as np
import pandas as pd
PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/"src"));sys.path.insert(0,str(PROJECT/"scripts"))
from cryptoai_v13.backtest import exact_fast
from cryptoai_v13.data import FuturesData
from paper_once_v15 import build_v15
REPORT=PROJECT/"reports"/"candidate_v99_r23_vol_trend.json"; H=(7,30,90,180,365)

def stats(e):
 e=e.dropna().astype(float)
 if len(e)<2:return {"return":0.,"max_drawdown":0.,"best_day":0.,"worst_day":0.,"positive_days":0.}
 n=e/e.iloc[0];dd=n/n.cummax()-1;d=n.resample("1D").last().pct_change(fill_method=None).dropna()
 return {"return":float(n.iloc[-1]-1),"max_drawdown":float(dd.min()),"best_day":float(d.max()) if len(d) else 0.,"worst_day":float(d.min()) if len(d) else 0.,"positive_days":float((d>0).mean()) if len(d) else 0.}
def sdata(data,start,end):return FuturesData(frames={k:v.loc[start:end].copy() for k,v in data.frames.items()},funding=data.funding.loc[start:end].copy(),symbols=data.symbols)
def cap(t,c):
 g=t.abs().sum(axis=1);f=(c/g.replace(0,np.nan)).clip(upper=1).fillna(1);return t.mul(f,axis=0)
def run(data,t,ex,cost,gross,guard=None):
 kw={}
 if guard:kw={"drawdown_guard_threshold":guard["drawdown_threshold"],"drawdown_guard_multiplier":guard["exposure_multiplier"],"drawdown_guard_cooldown_hours":guard["cooldown_hours"]}
 return exact_fast(data,t,cost_per_side=cost,maintenance_equity_fraction=ex["maintenance_equity_fraction"],gross_guard_cap=gross,**kw)
def guard_factor(eq,g):
 a=np.ones(len(eq));peak=1.;active=False;until=-1;v=eq.to_numpy(float)
 for i,x in enumerate(v):
  if active and i>=until:active=False;peak=x
  dd=x/peak-1 if peak else -1
  if not active and dd<=-abs(g["drawdown_threshold"]):active=True;until=i+g["cooldown_hours"]
  a[i]=g["exposure_multiplier"] if active else 1.;peak=max(peak,x)
 return pd.Series(a,index=eq.index)
def smooth_scale(eq,boost,min_scale,max_scale,trend_boost,shock_scale):
 r=eq.pct_change(fill_method=None);rv=r.rolling(720,min_periods=168).std()*np.sqrt(24*365)
 baseline=rv.expanding(min_periods=720).median();vs=(baseline*boost/rv.replace(0,np.nan)).clip(lower=min_scale,upper=max_scale).fillna(1.)
 r7=eq/eq.shift(168)-1;r30=eq/eq.shift(720)-1;r90=eq/eq.shift(2160)-1;dd=eq/eq.cummax()-1
 trend=((r30>0.04)&(r90>0.08)&(r7>0)).fillna(False);shock=((dd<-0.07)|(r7<-0.05)|((r30<0)&(r7<0))).fillna(False)
 shock=shock.astype(float).rolling(72,min_periods=1).max().gt(0)
 s=vs.copy();s.loc[trend&~shock]=(s.loc[trend&~shock]*trend_boost).clip(upper=max_scale);s.loc[shock]=np.minimum(s.loc[shock],shock_scale)
 return s
def build(raw,shadow,g,p):return cap(raw.mul(guard_factor(shadow,g)*smooth_scale(shadow,p["boost"],p["min_scale"],p["max_scale"],p["trend_boost"],p["shock_scale"]),axis=0),p["gross_cap"])
def slice_eval(data,raw,ex,g,bg,cost,p,start,end):
 d=sdata(data,start,end);r=raw.reindex(index=d.close.index,columns=d.close.columns).fillna(0);sh=run(d,r,ex,cost,bg,g).equity;t=build(r,sh,g,p);return stats(run(d,t,ex,cost,p["gross_cap"],None).equity),stats(sh)
def main():
 cand,data,raw,_,_,q,meta=build_v15();v14=json.loads((PROJECT/"config"/cand["parent_candidate_config"]).read_text());fin=json.loads((PROJECT/"config"/v14["frozen_core_config"]).read_text());base=json.loads((PROJECT/"config"/fin["base_candidate_config"]).read_text());ex=base["execution"];g=v14["circuit_breaker"];bg=float(v14["allocation"]["gross_drift_guard_cap"]);bc=float(ex["base_cost_per_side"]);sc=float(ex["severe_cost_per_side"])
 shadow=run(data,raw,ex,bc,bg,g).equity;v15=stats(shadow);v15sev=stats(run(data,raw,ex,sc,bg,g).equity);split=int(len(shadow)*.6);te=shadow.index[split];hs=shadow.index[min(split+1,len(shadow)-1)]
 rows=[];cache={}
 for boost,min_s,max_s,tb,shock,gross in itertools.product((.90,1.00,1.10),(.35,.50), (1.25,1.40,1.55),(1.00,1.10,1.20),(.25,.40,.55),(1.9,2.2,2.5)):
  if max_s<=min_s:continue
  p={"boost":boost,"min_scale":min_s,"max_scale":max_s,"trend_boost":tb,"shock_scale":shock,"gross_cap":gross};t=build(raw,shadow,g,p);eq=run(data,t,ex,bc,gross,None).equity;s=stats(eq);tr=stats(eq.loc[:te]);ho=stats(eq.loc[hs:]);trv=stats(shadow.loc[:te]);hov=stats(shadow.loc[hs:]);wr=(1+s["return"])/(1+v15["return"]);hr=(1+ho["return"])/(1+hov["return"]);dr=abs(s["max_drawdown"])/abs(v15["max_drawdown"]);hdr=abs(ho["max_drawdown"])/max(1e-12,abs(hov["max_drawdown"]));worst=abs(s["worst_day"])/abs(v15["worst_day"]);score=4*np.log(max(wr,1e-12))+3*np.log(max(hr,1e-12))+2*max(0,1-dr)-4*max(0,dr-1)-2*max(0,worst-1)
  key=f"b{boost:.2f}_n{min_s:.2f}_x{max_s:.2f}_t{tb:.2f}_s{shock:.2f}_g{gross:.1f}";rows.append({"key":key,"params":p,"summary":s,"wealth_ratio_to_v15":float(wr),"holdout_wealth_ratio":float(hr),"drawdown_ratio_to_v15":float(dr),"holdout_drawdown_ratio":float(hdr),"worst_day_ratio_to_v15":float(worst),"score":float(score)});cache[key]=t
 rank=sorted(rows,key=lambda z:z["score"],reverse=True);final=[];end=data.close.index[-1]
 for row in rank[:10]:
  p=row["params"];iso={};iv={};wins={};ddw={}
  for d in H:
   a,b=slice_eval(data,raw,ex,g,bg,bc,p,end-pd.Timedelta(days=d),end);iso[str(d)]=a;iv[str(d)]=b;wins[str(d)]=a["return"]>=b["return"];ddw[str(d)]=abs(a["max_drawdown"])<=abs(b["max_drawdown"])
  sev=stats(run(data,cache[row["key"]],ex,sc,p["gross_cap"],None).equity);sr=(1+sev["return"])/(1+v15sev["return"]);gate=bool(all(wins.values()) and row["wealth_ratio_to_v15"]>=1.25 and row["drawdown_ratio_to_v15"]<=.80 and row["worst_day_ratio_to_v15"]<=.85 and row["holdout_wealth_ratio"]>=1.15 and row["holdout_drawdown_ratio"]<=.85 and sr>=1.15);final.append({**row,"isolated":iso,"isolated_v15":iv,"isolated_return_wins_vs_v15":wins,"isolated_drawdown_wins_vs_v15":ddw,"severe_cost":sev,"severe_wealth_ratio_to_v15":float(sr),"superior_gate_passed":gate})
 final.sort(key=lambda z:(z["superior_gate_passed"],sum(z["isolated_return_wins_vs_v15"].values()),z["holdout_wealth_ratio"],z["wealth_ratio_to_v15"],-z["drawdown_ratio_to_v15"]),reverse=True);sel=final[0] if final else None
 out={"study":"V99 R23 smooth volatility/trend risk budget","status":"RESEARCH_ONLY_DO_NOT_REWRITE_FROZEN_V99_PAPER","objective":"materially increase V15 compounding through causal volatility budgeting while de-risking shocks","disclosure":"Historical research; parameters are not forward proof. Any winner must be frozen before a fresh independent paper boundary.","grid_size":len(rows),"v15":{"summary":v15,"severe_cost":v15sev},"selected":sel,"finalists":final,"top_screen":rank[:30],"funding_quarantined_symbols":q,"v15_metadata":meta};REPORT.write_text(json.dumps(out,indent=2)+"\n");print(json.dumps({"study":out["study"],"grid_size":len(rows),"v15":out["v15"],"selected":sel},indent=2),flush=True)
if __name__=="__main__":main()
