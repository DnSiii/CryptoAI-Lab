"""Guard against funding-edge checks being accidentally commented out in the reader.

Regression: escaped literal \\n in a comment previously swallowed the call.
This test checks the executable AST, not the helper in isolation.
"""
import ast
import inspect
import unittest
from research.v98_independent import v98_phase243_training_reader as reader


class FundingEdgeWiring(unittest.TestCase):
    def test_load_executes_funding_edge_guard(self):
        tree = ast.parse(inspect.getsource(reader.load))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name)
                 and node.func.id == "validate_funding_edges"]
        self.assertEqual(len(calls), 1, "load() must invoke the edge guard exactly once per asset")
        self.assertEqual([arg.id for arg in calls[0].args if isinstance(arg, ast.Name)],
                         ["events", "asset"])

    def test_edge_guard_rejects_truncated_boundaries(self):
        hour = reader.HOUR_MS
        for events in (
            {reader.START_MS + 9 * hour: 0.0001, reader.END_MS - 8 * hour: 0.0001},
            {reader.START_MS + 8 * hour: 0.0001, reader.END_MS - 9 * hour: 0.0001},
        ):
            with self.assertRaisesRegex(ValueError, "EDGE_COVERAGE"):
                reader.validate_funding_edges(events, "BTCUSDT")


if __name__ == "__main__":
    unittest.main()
