"""Suite execution logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .assertions import AssertionExecutionError, AssertionResult, evaluate_assertions
from .render import render_template


@dataclass
class CaseExecution:
    """Single test case execution record."""

    id: str
    description: str
    prompt: str | None
    actual: str
    golden: str | None
    golden_passed: bool | None
    assertion_results: list[AssertionResult]
    passed: bool
    errors: list[str]


@dataclass
class SuiteExecution:
    """Aggregated suite run result."""

    suite_name: str
    total: int
    passed: int
    failed: int
    stopped_early: bool
    cases: list[CaseExecution]


def run_suite(
    suite: dict[str, Any],
    *,
    fail_on_missing_golden: bool = False,
    max_failures: int | None = None,
    strict: bool = False,
) -> SuiteExecution:
    defaults = suite.get("defaults", {})
    default_vars = defaults.get("vars", {}) if isinstance(defaults, dict) else {}
    failures = 0
    cases: list[CaseExecution] = []
    suite_name = str(suite.get("suite", "unnamed-suite"))

    for case in suite["cases"]:
        record = _run_case(
            case,
            default_vars=default_vars,
            fail_on_missing_golden=fail_on_missing_golden or strict,
        )
        cases.append(record)
        if not record.passed:
            failures += 1
            if max_failures is not None and failures >= max_failures:
                break

    total = len(cases)
    passed = sum(1 for case in cases if case.passed)
    failed = total - passed
    stopped_early = max_failures is not None and failures >= max_failures and len(cases) < len(suite["cases"])

    return SuiteExecution(
        suite_name=suite_name,
        total=total,
        passed=passed,
        failed=failed,
        stopped_early=stopped_early,
        cases=cases,
    )


def _run_case(
    case: dict[str, Any],
    *,
    default_vars: dict[str, Any],
    fail_on_missing_golden: bool,
) -> CaseExecution:
    merged_vars = dict(default_vars)
    merged_vars.update(case.get("vars", {}))

    prompt = render_template(case.get("prompt"), merged_vars)
    actual = str(render_template(case["actual"], merged_vars))
    golden_value = case.get("golden")
    golden = render_template(golden_value, merged_vars) if golden_value is not None else None

    errors: list[str] = []
    golden_passed: bool | None = None
    if golden is None:
        if fail_on_missing_golden:
            errors.append("Missing golden output.")
    else:
        golden_passed = actual == str(golden)
        if not golden_passed:
            errors.append("Golden output mismatch.")

    assertion_results: list[AssertionResult] = []
    try:
        assertion_results = evaluate_assertions(case.get("assertions", []), actual)
        for result in assertion_results:
            if not result.passed:
                errors.append(result.message)
    except AssertionExecutionError as exc:
        errors.append(str(exc))

    passed = not errors
    return CaseExecution(
        id=str(case["id"]),
        description=str(case.get("description", "")),
        prompt=prompt if prompt is None or isinstance(prompt, str) else str(prompt),
        actual=actual,
        golden=None if golden is None else str(golden),
        golden_passed=golden_passed,
        assertion_results=assertion_results,
        passed=passed,
        errors=errors,
    )
