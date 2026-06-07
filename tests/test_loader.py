import json
import tempfile
import unittest
from pathlib import Path

from prompt_regression_lab.errors import SuiteFormatError
from prompt_regression_lab.loader import load_suite


class LoaderTests(unittest.TestCase):
    def test_load_json_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "suite.json"
            path.write_text(json.dumps({"suite": "demo", "cases": [{"id": "a", "actual": "x"}]}), encoding="utf-8")
            suite = load_suite(path)
            self.assertEqual(suite["suite"], "demo")

    def test_load_yaml_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "suite.yaml"
            path.write_text("suite: demo\ncases:\n  - id: a\n    actual: x\n", encoding="utf-8")
            suite = load_suite(path)
            self.assertEqual(suite["cases"][0]["id"], "a")

    def test_rejects_missing_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "suite.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaises(SuiteFormatError):
                load_suite(path)

    def test_rejects_bad_yaml_indentation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "suite.yaml"
            path.write_text("suite: demo\ncases:\n   - id: a\n    actual: x\n", encoding="utf-8")
            with self.assertRaises(SuiteFormatError):
                load_suite(path)
