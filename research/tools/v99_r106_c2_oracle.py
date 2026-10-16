"""Independent C2 journal-to-raw-open accounting oracle; not a signal optimizer."""
import csv,hashlib,json,math
from pathlib import Path
from research.tools import v99_r106_c2_engine as c
def near(label,a,b):
    if not math.isfinite(a) or not math.isfinite(b) or abs(a-b)>1e-9*max(1.,abs(a),abs(b)):
        raise ValueError("C2_ORACLE_MISMATCH_"+label)
def verify(b,e,path,cost):
    indices=[i for i in range(721,len(b)-1) if b[i][0]>=c.START]
    with path.open(newline="",encoding="utf-8") as file:
        rd=csv.DictReader(file)
        if rd.fieldnames!=list(c.JOURNAL_FIELDS):raise ValueError("journal_schema")
        rows=list(rd)
    if len(rows)!=len(indices):raise ValueError("journal_coverage")
    equity=peak=1.;prior=(0.,0.);fees=0.;weights=[]
    for k,(i,row) in enumerate(zip(indices,rows)):
        if row["time"]!=b[i][0].isoformat():raise ValueError("journal_timestamp")
        w=(float(row["btc_weight"]),float(row["eth_weight"]))
        turn=float(row["turnover"]);fee=float(row["fee"]);net=float(row["net"])
        if any(not math.isfinite(x) for x in (*w,turn,fee,net)):
            raise ValueError("nonfinite_journal")
        if sum(map(abs,w))>.90+1e-9 or max(map(abs,w))>.80+1e-9:
            raise ValueError("gross_limit")
        t=sum(abs(x-y) for x,y in zip(w,prior));f=cost*t
        r=w[0]*(b[i+1][1]/b[i][1]-1)+w[1]*(e[i+1][1]/e[i][1]-1)-f
        near("turnover",turn,t);near("fee",fee,f);near("net",net,r)
        equity*=1+r;peak=max(peak,equity)
        near("equity",float(row["equity"]),equity)
        near("peak",float(row["peak"]),peak)
        if equity<=0:raise ValueError("liquidated")
        weights.append(w);prior=w;fees+=f
    return {"rows":len(rows),"roi":equity-1,"fees":fees,
            "weights_sha256":hashlib.sha256(json.dumps(weights,separators=(",",":")).encode()).hexdigest(),
            "journal_sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
def main():
    b,_=c.load_train(Path("data/canonical/BTCUSDT_1h.csv"))
    e,_=c.load_train(Path("data/canonical/ETHUSDT_1h.csv"))
    report=json.loads(Path("reports/candidate_v99_r106_c2_complete_train.json").read_text())
    out={}
    for key,cost in (("severe",c.SEVERE),("supersevere",c.SUPERSEVERE)):
        witness=verify(b,e,Path("research_evidence/v99_r106_c2_"+key+".csv"),cost)
        near("report_roi",witness["roi"],report[key]["roi"])
        near("report_fees",witness["fees"],report[key]["modeled_transaction_cost_sum"])
        if witness["journal_sha256"]!=report[key]["journal_sha256"]:
            raise ValueError("journal_hash")
        out[key]=witness
    if out["severe"]["weights_sha256"]!=out["supersevere"]["weights_sha256"]:
        raise ValueError("cost_path_divergence")
    if out["supersevere"]["roi"]>out["severe"]["roi"]+1e-10:
        raise ValueError("cost_monotonicity")
    result={"status":"INDEPENDENT_PRE_FUNDING_ACCOUNTING_VERIFIED",
            "scenarios":out,"holdout_accessed":False,"promotion_authorized":False,
            "native_fee_funding_fills_authenticated":False}
    path=Path("research_evidence/v99_r106_c2_oracle.json")
    path.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"rows":out["severe"]["rows"],
                      "severe_roi":out["severe"]["roi"],"supersevere_roi":out["supersevere"]["roi"]}))
if __name__=="__main__":main()
