"""Frozen C1 complete-engine source firewall and causal decisions (TRAIN only)."""
import csv,hashlib,math
from datetime import datetime,timedelta,timezone
UTC=timezone.utc
START=datetime(2021,12,1,tzinfo=UTC)
END=datetime(2023,10,1,tzinfo=UTC)
FINAL_HOLDOUT=datetime(2024,1,18,tzinfo=UTC)
SEVERE=.0007
SUPERSEVERE=.0014
FIELDS=("timestamp","open","high","low","close","volume")

def load_train(path):
    values=[];hashing=hashlib.sha256();prior=None
    with open(path,newline="",encoding="utf-8") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames is None or any(k not in reader.fieldnames for k in FIELDS):
            raise ValueError("missing_canonical_fields")
        for row in reader:
            t=datetime.fromisoformat(row["timestamp"].replace("Z","+00:00"))
            if t.tzinfo is None or t.utcoffset()!=timedelta(0):
                raise ValueError("explicit_utc_required")
            if t>=END:break
            if prior is not None and t-prior!=timedelta(hours=1):
                raise ValueError("train_hour_gap_or_duplicate")
            o,h,l,c,v=(float(row[k]) for k in FIELDS[1:])
            if (not all(math.isfinite(x) for x in (o,h,l,c,v))
                or min(o,h,l,c)<=0 or v<0 or h<max(o,c) or l>min(o,c)):
                raise ValueError("invalid_train_ohlcv")
            values.append((t,o,h,l,c,v))
            hashing.update(("|".join(row[k] for k in FIELDS)+"\n").encode())
            prior=t
    if len(values)<1050:raise ValueError("insufficient_train")
    return values,hashing.hexdigest()

def features(rows):
    closes=[r[4] for r in rows]
    logs=[0.0]+[math.log(closes[i]/closes[i-1]) for i in range(1,len(rows))]
    sums=[0.0];ret=[0.0];sq=[0.0]
    for c,r in zip(closes,logs):
        sums.append(sums[-1]+c);ret.append(ret[-1]+r);sq.append(sq[-1]+r*r)
    out={}
    for i in range(721,len(rows)-1):
        mean=(sums[i]-sums[i-720])/720
        mom=closes[i-1]/closes[i-169]-1
        s=ret[i]-ret[i-168];s2=sq[i]-sq[i-168]
        vol=math.sqrt(max(0.,(s2-s*s/168)/167)*8760)
        out[i]=(closes[i-1],mean,mom,vol)
    return out

def signal(f):
    close,mean,mom,vol=f
    if vol<=1e-12 or not math.isfinite(vol):return 0.
    d=1 if close>mean and mom>0 else -1 if close<mean and mom<0 else 0
    return d*min(.65,.55/vol)

def regime(f):
    _,_,mom,vol=f
    d="BULL" if mom>.04 else "BEAR" if mom<-.04 else "SIDEWAYS"
    return d+"__"+("HIGH_VOLATILITY" if vol>.85 else "LOW_VOLATILITY")

def governor(weights,state,drawdown,lock):
    if lock>0:return (0.,0.),lock-1
    if drawdown<=-.20:return (0.,0.),167
    w=list(weights)
    if state=="BULL__HIGH_VOLATILITY":
        w=[x*.5 if x<0 else x for x in w]
    if state=="BEAR__HIGH_VOLATILITY":
        w=[x*.5 if x>0 else x for x in w]
    if drawdown<=-.12:w=[x*.5 for x in w]
    if sum(map(abs,w))>1.30+1e-12:raise ValueError("gross_cap")
    return tuple(w),0
