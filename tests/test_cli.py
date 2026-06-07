import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from prompt_regression_lab.cli import main


class CliTests(unittest.TestCase):
    def test_cli_run_success_writes_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite_path = Path(tmp) / "suite.json"
            suite_path.write_text(
                json.dumps({"suite": "demo", "cases": [{"id": "a", "actual": "x", "golden": "x"}]}),
                encoding="utf-8",
            )
            output_path = Path(tmp) / "report.md"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = main(["run", str(suite_path), "--output", str(output_path)])
            self.assertEqual(code, 0)
            self.assertTrue(output_path.exists())
            self.assertIn("passed=1", stdout.getvalue())

    def test_cli_run_failure_returns_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite_path = Path(tmp) / "suite.json"
            suite_path.write_text(
                json.dumps({"suite": "demo", "cases": [{"id": "a", "actual": "x", "golden": "y"}]}),
                encoding="utf-8",
            )
            code = main(["run", str(suite_path)])
            self.assertEqual(code, 1)

    def test_cli_bad_input_returns_two(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = main(["run", "missing-suite.yaml"])
        self.assertEqual(code, 2)
        self.assertIn("error:", stderr.getvalue())

    def test_cli_both_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite_path = Path(tmp) / "suite.json"
            suite_path.write_text(
                json.dumps({"suite": "demo", "cases": [{"id": "a", "actual": "x", "golden": "x"}]}),
                encoding="utf-8",
            )
            markdown_path = Path(tmp) / "report.md"
            json_path = Path(tmp) / "report.json"
            code = main(
                [
                    "run",
                    str(suite_path),
                    "--format",
                    "both",
                    "--output",
                    str(markdown_path),
                    "--json-output",
                    str(json_path),
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue(markdown_path.exists())
            self.assertTrue(json_path.exists())
