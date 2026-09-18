from __future__ import annotations
import json
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]; REPORT=PROJECT/'reports'/'candidate_v99_r106_phase54_alpha_frontier_failure_map.json'

def main():
    rows=[]; missing=[]
    for phase in range(24,54):
        hits=sorted((PROJECT/'reports').glob(f'candidate_v99_r106_phase{phase}_*.json'))
        if not hits: missing.append(phase); continue
        for path in hits:
            try: r=json.loads(path.read_text())
            except Exception: continue
            sleeves=r.get('sleeves',{})
            for name,d in sleeves.items():
                tr=d.get('train',{}); rows.append({'phase':phase,'report':path.name,'family':name,'stable_train':bool(d.get('stable_train',False)),'healthy_folds':int(d.get('healthy_folds',0)),'valid_folds':int(d.get('valid_folds',0)),'roi':float(tr.get('roi',0)),'profit_factor':float(tr.get('profit_factor',0)),'max_drawdown_abs':float(tr.get('max_drawdown_abs',0)),'robust_mean_without_top1pct':float(tr.get('robust_mean_without_top1pct',0))})
    # Train-only synthesis. No holdout fields are read or ranked.
    positive=[x for x in rows if x['roi']>0]; robust=[x for x in rows if x['robust_mean_without_top1pct']>0]; fold3=[x for x in rows if x['healthy_folds']>=3]
    near=sorted(rows,key=lambda x:(x['healthy_folds'],x['robust_mean_without_top1pct'],x['profit_factor'],x['roi']),reverse=True)[:15]
    out={'study':'V99 R106 phase 54 — train-only alpha frontier failure map','status':'DIAGNOSTIC_ONLY_NO_STRATEGY_CHANGE','frozen_assets_untouched':{'v16':True,'v99_frozen':True},'discipline':{'reads_holdout_metrics':False,'selection_or_strategy_change':False,'purpose':'map repeated train-only failure modes before spending further hypothesis budget; no thresholds are changed'},'coverage':{'phases_requested':[24,53],'reports_missing':missing,'families_examined':len(rows),'positive_train_roi_count':len(positive),'positive_robust_mean_count':len(robust),'three_healthy_fold_count':len(fold3),'stable_train_count':sum(x['stable_train'] for x in rows)},'failure_counts':{'roi_nonpositive':sum(x['roi']<=0 for x in rows),'profit_factor_le_1_08':sum(x['profit_factor']<=1.08 for x in rows),'robust_mean_nonpositive':sum(x['robust_mean_without_top1pct']<=0 for x in rows),'healthy_folds_lt_3':sum(x['healthy_folds']<3 for x in rows)},'train_only_near_frontier':near,'policy':'Use this map only to choose a genuinely distinct mechanism or lower-turnover structural formulation. Do not tune horizons, thresholds, direction, or gates to rescue a listed family. Untouched holdout remains unavailable for selection.','disclosure':'Historical research only. No real orders. Phase54 cannot alter V99 Frozen or V16 Frozen.'}; REPORT.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
