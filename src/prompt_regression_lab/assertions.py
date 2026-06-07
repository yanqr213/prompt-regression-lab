"""Assertion engine for prompt regression cases."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any, Iterable

from .errors import AssertionExecutionError


@dataclass
class AssertionResult:
    """Normalized assertion execution result."""

    type: str
    passed: bool
    message: str


def evaluate_assertions(assertions: Iterable[dict[str, Any]], actual: str) -> list[AssertionResult]:
    results: list[AssertionResult] = []
    for assertion in assertions:
        results.append(evaluate_assertion(assertion, actual))
    return results


def evaluate_assertion(assertion: dict[str, Any], actual: str) -> AssertionResult:
    assertion_type = assertion.get("type")
    if assertion_type == "contains":
        return _contains(assertion, actual)
    if assertion_type == "regex":
        return _regex(assertion, actual)
    if assertion_type == "json-path-lite":
        return _json_path_lite(assertion, actual)
    if assertion_type == "numeric_tolerance":
        return _numeric_tolerance(assertion, actual)
    raise AssertionExecutionError(f"Unsupported assertion type: {assertion_type}")


def _contains(assertion: dict[str, Any], actual: str) -> AssertionResult:
    value = str(assertion["value"])
    ignore_case = bool(assertion.get("ignore_case"))
    haystack = actual.lower() if ignore_case else actual
    needle = value.lower() if ignore_case else value
    passed = needle in haystack
    message = f"Expected output to contain '{value}'."
    return AssertionResult("contains", passed, message)


def _regex(assertion: dict[str, Any], actual: str) -> AssertionResult:
    pattern = assertion["pattern"]
    flags = re.IGNORECASE if assertion.get("ignore_case") else 0
    matched = re.search(pattern, actual, flags) is not None
    message = f"Expected output to match regex '{pattern}'."
    return AssertionResult("regex", matched, message)


def _json_path_lite(assertion: dict[str, Any], actual: str) -> AssertionResult:
    path = assertion["path"]
    expected = assertion.get("equals")
    try:
        document = json.loads(actual)
    except json.JSONDecodeError as exc:
        raise AssertionExecutionError("Actual value is not valid JSON for json-path-lite assertion.") from exc

    resolved = _resolve_path(document, path)
    passed = resolved == expected
    message = f"Expected JSON path '{path}' to equal {expected!r}, got {resolved!r}."
    return AssertionResult("json-path-lite", passed, message)


def _resolve_path(document: Any, path: str) -> Any:
    current = document
    token = ""
    index = 0
    while index < len(path):
        char = path[index]
        if char == ".":
            if token:
                current = _step_object(current, token)
                token = ""
            index += 1
            continue
        if char == "[":
            if token:
                current = _step_object(current, token)
                token = ""
            end = path.find("]", index)
            if end == -1:
                raise AssertionExecutionError(f"Invalid path syntax: {path}")
            raw_index = path[index + 1 : end]
            try:
                item_index = int(raw_index)
            except ValueError as exc:
                raise AssertionExecutionError(f"Invalid list index in path: {raw_index}") from exc
            current = _step_index(current, item_index)
            index = end + 1
            continue
        token += char
        index += 1

    if token:
        current = _step_object(current, token)
    return current


def _step_object(value: Any, key: str) -> Any:
    if not isinstance(value, dict) or key not in value:
        raise AssertionExecutionError(f"JSON path key not found: {key}")
    return value[key]


def _step_index(value: Any, item_index: int) -> Any:
    if not isinstance(value, list):
        raise AssertionExecutionError("JSON path attempted list index on non-list value.")
    try:
        return value[item_index]
    except IndexError as exc:
        raise AssertionExecutionError(f"JSON path index out of range: {item_index}") from exc


def _numeric_tolerance(assertion: dict[str, Any], actual: str) -> AssertionResult:
    expected = float(assertion["expected"])
    tolerance = float(assertion["tolerance"])
    pattern = assertion.get("pattern")
    observed = _extract_number(actual, pattern)
    delta = abs(observed - expected)
    passed = delta <= tolerance or math.isclose(observed, expected, abs_tol=tolerance)
    message = f"Expected numeric value {expected} +/- {tolerance}, got {observed}."
    return AssertionResult("numeric_tolerance", passed, message)


def _extract_number(actual: str, pattern: str | None) -> float:
    if pattern:
        match = re.search(pattern, actual)
        if not match:
            raise AssertionExecutionError(f"Pattern did not match any numeric value: {pattern}")
        group = match.group(1) if match.groups() else match.group(0)
        return float(group)

    match = re.search(r"-?\d+(?:\.\d+)?", actual)
    if not match:
        raise AssertionExecutionError("No numeric value found in actual output.")
    return float(match.group(0))
