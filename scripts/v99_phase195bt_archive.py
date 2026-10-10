import hashlib,json,zipfile
from pathlib import Path
from scripts.v99_phase195bt_core import audit
TRACKS=('v13','core_comparison_v1','opportunity_v1','combined_v1','v14','v15','v16','v99')
def inspect(path):
    out={}
    with zipfile.ZipFile(path) as z:
        for track in TRACKS:
            p='paper_'+track+'_ledger.json'
            old=json.loads(z.read('reports/published_baseline/'+p))
            new=json.loads(z.read('reports/'+p))
            a={r['timestamp']:r for r in old['equity_curve']}
            b={r['timestamp']:r for r in new['equity_curve']}
            changed=sorted(k for k in a.keys()&b.keys() if a[k]!=b[k])
            out[track]={'errors':len(audit(old))+len(audit(new)),
                'rewrites':len(changed),'first':changed[0] if changed else None}
    return {'status':'DATA_ONLY_HOLD','source_authenticated':False,'promotion_authorized':False,
        'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'tracks':out}
