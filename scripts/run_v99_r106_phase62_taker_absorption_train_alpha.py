from __future__ import annotations
import concurrent.futures,datetime as dt,json
from pathlib import Path
import numpy as np,pandas as pd
import run_v99_r106_phase61a_taker_flow_train_alpha as p61
import run_v99_r106_phase31_cross_sectional_low_vol_alpha_audit as p31
import run_v99_r106_native_all_regime_engine as p1
import run_v99_r106_phase47_downside_semivariance_alpha_audit as p47
import run_v99_r105_all_regime_structural_audit as audit
PROJECT=Path(__file__).resolve().parents[1]; OUT=PROJECT/'reports'/'candidate_v99_r106_phase62_taker_absorption_train_alpha.json'; H=24; EPS=1e-4; ALPHA_GROSS=.20

def main():
 cov=json.loads((PROJECT/'reports'/'candidate_v99_r106_phase60_taker_buy_train_coverage_audit.json').read_text());assert cov['all_train_coverage_pass']
 manifest=json.loads((PROJECT/'data'/'CANONICAL_MANIFEST_RESEARCH_PIT48.json').read_text());train_end=dt.datetime.fromisoformat(cov['train_end']);end_ms=int(train_end.timestamp()*1000);jobs=[]
 for s,meta in manifest['symbols'].items():
  first=dt.datetime.fromisoformat(meta['first']);fm=int(first.timestamp()*1000);jobs += [(s,m,fm,end_ms) for m in p61.months(first,train_end)]
 with concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool:loaded=list(pool.map(p61.load,jobs))
 by={s:[] for s in manifest['symbols']}
 for s,rs in loaded:by[s].extend(rs)
 cfg,data,raw,ex,guard,gross,quarantined,metadata=p1.r98.r36.v15_setup();idx=data.close.index;pressure=pd.DataFrame(index=idx,columns=data.close.columns,dtype=float)
 for s,rs in by.items():
  if s not in pressure.columns:continue
  ser=pd.Series({pd.to_datetime(t,unit='ms',utc=True):v for t,v in rs});ix=pressure.index.intersection(ser.index);pressure.loc[ix,s]=ser.reindex(ix).values
 flow=pressure.rolling(H,min_periods=H).mean();ret=data.close/data.close.shift(H)-1.0
 score=-(flow*np.sign(ret))*flow.abs()/(ret.abs()+EPS)
 lo=score.quantile(.05,axis=1);hi=score.quantile(.95,axis=1);score=score.clip(lower=lo,upper=hi,axis=0)
 feature=score.shift(1);targets=p31.weights(feature,data.close);severe=float(ex['severe_cost_per_side']);result=p1.run_targets(data,targets,ex,guard,severe,ALPHA_GROSS)
 start=max(data.close.index[0],min(x for x in feature.index if x<=train_end));d=p47.diag(result,data.close.index,start,train_end);passed=bool(d['stable_train'])
 out={'study':'V99 R106 phase62 — native taker-flow absorption TRAIN-ONLY alpha gate','status':'TRAIN_ALPHA_PASS_FREEZE_FOR_HOLDOUT' if passed else 'TRAIN_ALPHA_REJECT','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'precommitment':{'prereg':'research/v99_r106_phase62_taker_absorption_prereg.md','source':'Binance USD-M native taker_buy_quote_volume/quote_volume + canonical close','transform':'cross-sectional winsor05/95[-flow24*sign(ret24)*abs(flow24)/(abs(ret24)+1e-4)].shift(1)','mechanism':'passive-liquidity absorption','single_hypothesis_no_grid':True,'alpha_gross':ALPHA_GROSS,'selection_train_only':True,'holdout_not_parsed':True},'train_end':train_end.isoformat(),'diagnostic':d,'selected_train_only':'native_taker_flow_absorption_24h' if passed else None,'next_gate':'If pass, freeze exact specification and evaluate untouched holdout separately; if reject, no sign/horizon/epsilon/winsor retuning.','quarantined_symbols':quarantined,'disclosure':'Phase62 downloads/parses native taker-flow only through train_end. No holdout feature values or returns are inspected.'};OUT.write_text(json.dumps(out,indent=2,default=audit.safe_float)+'\n');print(json.dumps({'status':out['status'],'stable_train':passed,'healthy_folds':d['healthy_folds'],'valid_folds':d['valid_folds'],'train':d['train']},indent=2,default=audit.safe_float))
if __name__=='__main__':main()
