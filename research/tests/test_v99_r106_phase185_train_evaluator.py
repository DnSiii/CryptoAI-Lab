import csv,importlib.util,pathlib,tempfile
P=pathlib.Path(__file__).parents[1]/'tools'/'v99_r106_phase185_train_evaluator.py';S=importlib.util.spec_from_file_location('p185',P);m=importlib.util.module_from_spec(S);S.loader.exec_module(m)

def rows(n=400):
 from datetime import datetime,timezone,timedelta
 t=datetime(2021,11,1,tzinfo=timezone.utc);b=[];e=[]
 for i in range(n):
  bc=100*(1.0002**i)*(1+0.01*((i%37)==0));ec=50*(1.00025**i)*(1+0.008*((i%37)==1));b.append((t+timedelta(hours=i),bc));e.append((t+timedelta(hours=i),ec))
 return b,e

def packed(x): return [(t,c,c,c,c,1.) for t,c in x]
def test_signal_is_t_minus_1_causal():
 b,e=rows();a=m.signal_series(packed(b),packed(e));k=220
 # Mutating close at decision bar k must not change signal stamped k; only future-known calculations may change.
 b2=list(b);b2[k]=(b2[k][0],b2[k][1]*9);z=m.signal_series(packed(b2),packed(e));ta={x[0]:x[1:3] for x in a};tz={x[0]:x[1:3] for x in z};assert ta[b[k][0]]==tz[b[k][0]]
def test_direction_matches_latest_completed_btc_shock():
 b,e=rows();s=m.signal_series(packed(b),packed(e));assert all((p==0) or (p>0)==(z>0) for _,p,z,_,_ in s)
def test_supersevere_not_better_from_cost_accounting():
 b,e=rows();sev=m.evaluate(packed(b),packed(e),m.SEVERE);sup=m.evaluate(packed(b),packed(e),m.SUPERSEVERE);assert sup['return']<=sev['return']+1e-12
def test_deterministic():
 b,e=rows();assert m.evaluate(packed(b),packed(e),m.SEVERE)==m.evaluate(packed(b),packed(e),m.SEVERE)
def test_cutoff_loader_does_not_parse_holdout_values():
 from datetime import timedelta
 with tempfile.NamedTemporaryFile('w',newline='',delete=False) as f:
  w=csv.writer(f);w.writerow(['timestamp','open','high','low','close','volume']);w.writerow([(m.CUTOFF-timedelta(hours=1)).isoformat(),1,1,1,1,1]);w.writerow([m.CUTOFF.isoformat(),'NOT_A_NUMBER',1,1,1,1]);p=f.name
 out,_=m.load_train(p);assert len(out)==1
