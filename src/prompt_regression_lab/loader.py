"""Load JSON or practical-subset YAML regression suites."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Tuple

from .errors import SuiteFormatError


def load_suite(path: str | Path) -> dict[str, Any]:
    """Load a suite from JSON or a practical YAML subset."""
    source_path = Path(path)
    if not source_path.exists():
        raise SuiteFormatError(f"Suite file not found: {source_path}")

    text = source_path.read_text(encoding="utf-8")
    suffix = source_path.suffix.lower()

    try:
        if suffix == ".json":
            data = json.loads(text)
        elif suffix in {".yaml", ".yml"}:
            data = _parse_yaml(text)
        else:
            raise SuiteFormatError(f"Unsupported suite extension: {suffix}")
    except json.JSONDecodeError as exc:
        raise SuiteFormatError(f"Invalid JSON: {exc}") from exc

    _validate_suite(data)
    return data


def _validate_suite(data: Any) -> None:
    if not isinstance(data, dict):
        raise SuiteFormatError("Suite root must be an object/mapping.")
    if "cases" not in data or not isinstance(data["cases"], list):
        raise SuiteFormatError("Suite must contain a 'cases' list.")
    for index, case in enumerate(data["cases"]):
        if not isinstance(case, dict):
            raise SuiteFormatError(f"Case at index {index} must be an object.")
        if "id" not in case:
            raise SuiteFormatError(f"Case at index {index} is missing required field 'id'.")
        if "actual" not in case:
            raise SuiteFormatError(f"Case '{case['id']}' is missing required field 'actual'.")


def _parse_yaml(text: str) -> Any:
    lines = _preprocess_yaml_lines(text)
    if not lines:
        return {}
    value, next_index = _parse_block(lines, 0, 0)
    if next_index != len(lines):
        raise SuiteFormatError("Unexpected trailing YAML content.")
    return value


def _preprocess_yaml_lines(text: str) -> List[Tuple[int, str]]:
    result: List[Tuple[int, str]] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent % 2 != 0:
            raise SuiteFormatError("YAML indentation must use multiples of two spaces.")
        content = raw[indent:]
        result.append((indent, content))
    return result


def _parse_block(lines: List[Tuple[int, str]], index: int, indent: int) -> Tuple[Any, int]:
    if index >= len(lines):
        return {}, index

    current_indent, current_content = lines[index]
    if current_indent != indent:
        raise SuiteFormatError("Invalid indentation structure in YAML.")

    if current_content.startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_mapping(lines, index, indent)


def _parse_list(lines: List[Tuple[int, str]], index: int, indent: int) -> Tuple[list[Any], int]:
    items: list[Any] = []
    while index < len(lines):
        current_indent, current_content = lines[index]
        if current_indent < indent:
            break
        if current_indent != indent:
            raise SuiteFormatError("Invalid list indentation in YAML.")
        if not current_content.startswith("- "):
            break

        payload = current_content[2:].strip()
        index += 1

        if not payload:
            item, index = _parse_block(lines, index, indent + 2)
            items.append(item)
            continue

        if ":" in payload:
            key, raw_value = _split_key_value(payload)
            item: dict[str, Any] = {key: _parse_scalar(raw_value) if raw_value else None}
            if raw_value == "" and index < len(lines) and lines[index][0] == indent + 2:
                child, index = _parse_block(lines, index, indent + 2)
                item[key] = child
            while index < len(lines) and lines[index][0] == indent + 2 and not lines[index][1].startswith("- "):
                nested_key, nested_value, index = _parse_mapping_entry(lines, index, indent + 2)
                item[nested_key] = nested_value
            items.append(item)
            continue

        items.append(_parse_scalar(payload))

    return items, index


def _parse_mapping(lines: List[Tuple[int, str]], index: int, indent: int) -> Tuple[dict[str, Any], int]:
    mapping: dict[str, Any] = {}
    while index < len(lines):
        current_indent, current_content = lines[index]
        if current_indent < indent:
            break
        if current_indent != indent:
            raise SuiteFormatError("Invalid mapping indentation in YAML.")
        if current_content.startswith("- "):
            break
        key, value, index = _parse_mapping_entry(lines, index, indent)
        mapping[key] = value
    return mapping, index


def _parse_mapping_entry(
    lines: List[Tuple[int, str]], index: int, indent: int
) -> Tuple[str, Any, int]:
    current_indent, current_content = lines[index]
    if current_indent != indent:
        raise SuiteFormatError("Invalid mapping indentation in YAML.")
    key, raw_value = _split_key_value(current_content)
    index += 1

    if raw_value:
        return key, _parse_scalar(raw_value), index

    if index < len(lines) and lines[index][0] > indent:
        value, index = _parse_block(lines, index, indent + 2)
        return key, value, index
    return key, None, index


def _split_key_value(content: str) -> Tuple[str, str]:
    if ":" not in content:
        raise SuiteFormatError(f"Invalid YAML mapping entry: {content}")
    key, value = content.split(":", 1)
    key = key.strip()
    if not key:
        raise SuiteFormatError("YAML key cannot be empty.")
    return key, value.strip()


def _parse_scalar(value: str) -> Any:
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
        quote = value[0]
        if value[-1] != quote:
            raise SuiteFormatError(f"Unmatched quoted scalar: {value}")
        inner = value[1:-1]
        if quote == '"':
            return bytes(inner, "utf-8").decode("unicode_escape")
        return inner
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value
