import csv,importlib.util
from pathlib import Path
P=Path(__file__).parents[1]/'tools'/'v99_r106_phase182_train_evaluator.py'; s=importlib.util.spec_from_file_location('p182e',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def write(p,n=200,shock=0):
 with open(p,'w',newline='') as f:
  w=csv.writer(f);w.writerow(['timestamp','open','high','low','close','volume'])
  from datetime import datetime,timezone,timedelta
  t=datetime(2021,11,20,tzinfo=timezone.utc); px=100.
  for i in range(n):
   px*=1+(0.0002*((i%7)-3)+shock);w.writerow([(t+timedelta(hours=i)).isoformat(),px,px*1.01,px*.99,px,100+i%11])
def test_deterministic_and_firewall(tmp_path):
 b=tmp_path/'b.csv';e=tmp_path/'e.csv';write(b,800,0);write(e,800,0.00001); rb,_=m.load_train(b);re,_=m.load_train(e);a=m.eval_pair(rb,re,m.SEVERE);c=m.eval_pair(rb,re,m.SEVERE);assert a==c
 # append a holdout row with deliberately non-numeric OHLCV: loader must stop before parsing it
 with open(b,'a') as f:f.write('2024-01-18T00:00:00+00:00,SECRET,SECRET,SECRET,SECRET,SECRET\n')
 rb2,_=m.load_train(b);assert len(rb2)==len(rb)
def test_supersevere_is_stricter(tmp_path):
 b=tmp_path/'b.csv';e=tmp_path/'e.csv';write(b,900,0);write(e,900,0.00002);rb,_=m.load_train(b);re,_=m.load_train(e);a=m.eval_pair(rb,re,m.SEVERE);z=m.eval_pair(rb,re,m.SUPERSEVERE);assert z['return']<=a['return']+1e-12;assert m.SUPERSEVERE==2*m.SEVERE
