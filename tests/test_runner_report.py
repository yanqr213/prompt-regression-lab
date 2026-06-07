import json
import tempfile
import unittest
from pathlib import Path

from prompt_regression_lab.report import render_markdown_report, suite_to_dict, write_json_report
from prompt_regression_lab.runner import run_suite


class RunnerAndReportTests(unittest.TestCase):
    def test_run_suite_marks_failure_on_golden_mismatch(self):
        suite = {
            "suite": "demo",
            "cases": [
                {"id": "a", "actual": "actual", "golden": "expected"},
            ],
        }
        result = run_suite(suite)
        self.assertEqual(result.failed, 1)
        self.assertIn("Golden output mismatch.", result.cases[0].errors)

    def test_run_suite_respects_max_failures(self):
        suite = {
            "suite": "demo",
            "cases": [
                {"id": "a", "actual": "x", "golden": "y"},
                {"id": "b", "actual": "x", "golden": "y"},
            ],
        }
        result = run_suite(suite, max_failures=1)
        self.assertEqual(result.total, 1)
        self.assertTrue(result.stopped_early)

    def test_markdown_report_contains_case_status(self):
        suite = {"suite": "demo", "cases": [{"id": "a", "actual": "x", "golden": "x"}]}
        result = run_suite(suite)
        report = render_markdown_report(result)
        self.assertIn("## a - PASS", report)

    def test_json_report_writes_expected_payload(self):
        suite = {"suite": "demo", "cases": [{"id": "a", "actual": "x", "golden": "x"}]}
        result = run_suite(suite)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            write_json_report(path, result)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["passed"], 1)
            self.assertEqual(suite_to_dict(result)["cases"][0]["id"], "a")
