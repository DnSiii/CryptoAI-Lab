"""V98 Phase243 isolation and decision-status adversarial regression tests."""
import tempfile
import unittest
from pathlib import Path
from phase243_evidence_inventory import inventory, classify


class InventoryIsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root/'reports').mkdir()
        (self.root/'research'/'v98_independent').mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, rel, content):
        p = self.root/rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return p

    def test_v99_decision_never_read(self):
        self.put('reports/v99_phase200_decision.md', 'Status: PROMOTED\n')
        self.put('reports/v98_independent_phase200_decision.md', 'Status: REJECT_FAMILY_NO_RESCUE\n')
        rows = inventory(self.root)['phases']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['status'], 'rejected')
        self.assertTrue(all('v99' not in p for p in rows[0]['files']))

    def test_code_and_prereg_are_not_evidence(self):
        self.put('research/v98_independent/phase243_evidence_inventory.py', 'REJECTED_NO_RESCUE')
        self.put('research/v98_independent/phase243_prereg.md', 'Status: PROMOTED')
        self.assertEqual(inventory(self.root)['phase_count'], 0)

    def test_no_champion_and_narrative_promoted_do_not_promote(self):
        self.put('reports/v98_independent_phase221_decision.md',
                 'Status: NO_CHAMPION\nThis mentions PROMOTED as a hypothetical.\n')
        self.assertEqual(inventory(self.root)['phases'][0]['status'], 'unknown')

    def test_json_explicit_status_only(self):
        self.put('reports/v98_independent_phase200_results.json',
                 '{"decision":"REJECT_FAMILY_NO_RESCUE"}')
        self.put('reports/v98_independent_phase201_results.json',
                 '{"specs":{"note":"PROMOTED"}}')
        r = {x['phase']:x['status'] for x in inventory(self.root)['phases']}
        self.assertEqual(r, {200:'rejected',201:'unknown'})

    def test_conflicting_status_is_unresolved(self):
        self.put('reports/v98_independent_phase100_decision.md', 'Status: PROMOTED')
        self.put('reports/v98_independent_phase100_audit.md', 'Status: REJECTED')
        self.assertEqual(inventory(self.root)['phases'][0]['status'], 'unknown')

    def test_symlink_to_external_report_skipped(self):
        target = self.put('reports/v99_phase150_decision.md', 'Status: PROMOTED')
        alias = self.root/'reports'/'v98_independent_phase150_decision.md'
        alias.symlink_to(target)
        self.assertEqual(inventory(self.root)['phase_count'], 0)

    def test_unsupported_word_does_not_count(self):
        self.assertEqual(classify('Status: NO_CHAMPION'), 'unknown')
        self.assertEqual(classify('We could PROMOTE someday.'), 'unknown')
        self.assertEqual(classify('{"status":"PASS_TRAINING"}',suffix='.json'), 'training_pass')

if __name__ == '__main__':
    unittest.main()
