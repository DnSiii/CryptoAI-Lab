import csv,tempfile,hashlib
from pathlib import Path
from research.tools.v99_r106_phase182_feature_builder import build

F=['timestamp','open','high','low','close','volume']
def make(n=60,mutate=None):
 p=Path(tempfile.mkstemp(suffix='.csv')[1])
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=F);w.writeheader()
  for i in range(n):
   c=100+i*.1; v=10+i%7
   if mutate and i==mutate[0]: c,v=mutate[1],mutate[2]
   w.writerow({'timestamp':f'2023-01-{1+i//24:02d}T{i%24:02d}:00:00Z','open':c,'high':c+1,'low':c-1,'close':c,'volume':v})
 return p
def out(): return Path(tempfile.mkstemp(suffix='.csv')[1])
def lines(p): return list(csv.DictReader(open(p)))

def test_deterministic_byte_identical():
 b,e=make(),make();a,z=out(),out();m1=build(b,e,a);m2=build(b,e,z)
 assert a.read_bytes()==z.read_bytes() and m1['feature_sha256']==m2['feature_sha256']

def test_future_mutation_cannot_change_prior_features():
 b,e=make(),make(); a=out(); build(b,e,a); base=lines(a)
 # mutate source bar 50: rows with decision timestamp <= bar 50 must not use bar 50 (t-1 discipline)
 e2=make(mutate=(50,999,999)); z=out(); build(b,e2,z); alt=lines(z)
 for x,y in zip(base,alt):
  if x['timestamp']<= '2023-01-03T02:00:00Z': assert x==y

def test_current_bar_mutation_does_not_change_its_decision_row():
 b,e=make(),make();a=out();build(b,e,a);base=lines(a)
 e2=make(mutate=(40,777,777));z=out();build(b,e2,z);alt=lines(z)
 target='2023-01-02T16:00:00Z'
 assert next(x for x in base if x['timestamp']==target)==next(x for x in alt if x['timestamp']==target)

def test_warmup_is_not_imputed():
 b,e=make(),make();a=out();m=build(b,e,a)
 assert m['rows']==60-25 and lines(a)[0]['timestamp']=='2023-01-02T01:00:00Z'
