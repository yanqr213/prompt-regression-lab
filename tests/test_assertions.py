import unittest

from prompt_regression_lab.assertions import evaluate_assertion
from prompt_regression_lab.errors import AssertionExecutionError


class AssertionTests(unittest.TestCase):
    def test_contains_pass(self):
        result = evaluate_assertion({"type": "contains", "value": "world"}, "hello world")
        self.assertTrue(result.passed)

    def test_regex_pass(self):
        result = evaluate_assertion({"type": "regex", "pattern": r"hello\s+world"}, "hello world")
        self.assertTrue(result.passed)

    def test_json_path_lite_pass(self):
        result = evaluate_assertion(
            {"type": "json-path-lite", "path": "items[0].score", "equals": 3},
            '{"items": [{"score": 3}]}',
        )
        self.assertTrue(result.passed)

    def test_numeric_tolerance_pass(self):
        result = evaluate_assertion(
            {"type": "numeric_tolerance", "expected": 10.0, "tolerance": 0.5},
            "score: 10.2",
        )
        self.assertTrue(result.passed)

    def test_unknown_assertion_type_raises(self):
        with self.assertRaises(AssertionExecutionError):
            evaluate_assertion({"type": "unknown"}, "value")
