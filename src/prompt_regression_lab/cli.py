"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .errors import PromptRegressionLabError
from .loader import load_suite
from .report import render_markdown_report, write_json_report, write_report
from .runner import run_suite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prlab", description="Offline prompt regression test runner.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command")
    run_parser = subparsers.add_parser("run", help="Run a regression suite.")
    run_parser.add_argument("suite_path", help="Path to the YAML or JSON suite.")
    run_parser.add_argument("--format", choices=["markdown", "json", "both"], default="markdown")
    run_parser.add_argument("--output", default="prompt-regression-report.md", help="Markdown report path.")
    run_parser.add_argument("--json-output", default="prompt-regression-report.json", help="JSON report path.")
    run_parser.add_argument("--fail-on-missing-golden", action="store_true")
    run_parser.add_argument("--max-failures", type=int, default=None)
    run_parser.add_argument("--strict", action="store_true", help="Enable strict quality gate behavior.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "run":
        parser.print_help()
        return 2

    try:
        suite = load_suite(args.suite_path)
        result = run_suite(
            suite,
            fail_on_missing_golden=args.fail_on_missing_golden,
            max_failures=args.max_failures,
            strict=args.strict,
        )
    except PromptRegressionLabError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format in {"markdown", "both"}:
        write_report(args.output, render_markdown_report(result))
    if args.format in {"json", "both"}:
        write_json_report(args.json_output, result)

    print(f"Suite: {result.suite_name} | passed={result.passed} failed={result.failed} total={result.total}")
    return 0 if result.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
