"""Report generation for suite execution."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .runner import SuiteExecution


def suite_to_dict(result: SuiteExecution) -> dict[str, Any]:
    return {
        "suite": result.suite_name,
        "total": result.total,
        "passed": result.passed,
        "failed": result.failed,
        "stopped_early": result.stopped_early,
        "cases": [
            {
                "id": case.id,
                "description": case.description,
                "passed": case.passed,
                "prompt": case.prompt,
                "actual": case.actual,
                "golden": case.golden,
                "golden_passed": case.golden_passed,
                "assertions": [
                    {
                        "type": assertion.type,
                        "passed": assertion.passed,
                        "message": assertion.message,
                    }
                    for assertion in case.assertion_results
                ],
                "errors": case.errors,
            }
            for case in result.cases
        ],
    }


def render_markdown_report(result: SuiteExecution) -> str:
    lines = [
        f"# Prompt Regression Report: {result.suite_name}",
        "",
        f"- Total: {result.total}",
        f"- Passed: {result.passed}",
        f"- Failed: {result.failed}",
        f"- Stopped Early: {'yes' if result.stopped_early else 'no'}",
        "",
    ]

    for case in result.cases:
        lines.append(f"## {case.id} - {'PASS' if case.passed else 'FAIL'}")
        if case.description:
            lines.append(case.description)
        if case.prompt:
            lines.extend(["", "Prompt:", "```text", case.prompt, "```"])
        lines.extend(["", "Actual:", "```text", case.actual, "```"])
        if case.golden is not None:
            lines.extend(["", "Golden:", "```text", case.golden, "```"])
        if case.assertion_results:
            lines.append("")
            lines.append("Assertions:")
            for assertion in case.assertion_results:
                status = "PASS" if assertion.passed else "FAIL"
                lines.append(f"- [{status}] {assertion.type}: {assertion.message}")
        if case.errors:
            lines.append("")
            lines.append("Errors:")
            for error in case.errors:
                lines.append(f"- {error}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_report(path: str | Path, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def write_json_report(path: str | Path, result: SuiteExecution) -> None:
    payload = json.dumps(suite_to_dict(result), indent=2, ensure_ascii=False)
    write_report(path, payload + "\n")
