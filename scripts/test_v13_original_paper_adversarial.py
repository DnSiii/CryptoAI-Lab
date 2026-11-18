"""Adversarial checks against the unmodified original-paper verifier, in disposable copies."""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

research = Path(sys.argv[1]).resolve()
published = Path(sys.argv[2]).resolve()
with tempfile.TemporaryDirectory(prefix="v13-adversarial-") as root:
    base = Path(root)
    for rel in ("scripts/verify_paper_cycle_v13.py",):
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(research / rel, target)
    for rel in ("config/candidate_v13_circuit_breaker.json", "state/paper_v13_state.json",
                "reports/paper_v13_snapshot.json", "reports/paper_v13_ledger.json",
                "reports/paper_data_sync_v13.json"):
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(published / rel, target)
    ledger_path = base / "reports/paper_v13_ledger.json"
    original = json.loads(ledger_path.read_text())
    def run(expected_success):
        result = subprocess.run([sys.executable, str(base / "scripts/verify_paper_cycle_v13.py")],
                                capture_output=True, text=True)
        if (result.returncode == 0) != expected_success:
            raise AssertionError(f"expected success={expected_success}, rc={result.returncode}: {result.stderr[-1000:]}")
    run(True)
    decisions = original["decisions"]
    index = next(i for i, d in enumerate(decisions) if d.get("adjustments"))
    def case(name, mutate, accepted):
        data = copy.deepcopy(original)
        adj = data["decisions"][index]["adjustments"][0]
        mutate(adj)
        ledger_path.write_text(json.dumps(data))
        run(accepted)
        print(f"{name}: {'accepted' if accepted else 'rejected'}")
    case("zero without raw", lambda a: a.update(order_value_brl=0, order_value_brl_unrounded=None), False)
    case("zero with negative raw", lambda a: a.update(order_value_brl=0, order_value_brl_unrounded=-0.001), False)
    case("zero with threshold raw", lambda a: a.update(order_value_brl=0, order_value_brl_unrounded=0.005), False)
    case("zero with nan raw", lambda a: a.update(order_value_brl=0, order_value_brl_unrounded="NaN"), False)
    case("zero with infinity raw", lambda a: a.update(order_value_brl=0, order_value_brl_unrounded="Infinity"), False)
    case("nan display", lambda a: a.update(order_value_brl="NaN"), False)
    case("negative display", lambda a: a.update(order_value_brl=-1), False)
    case("valid subcent", lambda a: a.update(order_value_brl=0, order_value_brl_unrounded=0.001), True)
    ledger_path.write_text(json.dumps(original))
    run(True)
    print("adversarial checks complete; original ledger restored in disposable directory")
