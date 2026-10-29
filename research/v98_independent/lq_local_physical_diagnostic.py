#!/usr/bin/env python3
"""V98 LQ local signed physical diagnostic; rejection-only, never promotion."""
import json,math,numpy as np
from v98_clean4_training_reader import load
from lq_sources import bundle,HOURS,WARMUP
from lq_independent_source_gate import run as gate
COSTS={'base':(.0004,.0002),'severe':(.001,.001),'supersevere':(.0015,.002)}
BOOKS={'LQ_core_only':(0,), 'LQ_full':(0,1,2,3),'LQ_minus_opportunity':(0,2,3),'LQ_minus_RV':(0,1,3),'LQ_minus_stress':(0,1,2)}

def physical(d,intents,updates,book,tier,order):
 o,h,l,c,rate,mark,event=[d[k] for k in ('o','h','l','c','rate','mark','event')]
 fee,slip=COSTS[tier];inc=BOOKS[book];qty=np.zeros((4,4));equity=10000.;prev=c[WARMUP]
 turn=fees=slippage=funding=0.;clipped=breaches=0;intramin=10000.;year_start={2023:10000.,2024:None};year_end={}
 hist=[];grosspeak=0.
 for t in range(WARMUP+1,HOURS):
  px=o[t];equity+=float(np.sum(qty*(px-prev)))
  if equity<=0 or not math.isfinite(equity):return {'passed':False,'failure':'INSOLVENT_OPEN','t':t,'book':book,'tier':tier,'order':order}
  if order=='carried_before_fill' and event[t].any():
   f=-float(np.nansum(qty.sum(axis=0)[event[t]]*mark[t,event[t]]*rate[t,event[t]]));equity+=f;funding+=f
  for k in inc:
   if not updates[t-1,k]:continue
   target=intents[t-1,k]*equity/px
   delta=target-qty[k]
   notion=float(np.sum(np.abs(delta)*px))
   cost=notion*(fee+slip)
   qty[k]=target;equity-=cost;turn+=notion;fees+=notion*fee;slippage+=notion*slip
  if order=='new_after_fill' and event[t].any():
   f=-float(np.nansum(qty.sum(axis=0)[event[t]]*mark[t,event[t]]*rate[t,event[t]]));equity+=f;funding+=f
  gross=float(np.sum(np.abs(qty)*px));grosspeak=max(grosspeak,gross/max(equity,1e-10))
  if gross>.95*equity and gross>0:
   frac=max(0.,(.93*equity)/gross);delta=qty*(1-frac)
   notion=float(np.sum(np.abs(delta)*px));qty*=frac
   equity-=notion*(fee+slip);turn+=notion;fees+=notion*fee;slippage+=notion*slip;clipped+=1
  if float(np.sum(np.abs(qty)*px))>.95*equity+1e-6:breaches+=1
  net=qty.sum(axis=0);worst=np.where(net>=0,l[t],h[t]);intramin=min(intramin,equity+float(np.dot(net,worst-px)))
  equity+=float(np.dot(net,c[t]-px));prev=c[t];hist.append(equity)
  if t==9503:year_end[2023]=equity;year_start[2024]=equity
  if equity<=0 or not math.isfinite(equity):return {'passed':False,'failure':'INSOLVENT_CLOSE','t':t,'book':book,'tier':tier,'order':order}
 year_end[2024]=equity
 curve=np.asarray(hist);peak=np.maximum.accumulate(np.r_[10000.,curve]);dd=float(np.min(np.r_[10000.,curve]/peak-1))
 daily=curve[23::24];dr=np.diff(np.r_[10000.,daily])/np.r_[10000.,daily[:-1]]
 return {'passed':not breaches and intramin>0,'book':book,'tier':tier,'order':order,'final_equity':float(equity),
  'cagr':float((equity/10000.)**.5-1),'log_growth':float(np.log(equity/10000.)),
  'year_returns':{str(y):float(year_end[y]/year_start[y]-1) for y in (2023,2024)},
  'max_dd':dd,'turnover':turn,'fees':fees,'slippage':slippage,'funding':funding,'clipped':clipped,'gross_breaches':breaches,
  'min_intrabar_equity':intramin,'max_pre_governor_gross_fraction':grosspeak,'positive_days':int((dr>0).sum()),'daily_count':len(dr),
  'daily_win_rate':float(np.mean(dr>0)),'cvar_1pct':float(np.mean(np.sort(dr)[:max(1,len(dr)//100)])),
  'trade_pf_payoff_win_rate_independent':False}

def run(root,tiers=('base','severe'),orders=('carried_before_fill',)):
 g=gate(root);assert g['decision']=='PASS_SOURCE_ONLY'
 d=load(root);intent,updates,*_=bundle(*(d[k] for k in ('o','h','l','c','q','rate','event')))
 cells=[]
 for tier in tiers:
  for order in orders:
   for book in BOOKS:
    x=physical(d,intent,updates,book,tier,order);cells.append(x)
    print('LQ_LOCAL',tier,order,book,'CAGR',round(x.get('cagr',-1)*100,3),'TURN',round(x.get('turnover',-1)),flush=True)
 marg={}
 for tier in tiers:
  for order in orders:
   k=tier+'/'+order;group={z['book']:z for z in cells if z['tier']==tier and z['order']==order}
   f=group['LQ_full'];marg[k]={s:float(f['log_growth']-group[b]['log_growth']) for s,b in [('Opportunity','LQ_minus_opportunity'),('Relative_Value','LQ_minus_RV'),('Stress_Recovery','LQ_minus_stress')]}
 return {'architecture':'LQ','source_gate':g,'cells':cells,'marginals':marg,'training_only':True,'local_diagnostic_only':True,'eligible_for_promotion':False,'independent_settlement_oracle':False,'original_30cell_workflow':False,'holdout_accessed':False}
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--output',required=True)
 p.add_argument('--tiers',nargs='+',default=['base','severe'],choices=tuple(COSTS));p.add_argument('--orders',nargs='+',default=['carried_before_fill'],choices=('carried_before_fill','new_after_fill'))
 a=p.parse_args();r=run(a.root,a.tiers,a.orders);open(a.output,'w').write(json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+'\n')
 print('MARGINALS',json.dumps(r['marginals'],indent=2))
