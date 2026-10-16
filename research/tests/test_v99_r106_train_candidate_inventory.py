import json,tempfile,unittest
from pathlib import Path
from research.tools import v99_r106_train_candidate_inventory as s
class Tests(unittest.TestCase):
 def test_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   (Path(d)/"candidate_v99_r106_phase182_train_alpha.json").write_text(json.dumps({"status":"TRAIN_ALPHA_REJECT"}))
   x=s.scan(Path(d));self.assertEqual(x["count"],1);self.assertEqual(x["not_rejected_not_promoted"],[]);self.assertFalse(x["promotion_authorized"])
 def test_nonrejected_is_not_promoted(self):
  with tempfile.TemporaryDirectory() as d:
   (Path(d)/"candidate_v99_r106_phase10_test_train_alpha.json").write_text(json.dumps({"status":"TRAIN_ALPHA_PASS"}))
   x=s.scan(Path(d));self.assertEqual(len(x["not_rejected_not_promoted"]),1);self.assertFalse(x["promotion_authorized"])
 def test_holdout_flag_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   (Path(d)/"candidate_v99_r106_phase10_test_train_alpha.json").write_text(json.dumps({"status":"REJECT","holdout_rows_used_for_selection":True}))
   with self.assertRaisesRegex(ValueError,"contaminated"):s.scan(Path(d))
 def test_empty(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(ValueError,"no_train_records"):s.scan(Path(d))
