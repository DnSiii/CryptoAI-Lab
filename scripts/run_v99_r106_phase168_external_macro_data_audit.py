from __future__ import annotations
import csv, io, json, math, urllib.request
from pathlib import Path
from datetime import date, timedelta

START=date(2021,12,1); END=date(2024,1,18)  # exclusive
SERIES=['DFF','DGS2','DGS10','DTWEXBGS','VIXCLS']
OUT=Path('reports/candidate_v99_r106_phase168_external_macro_data_audit.json')

def business_days(a,b):
    out=[]; d=a
    while d<b:
        if d.weekday()<5: out.append(d)
        d+=timedelta(days=1)
    return out

def fetch_series(s):
    url=f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}&cosd={START.isoformat()}&coed={(END-timedelta(days=1)).isoformat()}'
    with urllib.request.urlopen(url, timeout=45) as r: text=r.read().decode('utf-8')
    rows=[]
    for x in csv.DictReader(io.StringIO(text)):
        ds=x.get('DATE') or x.get('observation_date'); vs=x.get(s)
        if not ds: continue
        d=date.fromisoformat(ds)
        if not (START<=d<END): continue
        try: v=float(vs)
        except (TypeError,ValueError): v=float('nan')
        rows.append((d,v))
    return rows

def longest_missing_run(expected, finite_dates):
    best=cur=0
    for d in expected:
        if d in finite_dates: cur=0
        else: cur+=1; best=max(best,cur)
    return best

def main():
    exp=business_days(START,END); assets={}; overall=True
    for s in SERIES:
        try:
            rows=fetch_series(s); dates=[d for d,_ in rows]
            finite={d for d,v in rows if math.isfinite(v)}
            coverage=len(set(exp)&finite)/len(exp)
            dup=len(dates)-len(set(dates)); increasing=all(a<b for a,b in zip(dates,dates[1:]))
            outside=sum(not (START<=d<END) for d in dates); missrun=longest_missing_run(exp,finite)
            ok=coverage>=0.90 and dup==0 and increasing and outside==0 and missrun<=10
            assets[s]={'rows':len(rows),'finite_business_days':len(set(exp)&finite),'expected_business_days':len(exp),'coverage_business_day':coverage,'duplicate_dates':dup,'strictly_increasing':increasing,'rows_outside_train':outside,'longest_missing_business_day_run':missrun,'pass':ok}
        except Exception as e:
            ok=False; assets[s]={'error':type(e).__name__+': '+str(e),'pass':False}
        overall &= ok
    report={'study':'V99 R106 Phase168 external macro DATA-only audit','status':'PASS_DATA_ONLY' if overall else 'FAIL_DATA_ONLY','train_start':START.isoformat(),'train_end_exclusive':END.isoformat(),'frozen_series':SERIES,'assets':assets,'pnl_computed':False,'holdout_rows_used_for_feature_construction':0,'holdout_rows_used_for_selection':0,'frozen_assets_untouched':{'v16':True,'v99_frozen':True},'decision':'DATA gate passed; alpha still forbidden until separately preregistered.' if overall else 'Reject this frozen macro panel before alpha; no gate rescue.'}
    OUT.parent.mkdir(exist_ok=True); OUT.write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
